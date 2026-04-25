from __future__ import annotations

from types import SimpleNamespace

from apps.datasource.executor_info import build_executor_info
from apps.executors.base import ExecutorFactory

from apps.datatask.source_registry import SourceHandler, register_source_handler

from .models import DataIntegrationTask

SOURCE_MODULE = 'dataintegration.task'


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


def build_task_config(integration_task: DataIntegrationTask) -> dict:
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
    }


def build_executor_task(integration_task: DataIntegrationTask):
    return SimpleNamespace(
        id=integration_task.id,
        task_code=integration_task.task_code,
        task_name=integration_task.task_name,
        source_datasource_id=integration_task.source_datasource_id,
        target_datasource_id=integration_task.target_datasource_id,
        source_datasource=_build_runtime_datasource(
            integration_task.source_datasource,
            database_name=integration_task.source_database_name,
        ),
        target_datasource=_build_runtime_datasource(integration_task.target_datasource),
        source_table_name=integration_task.source_table_name,
        target_schema_name=integration_task.target_schema_name,
        target_table_name=integration_task.target_table_name,
        load_type=integration_task.load_type,
        write_mode=integration_task.write_mode,
        task_config=integration_task.task_config or {},
    )


def get_source_record(source_record_id: int) -> DataIntegrationTask | None:
    return DataIntegrationTask.objects.select_related(
        'source_datasource',
        'target_datasource',
    ).filter(pk=source_record_id, del_flag='0').first()


def sync_source_task(integration_task: DataIntegrationTask, *, username: str = ''):
    from apps.datatask.services import TaskService

    task, _ = TaskService.upsert_source_task(
        task_name=integration_task.task_name,
        task_type='DATA_SYNC',
        source_module=SOURCE_MODULE,
        source_record_id=integration_task.id,
        status=integration_task.status,
        schedule_type='cron' if integration_task.schedule_type == 'cron' else 'manual',
        cron_expression=integration_task.cron_expression,
        owner=integration_task.owner or username,
        task_config=build_task_config(integration_task),
        remark=integration_task.remark,
        username=username,
    )
    return task


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

    binding_error = _get_datasource_binding_error(integration_task)
    if binding_error:
        return {'ok': False, 'msg': binding_error, 'data': None}

    effective_runtime_config = {
        'integrationTaskId': integration_task.id,
        **(runtime_config or {}),
    }
    task_instance = TaskService.create_task_instance(
        task=platform_task,
        trigger_mode=trigger_mode,
        runtime_config=effective_runtime_config,
        triggered_by=username or trigger_mode,
        executor_type=integration_task.executor_type,
    )
    TaskService.mark_instance_running(task_instance, executor_type=integration_task.executor_type)

    try:
        executor = ExecutorFactory.create_executor(
            integration_task.executor_type,
            build_executor_task(integration_task),
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
            result_summary={'engine': integration_task.executor_type, 'error': str(exc)},
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
