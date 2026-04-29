from __future__ import annotations

from types import SimpleNamespace

from apps.datasource.models import DataSource
from apps.datasource.executor_info import build_executor_info
from apps.executors.base import ExecutorFactory

from apps.datatask.source_registry import SourceHandler, register_source_handler

from .models import DataIntegrationTask

SOURCE_MODULE = 'dataintegration.task'
PUBLISHED_TO_TASK_OPS_KEY = '_publishedToTaskOps'
RUNTIME_TASK_ONLY_KEY = '_runtimeTaskOnly'
RUNTIME_TASK_CONFIG_OVERRIDE_KEY = '_runtimeTaskConfigOverride'


def _get_datasource_binding_error(integration_task: DataIntegrationTask) -> str:
    if integration_task.source_datasource_id is None or integration_task.source_datasource is None:
        return '源数据源已删除或未配置，请重新绑定后再执行'
    if integration_task.target_datasource_id is None or integration_task.target_datasource is None:
        return '目标数据源已删除或未配置，请重新绑定后再执行'
    return ''


def _build_runtime_datasource(data_source, *, database_name: str = ''):
    executor_info = build_executor_info(data_source, database_name=database_name)
    return SimpleNamespace(
        id=data_source.id,
        db_type=executor_info['type'],
        host=executor_info['host'],
        port=executor_info['port'],
        db_name=executor_info['database'],
        username=executor_info['username'],
        password=executor_info['password'],
        params=executor_info['params'],
        name=data_source.name,
    )


def build_task_config(
    integration_task: DataIntegrationTask,
    *,
    published_to_task_ops: bool,
    runtime_task_only: bool,
) -> dict:
    return {
        'sourceDataSourceId': integration_task.source_datasource_id,
        'targetDataSourceId': integration_task.target_datasource_id,
        'sourceDatabaseName': integration_task.source_database_name,
        'sourceTableName': integration_task.source_table_name,
        'targetSchemaName': integration_task.target_schema_name,
        'targetTableName': integration_task.target_table_name,
        'loadType': integration_task.load_type,
        'writeMode': integration_task.write_mode,
        'executorType': integration_task.executor_type,
        'scheduleType': integration_task.schedule_type,
        'cronExpression': integration_task.cron_expression,
        'taskConfig': integration_task.task_config,
        PUBLISHED_TO_TASK_OPS_KEY: published_to_task_ops,
        RUNTIME_TASK_ONLY_KEY: runtime_task_only,
    }


def build_executor_task(integration_task: DataIntegrationTask):
    return build_executor_task_from_snapshot(integration_task, snapshot_config={})


def _get_runtime_datasource(*, data_source_id, fallback_data_source, database_name: str = ''):
    resolved_data_source = fallback_data_source
    if data_source_id not in (None, ''):
        resolved_data_source = DataSource.objects.filter(pk=data_source_id, del_flag='0').first()
        if resolved_data_source is None:
            return None
    if resolved_data_source is None:
        return None
    return _build_runtime_datasource(resolved_data_source, database_name=database_name)


def build_executor_task_from_snapshot(integration_task: DataIntegrationTask, snapshot_config: dict | None = None):
    snapshot_config = snapshot_config or {}
    source_database_name = snapshot_config.get('sourceDatabaseName') or integration_task.source_database_name
    source_table_name = snapshot_config.get('sourceTableName') or integration_task.source_table_name
    target_schema_name = snapshot_config.get('targetSchemaName') or integration_task.target_schema_name
    target_table_name = snapshot_config.get('targetTableName') or integration_task.target_table_name
    load_type = snapshot_config.get('loadType') or integration_task.load_type
    write_mode = snapshot_config.get('writeMode') or integration_task.write_mode
    task_config = snapshot_config.get('taskConfig') or integration_task.task_config or {}
    source_datasource_id = snapshot_config.get('sourceDataSourceId') or integration_task.source_datasource_id
    target_datasource_id = snapshot_config.get('targetDataSourceId') or integration_task.target_datasource_id
    return SimpleNamespace(
        id=integration_task.id,
        task_code=integration_task.task_code,
        task_name=integration_task.task_name,
        source_datasource_id=source_datasource_id,
        target_datasource_id=target_datasource_id,
        source_datasource=_get_runtime_datasource(
            data_source_id=source_datasource_id,
            fallback_data_source=integration_task.source_datasource,
            database_name=source_database_name,
        ),
        target_datasource=_get_runtime_datasource(
            data_source_id=target_datasource_id,
            fallback_data_source=integration_task.target_datasource,
        ),
        source_table_name=source_table_name,
        target_schema_name=target_schema_name,
        target_table_name=target_table_name,
        load_type=load_type,
        write_mode=write_mode,
        task_config=task_config,
    )


def get_source_record(source_record_id: int) -> DataIntegrationTask | None:
    return DataIntegrationTask.objects.select_related(
        'source_datasource',
        'target_datasource',
    ).filter(pk=source_record_id, del_flag='0').first()


def is_task_published(platform_task) -> bool:
    return bool((platform_task.task_config or {}).get(PUBLISHED_TO_TASK_OPS_KEY))


def get_platform_task(source_record_id: int):
    from apps.datatask.models import Task

    return Task.objects.filter(
        source_module=SOURCE_MODULE,
        source_record_id=source_record_id,
        del_flag='0',
    ).first()


def sync_source_task(
    integration_task: DataIntegrationTask,
    *,
    username: str = '',
    published_to_task_ops: bool = True,
):
    from apps.datatask.services import TaskService

    task, _ = TaskService.upsert_source_task(
        task_name=integration_task.task_name,
        task_type='DATA_SYNC',
        source_module=SOURCE_MODULE,
        source_record_id=integration_task.id,
        status=integration_task.status if published_to_task_ops else 'draft',
        schedule_type=(
            'cron' if published_to_task_ops and integration_task.schedule_type == 'cron' else 'manual'
        ),
        cron_expression=(integration_task.cron_expression if published_to_task_ops and integration_task.schedule_type == 'cron' else ''),
        owner=integration_task.owner or username,
        task_config=build_task_config(
            integration_task,
            published_to_task_ops=published_to_task_ops,
            runtime_task_only=not published_to_task_ops,
        ),
        remark=integration_task.remark,
        username=username,
    )
    return task


def ensure_runtime_task(integration_task: DataIntegrationTask, *, username: str = ''):
    platform_task = get_platform_task(integration_task.id)
    if platform_task is not None and is_task_published(platform_task):
        return platform_task
    return sync_source_task(
        integration_task,
        username=username,
        published_to_task_ops=False,
    )


def sync_platform_snapshot(task, changed_fields: set[str] | None = None, username: str = '') -> None:
    changed_fields = changed_fields or set()
    if not changed_fields or not task.source_record_id:
        return

    integration_task = DataIntegrationTask.objects.filter(
        pk=task.source_record_id,
        del_flag='0',
    ).first()
    if integration_task is None:
        return

    update_fields: list[str] = []
    if 'status' in changed_fields and integration_task.status != task.status:
        integration_task.status = task.status
        update_fields.append('status')
    if 'owner' in changed_fields and integration_task.owner != task.owner:
        integration_task.owner = task.owner
        update_fields.append('owner')
    if 'remark' in changed_fields and integration_task.remark != task.remark:
        integration_task.remark = task.remark
        update_fields.append('remark')
    if task.schedule_type != 'dependency':
        if 'schedule_type' in changed_fields and integration_task.schedule_type != task.schedule_type:
            integration_task.schedule_type = task.schedule_type
            update_fields.append('schedule_type')
        expected_cron_expression = task.cron_expression if task.schedule_type == 'cron' else ''
        if 'cron_expression' in changed_fields and integration_task.cron_expression != expected_cron_expression:
            integration_task.cron_expression = expected_cron_expression
            update_fields.append('cron_expression')
    if not update_fields:
        return
    integration_task.update_by = username
    integration_task.save(update_fields=update_fields + ['update_by', 'update_time'])


def validate_task_configuration(task: DataIntegrationTask, runtime_config: dict | None = None):
    binding_error = _get_datasource_binding_error(task)
    if binding_error:
        return False, binding_error
    executor = ExecutorFactory.create_executor(
        task.executor_type,
        build_executor_task(task),
        runtime_config or {},
    )
    return executor.validate()


def execute_task(platform_task, integration_task: DataIntegrationTask, username: str = '', trigger_mode: str = 'manual', runtime_config: dict | None = None) -> dict:
    from apps.datatask.services import TaskService

    runtime_config = runtime_config or {}
    snapshot_config = dict(
        runtime_config.get(RUNTIME_TASK_CONFIG_OVERRIDE_KEY)
        or platform_task.task_config
        or {}
    )
    executor_task = build_executor_task_from_snapshot(integration_task, snapshot_config=snapshot_config)
    if executor_task.source_datasource is None:
        return {'ok': False, 'msg': '源数据源已删除或未配置，请重新绑定后再执行', 'data': None}
    if executor_task.target_datasource is None:
        return {'ok': False, 'msg': '目标数据源已删除或未配置，请重新绑定后再执行', 'data': None}
    executor_type = snapshot_config.get('executorType') or integration_task.executor_type

    effective_runtime_config = {
        'integrationTaskId': integration_task.id,
        **runtime_config,
    }
    task_instance = TaskService.create_task_instance(
        task=platform_task,
        trigger_mode=trigger_mode,
        runtime_config=effective_runtime_config,
        triggered_by=username or trigger_mode,
        executor_type=executor_type,
    )
    TaskService.mark_instance_running(task_instance, executor_type=executor_type)

    try:
        executor = ExecutorFactory.create_executor(
            executor_type,
            executor_task,
            config=effective_runtime_config,
        )
        is_valid, validate_message = executor.validate()
        if not is_valid:
            raise ValueError(validate_message)
        result = executor.execute()
    except Exception as exc:
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            result_summary={'engine': executor_type, 'error': str(exc)},
            error_message=str(exc),
        )
        return {
            'ok': False,
            'msg': f'执行失败: {exc}',
            'data': {
                'taskInstanceId': task_instance.id,
                'executionId': task_instance.instance_id,
                'status': 'failed',
            },
        }

    result_status = result.get('status') or 'success'
    TaskService.finalize_instance(
        instance=task_instance,
        status=result_status,
        result_summary=result,
        error_message=result.get('error_message') or '',
    )
    response_data = {
        'taskInstanceId': task_instance.id,
        'executionId': task_instance.instance_id,
        'status': result_status,
        'resultSummary': result,
    }
    if result_status == 'failed':
        return {
            'ok': False,
            'msg': result.get('error_message') or '执行失败',
            'data': response_data,
        }
    return {
        'ok': True,
        'msg': '执行成功',
        'data': response_data,
    }


register_source_handler(
    SOURCE_MODULE,
    SourceHandler(
        load_source_record=get_source_record,
        sync_source_task=sync_source_task,
        sync_platform_snapshot=sync_platform_snapshot,
        execute_task=execute_task,
    ),
)
