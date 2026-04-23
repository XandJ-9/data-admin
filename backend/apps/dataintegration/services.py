from __future__ import annotations

import uuid
from types import SimpleNamespace

from django.utils import timezone

from apps.common.encrypt import decrypt_password
from apps.executors.base import ExecutorFactory

from .models import DataIntegrationExecutionLog, DataIntegrationTask


def _clone_datasource(data_source):
    return SimpleNamespace(
        id=data_source.id,
        db_type=data_source.db_type,
        host=data_source.host,
        port=data_source.port,
        db_name=data_source.db_name,
        username=data_source.username,
        password=decrypt_password(data_source.password),
        params=data_source.params,
        name=data_source.name,
    )


def build_executor_task(task: DataIntegrationTask):
    source_table_name = task.source_table_name
    if task.source_table_snapshot_id and task.source_table_snapshot is not None:
        source_table_name = task.source_table_snapshot.table_name

    source_asset = SimpleNamespace(object_name=source_table_name) if source_table_name else None
    return SimpleNamespace(
        id=task.id,
        task_code=task.task_code,
        task_name=task.task_name,
        source_datasource_id=task.source_datasource_id,
        target_datasource_id=task.target_datasource_id,
        source_datasource=_clone_datasource(task.source_datasource),
        target_datasource=_clone_datasource(task.target_datasource),
        source_asset=source_asset,
        source_table_name=source_table_name,
        target_schema_name=task.target_schema_name,
        target_table_name=task.target_table_name,
        load_type=task.load_type,
        write_mode=task.write_mode,
        task_config=task.task_config or {},
    )


def validate_task_configuration(task: DataIntegrationTask, runtime_config: dict | None = None):
    executor = ExecutorFactory.create_executor(task.executor_type, build_executor_task(task), runtime_config or {})
    return executor.validate()


def execute_integration_task(task: DataIntegrationTask, triggered_by: str):
    runtime_config = {
        'sourceTableName': task.source_table_name,
        'targetTableName': task.target_table_name,
    }
    execution_log = DataIntegrationExecutionLog.objects.create(
        task=task,
        instance_id=uuid.uuid4().hex,
        status='running',
        trigger_mode='manual',
        triggered_by=triggered_by,
        executor_type=task.executor_type,
        runtime_config=runtime_config,
        started_at=timezone.now(),
        create_by=triggered_by,
        update_by=triggered_by,
    )
    try:
        executor_task = build_executor_task(task)
        executor = ExecutorFactory.create_executor(task.executor_type, executor_task, runtime_config)
        is_valid, error_message = executor.validate()
        if not is_valid:
            raise ValueError(error_message)
        result = executor.execute()
        finished_at = timezone.now()
        execution_log.status = result.get('status', 'success')
        execution_log.finished_at = finished_at
        execution_log.duration_seconds = int(result.get('duration_seconds') or 0)
        execution_log.error_message = result.get('error_message') or ''
        execution_log.result_summary = {
            'total_rows': result.get('total_rows', 0),
            'success_rows': result.get('success_rows', 0),
            'failed_rows': result.get('failed_rows', 0),
            'engine': result.get('engine', task.executor_type),
            'log_file': result.get('log_file'),
        }
        execution_log.raw_output = result.get('error_message') or ''
        execution_log.update_by = triggered_by
        execution_log.save(
            update_fields=[
                'status',
                'finished_at',
                'duration_seconds',
                'error_message',
                'result_summary',
                'raw_output',
                'update_by',
                'update_time',
            ]
        )
        return execution_log
    except Exception as exc:
        execution_log.status = 'failed'
        execution_log.finished_at = timezone.now()
        execution_log.error_message = str(exc)
        execution_log.result_summary = {'engine': task.executor_type}
        execution_log.raw_output = str(exc)
        execution_log.update_by = triggered_by
        execution_log.save(
            update_fields=[
                'status',
                'finished_at',
                'error_message',
                'result_summary',
                'raw_output',
                'update_by',
                'update_time',
            ]
        )
        return execution_log

