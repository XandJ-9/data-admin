from __future__ import annotations

import logging
import re
import uuid
from datetime import timedelta
from types import SimpleNamespace

from django.utils import timezone

from apps.datasource.executor_info import build_executor_info
from apps.datatask.source_registry import SourceHandler, register_source_handler

from .models import DataDevModel, DataDevScript, DataDevScriptExecution

logger = logging.getLogger(__name__)

SCRIPT_SOURCE_MODULE = 'datadev.script'
MODEL_SOURCE_MODULE = 'datadev.model'
SCRIPT_STATUS_TO_TASK_STATUS = {
    'draft': 'draft',
    'published': 'active',
    'archived': 'archived',
}
MODEL_STATUS_TO_TASK_STATUS = {
    'draft': 'draft',
    'deployed': 'active',
}


def _build_runtime_datasource(datasource):
    if datasource is None:
        return None
    executor_info = build_executor_info(datasource)
    return SimpleNamespace(
        id=datasource.id,
        db_type=executor_info['type'],
        host=executor_info['host'],
        port=executor_info['port'],
        db_name=executor_info['database'],
        username=executor_info['username'],
        password=executor_info['password'],
        params=executor_info['params'],
        name=datasource.name,
    )


def build_script_task_config(*, script, version, datasource, sql: str) -> dict:
    return {
        'scriptId': script.id,
        'scriptCode': script.script_code,
        'scriptType': script.script_type,
        'scriptRole': getattr(script, 'script_role', ''),
        'engineType': getattr(script, 'engine_type', ''),
        'targetModelId': getattr(script, 'target_model_id', None),
        'targetModelCode': getattr(getattr(script, 'target_model', None), 'model_code', ''),
        'targetModelName': getattr(getattr(script, 'target_model', None), 'model_name', ''),
        'targetLayer': getattr(getattr(script, 'target_model', None), 'layer', ''),
        'datasourceId': datasource.id if datasource else None,
        'datasourceType': datasource.db_type if datasource else '',
        'currentVersionId': version.id if version else None,
        'sqlText': sql,
    }


def sync_script_source_task(script, username: str = ''):
    from apps.datatask.models import Task
    from apps.datatask.services import TaskService

    existing_task = Task.objects.filter(
        source_module=SCRIPT_SOURCE_MODULE,
        source_record_id=script.id,
        del_flag='0',
    ).first()
    current_version = script.versions.filter(is_current=True).first()
    default_status = SCRIPT_STATUS_TO_TASK_STATUS.get(script.status, 'draft')
    preserved_status, preserved_schedule_type, preserved_cron_expression = TaskService.get_task_governance_defaults(
        existing_task
    )
    task, _ = TaskService.upsert_source_task(
        task_name=script.script_name,
        task_type='SQL_COMPUTE',
        source_module=SCRIPT_SOURCE_MODULE,
        source_record_id=script.id,
        status=existing_task.status if existing_task else default_status,
        schedule_type=preserved_schedule_type,
        cron_expression=preserved_cron_expression,
        owner=script.owner or username,
        task_config=build_script_task_config(
            script=script,
            version=current_version,
            datasource=script.datasource,
            sql=current_version.content if current_version else '',
        ),
        remark=script.remark or '',
        username=username,
    )
    if existing_task is None and task.status != default_status:
        task.status = default_status
        task.save(update_fields=['status', 'update_time'])
    return task


def sync_script_platform_snapshot(task, changed_fields: set[str] | None = None, username: str = '') -> None:
    changed_fields = changed_fields or set()
    if not changed_fields or not task.source_record_id:
        return
    script = DataDevScript.objects.filter(pk=task.source_record_id, del_flag='0').first()
    if script is None:
        return
    update_fields: list[str] = []
    if 'owner' in changed_fields and script.owner != task.owner:
        script.owner = task.owner
        update_fields.append('owner')
    if 'remark' in changed_fields and script.remark != task.remark:
        script.remark = task.remark
        update_fields.append('remark')
    if not update_fields:
        return
    script.update_by = username
    script.save(update_fields=update_fields + ['update_by', 'update_time'])


def _normalize_engine_type(script, runtime_params: dict) -> tuple[str, dict | None]:
    configured_engine_type = str(getattr(script, 'engine_type', '') or '').strip().lower()
    if configured_engine_type in ('spark-sql', 'sparksql'):
        configured_engine_type = 'spark'
    elif configured_engine_type in ('hiveserver2', 'hive2'):
        configured_engine_type = 'hive'
    elif configured_engine_type not in ('spark', 'hive', 'mvp'):
        configured_engine_type = 'mvp'

    execution_mode = str(runtime_params.get('executionMode') or '').strip().lower()
    modeling_info = None
    normalized_executor_type = 'mvp'
    if execution_mode == 'modeling':
        normalized_executor_type = str(runtime_params.get('engine') or 'spark').strip().lower()
        if normalized_executor_type in ('spark-sql', 'sparksql'):
            normalized_executor_type = 'spark'
        if normalized_executor_type not in ('spark', 'hive'):
            raise ValueError('建模执行仅支持 Spark SQL 或 Hive')
        if not re.search(r'\bcreate\s+table\b', runtime_params.get('_sqlText', ''), flags=re.IGNORECASE):
            raise ValueError('建模执行当前仅支持 CREATE TABLE 语句')
        modeling_owner = str(runtime_params.get('owner') or script.owner or '').strip()
        target_layer = str(runtime_params.get('targetLayer') or '').strip().upper()
        target_table_name = str(runtime_params.get('targetTableName') or '').strip()
        table_comment = str(runtime_params.get('tableComment') or '').strip()
        if not modeling_owner:
            raise ValueError('建模执行必须填写负责人')
        if target_layer not in ('ODS', 'DWD', 'DWS', 'ADS'):
            raise ValueError('建模执行必须选择 ODS/DWD/DWS/ADS 层级')
        if not target_table_name:
            raise ValueError('建模执行必须填写目标表名')
        if not table_comment:
            raise ValueError('建模执行必须填写表注释')
        modeling_info = {
            'engine': normalized_executor_type,
            'targetLayer': target_layer,
            'targetTableName': target_table_name,
            'tableComment': table_comment,
            'owner': modeling_owner,
        }
        return normalized_executor_type, modeling_info

    if script.datasource is not None:
        normalized_executor_type = str(script.datasource.db_type or '').lower()
        if normalized_executor_type in ('spark-sql', 'sparksql', 'spark'):
            normalized_executor_type = 'spark'
        elif normalized_executor_type in ('hive', 'hiveserver2', 'hive2'):
            normalized_executor_type = 'hive'
        else:
            normalized_executor_type = normalized_executor_type or 'mvp'
    elif script.script_type == 'sql' and configured_engine_type in ('spark', 'hive'):
        normalized_executor_type = configured_engine_type
    elif script.script_type == 'python' or configured_engine_type == 'mvp':
        normalized_executor_type = 'mvp'
    return normalized_executor_type, modeling_info


def execute_script(script, *, username: str = '', runtime_params: dict | None = None, trigger_mode: str = 'manual', runtime_config: dict | None = None, platform_task=None) -> dict:
    from apps.datatask.models import Task
    from apps.datatask.services import TaskService
    from apps.dbutils.factory import get_executor
    from apps.executors.base import ExecutorFactory

    runtime_params = runtime_params or {}
    task = platform_task
    if task is None:
        task = Task.objects.filter(
            source_module=SCRIPT_SOURCE_MODULE,
            source_record_id=script.id,
            del_flag='0',
        ).first()

    current_version = script.versions.filter(is_current=True).first()
    if task is not None:
        version_id = (task.task_config or {}).get('currentVersionId')
        if version_id:
            current_version = script.versions.filter(id=version_id).first() or current_version
        sql = (task.task_config or {}).get('sqlText') or (current_version.content if current_version else '')
    else:
        sql = current_version.content if current_version else ''

    if not current_version:
        return {'ok': False, 'msg': '脚本没有当前版本', 'data': None}
    if not sql or not sql.strip():
        return {'ok': False, 'msg': '脚本内容为空', 'data': None}

    runtime_params_with_sql = {**runtime_params, '_sqlText': sql}
    try:
        normalized_executor_type, modeling_info = _normalize_engine_type(script, runtime_params_with_sql)
    except ValueError as exc:
        return {'ok': False, 'msg': str(exc), 'data': None}

    task_instance = None
    if task is not None:
        task_instance = TaskService.create_task_instance(
            task=task,
            trigger_mode=trigger_mode,
            runtime_config={
                'scriptVersionId': current_version.id,
                'params': runtime_params,
                **(runtime_config or {}),
            },
            triggered_by=username or trigger_mode,
            executor_type=normalized_executor_type,
        )
        TaskService.mark_instance_running(task_instance, executor_type=normalized_executor_type)

    start_time = timezone.now()
    start_perf = timezone.now().timestamp()
    executor = None
    status = 'success'
    error_msg = ''
    columns: list[str] = []
    rows: list[dict] = []
    engine_result: dict = {}

    try:
        if normalized_executor_type == 'mvp':
            statement_count = len([segment for segment in sql.split(';') if segment.strip()]) or 1
            columns = ['mode', 'message', 'statementCount']
            rows = [{
                'mode': 'MVP预演',
                'message': '当前阶段未绑定执行数据源，本次仅完成脚本登记、版本确认和任务预演',
                'statementCount': statement_count,
            }]
            engine_result = {
                'status': 'success',
                'columns': columns,
                'rows': rows,
                'duration_seconds': 0,
                'design_only': True,
            }
        elif normalized_executor_type in ('spark', 'hive'):
            executor = ExecutorFactory.create_executor(
                normalized_executor_type,
                script,
                config={
                    'engine': normalized_executor_type,
                    'sql': sql,
                    'datasource': _build_runtime_datasource(script.datasource) if modeling_info is None else None,
                    'runtimeParams': runtime_params,
                },
            )
            is_valid, validate_message = executor.validate()
            if not is_valid:
                raise ValueError(validate_message)
            engine_result = executor.execute()
            status = engine_result.get('status') or 'success'
            error_msg = engine_result.get('error_message') or ''
            columns = engine_result.get('columns') or []
            raw_rows = engine_result.get('rows') or []
            if raw_rows and isinstance(raw_rows[0], dict):
                rows = raw_rows
                if not columns:
                    columns = list(raw_rows[0].keys())
            else:
                rows = [dict(zip(columns, row)) for row in raw_rows]
        else:
            info = build_executor_info(script.datasource)
            executor = get_executor(info)
            query_result = executor.execute_query(sql=sql)
            columns = query_result.get('columns', [])
            raw_rows = query_result.get('rows', [])
            rows = [dict(zip(columns, row)) for row in raw_rows]
    except Exception as exc:
        status = 'failed'
        error_msg = str(exc)
        logger.exception('脚本执行失败: script_id=%s, error=%s', script.id, exc)
    finally:
        if executor and hasattr(executor, 'close'):
            try:
                executor.close()
            except Exception:
                logger.warning('关闭脚本执行器失败: script_id=%s', script.id, exc_info=True)

    if modeling_info and status == 'success' and not columns and not rows:
        columns = ['mode', 'targetLayer', 'targetTableName', 'tableComment', 'owner']
        rows = [{
            'mode': '建模执行',
            'targetLayer': modeling_info['targetLayer'],
            'targetTableName': modeling_info['targetTableName'],
            'tableComment': modeling_info['tableComment'],
            'owner': modeling_info['owner'],
        }]

    duration = round(timezone.now().timestamp() - start_perf, 2)
    if engine_result.get('duration_seconds') not in (None, ''):
        duration = engine_result['duration_seconds']
    end_time = start_time + timedelta(seconds=duration)
    result_summary = {
        'columns': columns,
        'rows': rows,
        'rowCount': len(rows),
        'error': error_msg,
        'engine': normalized_executor_type,
    }
    if engine_result.get('raw_output'):
        result_summary['rawOutput'] = engine_result['raw_output']
    if engine_result.get('raw_error'):
        result_summary['rawError'] = engine_result['raw_error']
    task_result_summary = {
        'columns': columns,
        'rowCount': len(rows),
        'error': error_msg,
        'engine': normalized_executor_type,
    }
    if modeling_info:
        result_summary['executionMode'] = 'modeling'
        result_summary['modelingInfo'] = modeling_info
        task_result_summary['executionMode'] = 'modeling'
        task_result_summary['modelingInfo'] = modeling_info
    if engine_result.get('design_only'):
        result_summary['designOnly'] = True
        task_result_summary['designOnly'] = True
    if task_instance is not None:
        TaskService.finalize_instance(
            instance=task_instance,
            status=status,
            result_summary=task_result_summary,
            error_message=error_msg,
        )

    execution = DataDevScriptExecution.objects.create(
        script=script,
        version=current_version,
        task_instance=task_instance,
        execution_id=task_instance.instance_id if task_instance else uuid.uuid4().hex,
        status=status,
        executor_type=normalized_executor_type,
        executor_params=runtime_params,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        result_summary=result_summary,
        error_message=error_msg,
        executed_by=username,
    )
    if status == 'failed':
        return {
            'ok': False,
            'msg': f'执行失败: {error_msg}',
            'data': {
                'executionId': execution.execution_id,
                'status': 'failed',
                'rawOutput': result_summary.get('rawOutput', ''),
                'rawError': result_summary.get('rawError', ''),
            },
        }
    return {
        'ok': True,
        'msg': '执行成功',
        'data': {
            'executionId': execution.execution_id,
            'status': 'success',
            'columns': columns,
            'rows': rows,
            'duration': duration,
            'designOnly': bool(engine_result.get('design_only')),
            'executionMode': 'modeling' if modeling_info else 'standard',
            'modelingInfo': modeling_info,
            'rawOutput': result_summary.get('rawOutput', ''),
            'rawError': result_summary.get('rawError', ''),
        },
    }


def get_script_source_record(source_record_id: int):
    return DataDevScript.objects.select_related('datasource', 'target_model').filter(
        pk=source_record_id,
        del_flag='0',
    ).first()


def build_datamodel_create_sql(model) -> str:
    active_fields = model.model_fields.filter(del_flag='0').order_by('ordinal_position', 'id')
    if not active_fields.exists():
        raise ValueError('模型字段不能为空')
    qualified_table_name = model.table_name
    if getattr(model, 'schema_name', ''):
        qualified_table_name = f"{model.schema_name}.{model.table_name}"
    column_lines = []
    table_comment = str(model.table_comment or '').replace("'", "''")
    for field in active_fields:
        field_comment = str(field.field_comment or '').replace("'", "''")
        line = f"  `{field.field_name}` {field.field_type}"
        if not field.is_nullable:
            line += ' NOT NULL'
        line += f" COMMENT '{field_comment}'"
        column_lines.append(line)
    return '\n'.join([
        f"CREATE TABLE IF NOT EXISTS {qualified_table_name} (",
        ',\n'.join(column_lines),
        ')',
        f"COMMENT '{table_comment}'",
    ])


def build_datamodel_task_config(model, sql_text: str) -> dict:
    return {
        'modelId': model.id,
        'modelCode': model.model_code,
        'layer': model.layer,
        'tableName': model.table_name,
        'schemaName': model.schema_name,
        'tableComment': model.table_comment,
        'engineType': model.engine_type,
        'fieldCount': model.model_fields.filter(del_flag='0').count(),
        'sqlText': sql_text,
    }


def sync_model_source_task(model, username: str = ''):
    from apps.datatask.models import Task
    from apps.datatask.services import TaskService

    sql_text = build_datamodel_create_sql(model)
    existing_task = Task.objects.filter(
        source_module=MODEL_SOURCE_MODULE,
        source_record_id=model.id,
        del_flag='0',
    ).first()
    default_status = MODEL_STATUS_TO_TASK_STATUS.get(model.status, 'draft')
    preserved_status, preserved_schedule_type, preserved_cron_expression = TaskService.get_task_governance_defaults(
        existing_task
    )
    task, _ = TaskService.upsert_source_task(
        task_name=model.model_name,
        task_type='SQL_COMPUTE',
        source_module=MODEL_SOURCE_MODULE,
        source_record_id=model.id,
        status=existing_task.status if existing_task else default_status,
        schedule_type=preserved_schedule_type,
        cron_expression=preserved_cron_expression,
        owner=model.owner or username,
        task_config=build_datamodel_task_config(model, sql_text),
        remark=model.remark or '',
        username=username,
    )
    if existing_task is None and task.status != default_status:
        task.status = default_status
        task.save(update_fields=['status', 'update_time'])
    return task


def sync_model_platform_snapshot(task, changed_fields: set[str] | None = None, username: str = '') -> None:
    changed_fields = changed_fields or set()
    if not changed_fields or not task.source_record_id:
        return
    model = DataDevModel.objects.filter(pk=task.source_record_id, del_flag='0').first()
    if model is None:
        return
    update_fields: list[str] = []
    if 'owner' in changed_fields and model.owner != task.owner:
        model.owner = task.owner
        update_fields.append('owner')
    if 'remark' in changed_fields and model.remark != task.remark:
        model.remark = task.remark
        update_fields.append('remark')
    if not update_fields:
        return
    model.update_by = username
    model.save(update_fields=update_fields + ['update_by', 'update_time'])


def get_model_source_record(source_record_id: int):
    return DataDevModel.objects.prefetch_related('model_fields').filter(pk=source_record_id, del_flag='0').first()


def execute_model_task(
    model,
    *,
    username: str = '',
    trigger_mode: str = 'manual',
    runtime_config: dict | None = None,
) -> dict:
    from apps.datatask.models import Task
    from apps.datatask.services import TaskService
    from apps.executors.base import ExecutorFactory

    if not model.owner:
        return {'ok': False, 'msg': '提交建表前必须填写负责人', 'data': None}
    if not model.table_comment:
        return {'ok': False, 'msg': '提交建表前必须填写表注释', 'data': None}
    active_fields = model.model_fields.filter(del_flag='0').order_by('ordinal_position', 'id')
    if not active_fields.exists():
        return {'ok': False, 'msg': '提交建表前至少需要定义一个字段', 'data': None}
    for field in active_fields:
        if not field.field_comment:
            return {'ok': False, 'msg': f'字段 {field.field_name} 缺少字段注释', 'data': None}

    sql_text = build_datamodel_create_sql(model)
    existing_task = Task.objects.filter(
        source_module=MODEL_SOURCE_MODULE,
        source_record_id=model.id,
        del_flag='0',
    ).first()
    preserved_status, preserved_schedule_type, preserved_cron_expression = TaskService.get_task_governance_defaults(
        existing_task
    )
    task, _ = TaskService.upsert_source_task(
        task_name=model.model_name,
        task_type='SQL_COMPUTE',
        source_module=MODEL_SOURCE_MODULE,
        source_record_id=model.id,
        status=preserved_status,
        schedule_type=preserved_schedule_type,
        cron_expression=preserved_cron_expression,
        owner=model.owner or username,
        task_config=build_datamodel_task_config(model, sql_text),
        remark=model.remark or (existing_task.remark if existing_task else ''),
        username=username,
    )
    merged_runtime_config = {
        **(runtime_config or {}),
        'layer': model.layer,
        'tableName': model.table_name,
        'schemaName': model.schema_name,
        'engineType': model.engine_type,
    }
    task_instance = TaskService.create_task_instance(
        task=task,
        trigger_mode=trigger_mode,
        runtime_config=merged_runtime_config,
        triggered_by=username or trigger_mode,
        executor_type=model.engine_type,
    )
    TaskService.mark_instance_running(task_instance, executor_type=model.engine_type)

    start_time = timezone.now()
    start_perf = timezone.now().timestamp()
    executor = ExecutorFactory.create_executor(
        model.engine_type,
        model,
        config={'engine': model.engine_type, 'sql': sql_text},
    )
    status = 'success'
    error_msg = ''
    engine_result = {}
    columns = []
    rows = []
    try:
        is_valid, validate_message = executor.validate()
        if not is_valid:
            raise ValueError(validate_message)
        engine_result = executor.execute()
        status = engine_result.get('status') or 'success'
        error_msg = engine_result.get('error_message') or ''
        columns = engine_result.get('columns') or []
        raw_rows = engine_result.get('rows') or []
        if raw_rows and isinstance(raw_rows[0], dict):
            rows = raw_rows
            if not columns:
                columns = list(raw_rows[0].keys())
        else:
            rows = [dict(zip(columns, row)) for row in raw_rows]
    except Exception as exc:
        status = 'failed'
        error_msg = str(exc)
        logger.exception('模型建表失败: model_id=%s, error=%s', model.id, exc)
    finally:
        if executor and hasattr(executor, 'close'):
            try:
                executor.close()
            except Exception:
                logger.warning('关闭模型执行器失败: model_id=%s', model.id, exc_info=True)

    if status == 'success' and not columns and not rows:
        columns = ['layer', 'tableName', 'engineType', 'owner']
        rows = [{
            'layer': model.layer,
            'tableName': model.table_name,
            'engineType': model.engine_type,
            'owner': model.owner,
        }]

    duration = round(timezone.now().timestamp() - start_perf, 2)
    if engine_result.get('duration_seconds') not in (None, ''):
        duration = engine_result['duration_seconds']
    end_time = start_time + timedelta(seconds=duration)
    result_summary = {
        'columns': columns,
        'rowCount': len(rows),
        'engine': model.engine_type,
        'tableName': model.table_name,
        'layer': model.layer,
        'error': error_msg,
    }
    TaskService.finalize_instance(
        instance=task_instance,
        status=status,
        result_summary=result_summary,
        error_message=error_msg,
    )
    if status == 'success':
        model.status = 'deployed'
        model.update_by = username
        model.save(update_fields=['status', 'update_by', 'update_time'])
    if status == 'failed':
        return {
            'ok': False,
            'msg': f'提交建表失败: {error_msg}',
            'data': {'taskInstanceId': task_instance.id, 'status': 'failed'},
        }
    return {
        'ok': True,
        'msg': '提交建表成功',
        'data': {
            'taskInstanceId': task_instance.id,
            'executionId': task_instance.instance_id,
            'status': status,
            'columns': columns,
            'rows': rows,
            'duration': duration,
            'generatedSql': sql_text,
            'startedAt': start_time,
            'finishedAt': end_time,
        },
    }


def _execute_script_from_platform(platform_task, source_record, username: str, trigger_mode: str, runtime_config: dict | None):
    return execute_script(
        source_record,
        username=username,
        trigger_mode=trigger_mode,
        runtime_config=runtime_config,
        platform_task=platform_task,
    )


def _execute_model_from_platform(platform_task, source_record, username: str, trigger_mode: str, runtime_config: dict | None):
    return execute_model_task(
        source_record,
        username=username,
        trigger_mode=trigger_mode,
        runtime_config=runtime_config,
    )


register_source_handler(
    SCRIPT_SOURCE_MODULE,
    SourceHandler(
        load_source_record=get_script_source_record,
        sync_source_task=sync_script_source_task,
        sync_platform_snapshot=sync_script_platform_snapshot,
        execute_task=_execute_script_from_platform,
    ),
)

register_source_handler(
    MODEL_SOURCE_MODULE,
    SourceHandler(
        load_source_record=get_model_source_record,
        sync_source_task=sync_model_source_task,
        sync_platform_snapshot=sync_model_platform_snapshot,
        execute_task=_execute_model_from_platform,
    ),
)
