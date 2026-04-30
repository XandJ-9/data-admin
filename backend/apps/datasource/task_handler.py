from __future__ import annotations

import hashlib
import re
import threading
from datetime import timedelta
from types import SimpleNamespace

from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.datatask.models import Task, TaskInstance
from apps.datatask.source_registry import ExecuteTaskResult, SourceHandler, register_source_handler
from apps.datatask.services import TaskService

from .collectors import collect_table_to_asset, discover_tables, is_collectable_table_type
from .models import DataSource, DataSourceCollectionTask
from .utils import public_error_message

SOURCE_MODULE = 'datasource.collection'
DATABASE_COLLECTION_HEARTBEAT_TIMEOUT = timedelta(minutes=30)



def _normalize_code_part(value: str) -> str:
    normalized = re.sub(r'[^0-9a-zA-Z]+', '_', str(value or '').strip().lower()).strip('_')
    return normalized or 'default'


def build_collection_task_code(*, data_source_id: int, collection_scope: str, database_name: str, table_name: str = '') -> str:
    raw_parts = [str(data_source_id), collection_scope, database_name or '', table_name or '']
    readable = '_'.join(_normalize_code_part(part) for part in raw_parts if str(part).strip())[:72]
    digest = hashlib.md5('|'.join(raw_parts).encode('utf-8')).hexdigest()[:8]
    return f'ds_collect_{readable}_{digest}'


def build_collection_task_name(*, data_source_name: str, collection_scope: str, database_name: str, table_name: str = '') -> str:
    source_name = str(data_source_name or '数据源').strip() or '数据源'
    database_display = str(database_name or '').strip()
    if collection_scope == DataSourceCollectionTask.CollectionScope.DATABASE:
        return f'采集 {source_name} / {database_display or "默认库"}'
    return f'采集 {source_name} / {database_display or "默认库"} / {str(table_name or "").strip()}'


def get_source_record(source_record_id: int) -> DataSourceCollectionTask | None:
    return DataSourceCollectionTask.objects.select_related('data_source').filter(pk=source_record_id, del_flag='0').first()


def ensure_collection_task(
    *,
    data_source,
    collection_scope: str,
    database_name: str = '',
    table_name: str = '',
    username: str = '',
):
    database_name = str(database_name or '').strip()
    table_name = str(table_name or '').strip()
    task_code = build_collection_task_code(
        data_source_id=data_source.id,
        collection_scope=collection_scope,
        database_name=database_name,
        table_name=table_name,
    )
    task_name = build_collection_task_name(
        data_source_name=data_source.name,
        collection_scope=collection_scope,
        database_name=database_name,
        table_name=table_name,
    )
    defaults = {
        'task_name': task_name,
        'data_source': data_source,
        'collection_scope': collection_scope,
        'database_name': database_name,
        'table_name': table_name,
        'status': 'active',
        'owner': username,
        'create_by': username,
        'update_by': username,
    }
    with transaction.atomic():
        collection_task = DataSourceCollectionTask.objects.select_for_update().filter(
            data_source=data_source,
            collection_scope=collection_scope,
            database_name=database_name,
            table_name=table_name,
        ).first()
        if collection_task is None:
            collection_task = DataSourceCollectionTask.objects.select_for_update().filter(task_code=task_code).first()
        if collection_task is None:
            try:
                return DataSourceCollectionTask.objects.create(task_code=task_code, **defaults)
            except IntegrityError:
                collection_task = DataSourceCollectionTask.objects.select_for_update().filter(
                    data_source=data_source,
                    collection_scope=collection_scope,
                    database_name=database_name,
                    table_name=table_name,
                ).first()
                if collection_task is None:
                    collection_task = DataSourceCollectionTask.objects.select_for_update().get(task_code=task_code)

        changed_fields: list[str] = []
        if collection_task.del_flag != '0':
            collection_task.del_flag = '0'
            changed_fields.append('del_flag')
        mutable_defaults = {
            'task_name': task_name,
            'data_source': data_source,
            'collection_scope': collection_scope,
            'database_name': database_name,
            'table_name': table_name,
        }
        for field_name, field_value in mutable_defaults.items():
            if getattr(collection_task, field_name) != field_value:
                setattr(collection_task, field_name, field_value)
                changed_fields.append(field_name)
        if username and collection_task.update_by != username:
            collection_task.update_by = username
            changed_fields.append('update_by')
        if changed_fields:
            collection_task.save(update_fields=changed_fields + ['update_time'])
        return collection_task


def sync_source_task(collection_task: DataSourceCollectionTask, *, username: str = ''):
    existing_task = Task.objects.filter(
        source_module=SOURCE_MODULE,
        source_record_id=collection_task.id,
    ).first()
    default_status = collection_task.status
    _, preserved_schedule_type, preserved_cron_expression = TaskService.get_task_governance_defaults(existing_task)
    task, _ = TaskService.upsert_source_task(
        task_name=collection_task.task_name,
        task_type='ASSET_COLLECTION',
        source_module=SOURCE_MODULE,
        source_record_id=collection_task.id,
        status=existing_task.status if existing_task else default_status,
        schedule_type=preserved_schedule_type,
        cron_expression=preserved_cron_expression,
        owner=collection_task.owner or username,
        task_config={
            'dataSourceId': collection_task.data_source_id,
            'dataSourceName': collection_task.data_source.name if collection_task.data_source else '',
            'collectionScope': collection_task.collection_scope,
            'databaseName': collection_task.database_name,
            'tableName': collection_task.table_name,
            'continueOnError': collection_task.continue_on_error,
        },
        remark=collection_task.remark,
        username=username,
    )
    if existing_task is None and task.status != default_status:
        task.status = default_status
        task.save(update_fields=['status', 'update_time'])
    return task


def sync_platform_snapshot(task, changed_fields: set[str] | None = None, username: str = '') -> None:
    changed_fields = changed_fields or set()
    if not changed_fields or not task.source_record_id:
        return

    collection_task = DataSourceCollectionTask.objects.filter(pk=task.source_record_id, del_flag='0').first()
    if collection_task is None:
        return

    update_fields: list[str] = []
    if 'status' in changed_fields and collection_task.status != task.status:
        collection_task.status = task.status
        update_fields.append('status')
    if 'owner' in changed_fields and collection_task.owner != task.owner:
        collection_task.owner = task.owner
        update_fields.append('owner')
    if 'remark' in changed_fields and collection_task.remark != task.remark:
        collection_task.remark = task.remark
        update_fields.append('remark')
    if not update_fields:
        return
    collection_task.update_by = username
    collection_task.save(update_fields=update_fields + ['update_by', 'update_time'])


def terminate_deleted_collection_tasks(*, collection_task_ids: list[int], username: str = '') -> None:
    if not collection_task_ids:
        return

    active_instances = TaskInstance.objects.select_related('task').filter(
        task__source_module=SOURCE_MODULE,
        task__source_record_id__in=collection_task_ids,
        status__in=['pending', 'running'],
    )
    for task_instance in active_instances:
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            result_summary=task_instance.result_summary or {},
            error_message='数据源已删除，采集已终止',
        )

    for collection_task in DataSourceCollectionTask.objects.filter(id__in=collection_task_ids, del_flag='0'):
        collection_task.del_flag = '1'
        collection_task.update_by = username
        collection_task.save(update_fields=['del_flag', 'update_by', 'update_time'])
        TaskService.soft_delete_source_task(
            source_module=SOURCE_MODULE,
            source_record_id=collection_task.id,
            username=username,
        )


def _is_stale_database_collection_instance(task_instance):
    runtime_config = task_instance.runtime_config or {}
    heartbeat_at = runtime_config.get('heartbeatAt') or ''
    if not heartbeat_at:
        reference_time = task_instance.started_at or task_instance.scheduled_at or task_instance.create_time
        return reference_time is not None and timezone.now() - reference_time > DATABASE_COLLECTION_HEARTBEAT_TIMEOUT
    parsed_time = parse_datetime(heartbeat_at)
    if parsed_time is None:
        return False
    current_time = timezone.now()
    if timezone.is_naive(parsed_time) and timezone.is_aware(current_time):
        parsed_time = timezone.make_aware(parsed_time, timezone.get_current_timezone())
    elif timezone.is_aware(parsed_time) and timezone.is_naive(current_time):
        parsed_time = timezone.make_naive(parsed_time, timezone.get_current_timezone())
    return current_time - parsed_time > DATABASE_COLLECTION_HEARTBEAT_TIMEOUT


def recover_stale_database_collection_instance(task_instance):
    if task_instance.status not in ('pending', 'running'):
        return task_instance
    if not _is_stale_database_collection_instance(task_instance):
        return task_instance
    TaskService.finalize_instance(
        instance=task_instance,
        status='failed',
        result_summary=task_instance.result_summary or {},
        error_message='采集执行器已失联，请重新触发',
    )
    task_instance.refresh_from_db()
    return task_instance


def get_database_collection_run(run_id: str):
    task_instance = TaskInstance.objects.select_related('task').filter(
        task__source_module=SOURCE_MODULE,
        instance_id=run_id,
    ).first()
    if task_instance is None:
        return None
    if (task_instance.runtime_config or {}).get('collectionScope') != DataSourceCollectionTask.CollectionScope.DATABASE:
        return None
    return recover_stale_database_collection_instance(task_instance)


def cleanup_stale_instances() -> list[str]:
    recovered_instance_ids: list[str] = []
    with transaction.atomic():
        queryset = TaskInstance.objects.select_related('task').select_for_update().filter(
            task__source_module=SOURCE_MODULE,
            status__in=['pending', 'running'],
        )
        for task_instance in queryset:
            normalized_instance = recover_stale_database_collection_instance(task_instance)
            if normalized_instance.status == 'failed' and normalized_instance.instance_id not in recovered_instance_ids:
                recovered_instance_ids.append(normalized_instance.instance_id)
    return recovered_instance_ids


def _build_collection_runtime_config(collection_task, *, runtime_config=None):
    data_source = collection_task.data_source
    return {
        'collectionTaskId': collection_task.id,
        'dataSourceId': collection_task.data_source_id,
        'dataSourceName': data_source.name if data_source else '',
        'collectionScope': collection_task.collection_scope,
        'databaseName': collection_task.database_name,
        'tableName': collection_task.table_name,
        'heartbeatAt': timezone.now().isoformat(),
        **(runtime_config or {}),
    }


def _build_collection_summary(*, collection_task, successful_tables=0, failed_tables=0, skipped_tables=0, current_table='', failed_details=None, extra=None):
    return {
        'collectionScope': collection_task.collection_scope,
        'databaseName': collection_task.database_name,
        'tableName': collection_task.table_name,
        'totalTables': successful_tables + failed_tables + skipped_tables,
        'successfulTables': successful_tables,
        'failedTables': failed_tables,
        'skippedTables': skipped_tables,
        'currentTable': current_table,
        'failedDetails': failed_details or [],
        **(extra or {}),
    }


def _update_task_instance_progress(task_instance_id, *, result_summary=None, error_message=None):
    update_fields = {}
    if result_summary is not None:
        update_fields['result_summary'] = result_summary
    if error_message is not None:
        update_fields['error_message'] = error_message
    if update_fields:
        TaskInstance.objects.filter(pk=task_instance_id).update(**update_fields)


def _touch_task_instance_heartbeat(task_instance_id):
    task_instance = TaskInstance.objects.filter(pk=task_instance_id).first()
    if task_instance is None:
        return
    runtime_config = dict(task_instance.runtime_config or {})
    runtime_config['heartbeatAt'] = timezone.now().isoformat()
    task_instance.runtime_config = runtime_config
    task_instance.save(update_fields=['runtime_config'])


def _create_running_collection_instance(
    platform_task,
    collection_task,
    *,
    username='',
    trigger_mode='manual',
    runtime_config=None,
):
    runtime_payload = _build_collection_runtime_config(collection_task, runtime_config=runtime_config)
    task_instance = TaskService.create_task_instance(
        task=platform_task,
        trigger_mode=trigger_mode,
        runtime_config=runtime_payload,
        triggered_by=username or trigger_mode,
        executor_type='asset_collection',
    )
    TaskService.mark_instance_running(task_instance, executor_type='asset_collection')
    return task_instance


def _build_failed_execution_result(task_instance, message: str):
    return {
        'ok': False,
        'msg': message,
        'data': {
            'taskInstanceId': task_instance.id,
            'executionId': task_instance.instance_id,
            'status': 'failed',
        },
    }


def _finalize_table_collection_failure(task_instance, collection_task, message: str):
    TaskService.finalize_instance(
        instance=task_instance,
        status='failed',
        result_summary=_build_collection_summary(
            collection_task=collection_task,
            failed_tables=1,
            extra={'metaTableId': None},
        ),
        error_message=message,
    )
    return _build_failed_execution_result(task_instance, message)


def _build_database_collection_run_payload(task_instance):
    runtime_config = task_instance.runtime_config or {}
    result_summary = task_instance.result_summary or {}
    return {
        'taskInstanceId': task_instance.id,
        'executionId': task_instance.instance_id,
        'status': task_instance.status,
        'collectionScope': runtime_config.get('collectionScope', ''),
        'databaseName': runtime_config.get('databaseName', ''),
        'tableName': runtime_config.get('tableName', ''),
        'currentTable': result_summary.get('currentTable', ''),
        'totalTables': result_summary.get('totalTables', 0),
        'successfulTables': result_summary.get('successfulTables', 0),
        'failedTables': result_summary.get('failedTables', 0),
        'skippedTables': result_summary.get('skippedTables', 0),
        'errorMessage': task_instance.error_message or '',
    }


def _finalize_database_collection_start_failure(task_instance, collection_task, message: str):
    TaskService.finalize_instance(
        instance=task_instance,
        status='failed',
        result_summary=_build_collection_summary(collection_task=collection_task),
        error_message=message,
    )
    task_instance.refresh_from_db()
    return {
        'ok': False,
        'msg': f'整库异步采集启动失败: {message}',
        'data': _build_database_collection_run_payload(task_instance),
    }


def _build_collection_task_from_snapshot(collection_task_snapshot):
    data_source_id = collection_task_snapshot.get('data_source_id')
    data_source = None
    if data_source_id not in (None, ''):
        data_source = DataSource.objects.filter(pk=data_source_id, del_flag='0').first()
    return SimpleNamespace(
        id=collection_task_snapshot.get('id'),
        task_name=collection_task_snapshot.get('task_name', ''),
        data_source_id=data_source_id,
        data_source=data_source,
        collection_scope=collection_task_snapshot.get('collection_scope', ''),
        database_name=collection_task_snapshot.get('database_name', ''),
        table_name=collection_task_snapshot.get('table_name', ''),
        continue_on_error=collection_task_snapshot.get('continue_on_error', False),
    )


def _run_database_asset_sync(task_instance_id, collection_task_id, collection_task_snapshot=None):
    close_old_connections()
    task_instance = TaskInstance.objects.select_related('task').get(pk=task_instance_id)
    collection_task = None
    if collection_task_snapshot is not None:
        collection_task = _build_collection_task_from_snapshot(collection_task_snapshot)
    else:
        collection_task = DataSourceCollectionTask.objects.select_related('data_source').filter(pk=collection_task_id, del_flag='0').first()
    if collection_task is None:
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            result_summary=task_instance.result_summary or {},
            error_message='采集任务已删除，执行已终止',
        )
        close_old_connections()
        return
    successful_tables = 0
    failed_tables = 0
    skipped_tables = 0
    failure_details = []
    try:
        if collection_task.data_source is None:
            raise ValueError('采集任务绑定的数据源已删除或未配置，请重新绑定后再执行')
        _touch_task_instance_heartbeat(task_instance_id)
        rows = discover_tables(collection_task.data_source, collection_task.database_name)
        collectable_rows = [row for row in rows if is_collectable_table_type(row.get('tableType'))]
        skipped_tables = max(len(rows) - len(collectable_rows), 0)
        _update_task_instance_progress(
            task_instance_id,
            result_summary=_build_collection_summary(
                collection_task=collection_task,
                successful_tables=successful_tables,
                failed_tables=failed_tables,
                skipped_tables=skipped_tables,
                failed_details=failure_details,
                extra={
                    'totalTables': len(collectable_rows),
                    'totalDiscoveredObjects': len(rows),
                    'collectableTables': len(collectable_rows),
                },
            ),
        )
        if not collectable_rows:
            raise ValueError(f'数据库 {collection_task.database_name} 下没有可采集的真实数据表')
        for row in collectable_rows:
            collection_task = DataSourceCollectionTask.objects.select_related('data_source').filter(pk=collection_task_id, del_flag='0').first()
            if collection_task is None or collection_task.data_source is None:
                raise ValueError('采集任务已删除或数据源已失效，执行已终止')
            table_name = str(row.get('tableName') or '').strip()
            _touch_task_instance_heartbeat(task_instance_id)
            _update_task_instance_progress(
                task_instance_id,
                result_summary=_build_collection_summary(
                    collection_task=collection_task,
                    successful_tables=successful_tables,
                    failed_tables=failed_tables,
                    skipped_tables=skipped_tables,
                    current_table=table_name,
                    failed_details=failure_details,
                    extra={
                        'totalTables': len(collectable_rows),
                        'totalDiscoveredObjects': len(rows),
                        'collectableTables': len(collectable_rows),
                    },
                ),
            )
            try:
                collect_table_to_asset(collection_task.data_source, collection_task.database_name, table_name, user=None)
                successful_tables += 1
            except ValueError as exc:
                failed_tables += 1
                failure_details.append({'tableName': table_name, 'error': str(exc)})
                if not collection_task.continue_on_error:
                    raise
            except Exception as exc:
                failed_tables += 1
                safe_message = public_error_message(exc)
                failure_details.append({'tableName': table_name, 'error': safe_message})
                if not collection_task.continue_on_error:
                    raise RuntimeError(safe_message) from exc
            finally:
                _update_task_instance_progress(
                    task_instance_id,
                    result_summary=_build_collection_summary(
                        collection_task=collection_task,
                        successful_tables=successful_tables,
                        failed_tables=failed_tables,
                        skipped_tables=skipped_tables,
                        current_table=table_name,
                        failed_details=failure_details,
                        extra={
                            'totalTables': len(collectable_rows),
                            'totalDiscoveredObjects': len(rows),
                            'collectableTables': len(collectable_rows),
                        },
                    ),
                )
        final_status = 'success' if failed_tables == 0 else 'failed'
        TaskService.finalize_instance(
            instance=task_instance,
            status=final_status,
            result_summary=_build_collection_summary(
                collection_task=collection_task,
                successful_tables=successful_tables,
                failed_tables=failed_tables,
                skipped_tables=skipped_tables,
                failed_details=failure_details[:20],
                extra={
                    'totalTables': len(collectable_rows),
                    'totalDiscoveredObjects': len(rows),
                    'collectableTables': len(collectable_rows),
                },
            ),
            error_message=failure_details[0]['error'] if failure_details else '',
        )
    except ValueError as exc:
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            result_summary={
                'collectionScope': collection_task.collection_scope,
                'databaseName': collection_task.database_name,
                'tableName': collection_task.table_name,
                'totalTables': successful_tables + failed_tables + skipped_tables,
                'successfulTables': successful_tables,
                'failedTables': failed_tables,
                'skippedTables': skipped_tables,
                'failedDetails': failure_details[:20],
            },
            error_message=str(exc),
        )
    except Exception as exc:
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            error_message=public_error_message(exc),
            result_summary={
                'collectionScope': collection_task.collection_scope,
                'databaseName': collection_task.database_name,
                'tableName': collection_task.table_name,
                'totalTables': successful_tables + failed_tables + skipped_tables,
                'successfulTables': successful_tables,
                'failedTables': failed_tables,
                'skippedTables': skipped_tables,
                'failedDetails': failure_details[:20],
            },
        )
    finally:
        close_old_connections()


def execute_collection_task(
    collection_task: DataSourceCollectionTask,
    *,
    username: str = '',
    trigger_mode: str = 'manual',
    runtime_config: dict | None = None,
) -> ExecuteTaskResult:
    platform_task = sync_source_task(collection_task, username=username)
    return TaskService.execute_task(
        platform_task,
        username=username,
        trigger_mode=trigger_mode,
        runtime_config=runtime_config,
    )


def execute_table_collection_task(platform_task, collection_task, *, username='', trigger_mode='manual', runtime_config=None):
    task_instance = _create_running_collection_instance(
        platform_task,
        collection_task,
        username=username,
        trigger_mode=trigger_mode,
        runtime_config=runtime_config,
    )
    try:
        meta_table, _ = collect_table_to_asset(
            collection_task.data_source,
            collection_task.database_name,
            collection_task.table_name,
            user=None,
        )
    except ValueError as exc:
        return _finalize_table_collection_failure(task_instance, collection_task, str(exc))
    except Exception as exc:
        safe_message = public_error_message(exc)
        return _finalize_table_collection_failure(task_instance, collection_task, safe_message)

    TaskService.finalize_instance(
        instance=task_instance,
        status='success',
        result_summary=_build_collection_summary(
            collection_task=collection_task,
            successful_tables=1,
            extra={'metaTableId': meta_table.id},
        ),
    )
    return {
        'ok': True,
        'msg': '采集成功，已同步到数据资产',
        'data': {
            'taskInstanceId': task_instance.id,
            'executionId': task_instance.instance_id,
            'status': 'success',
            'tableId': meta_table.id,
            'tableName': meta_table.table_name,
            'databaseName': meta_table.database,
            'dataSourceId': meta_table.data_source_id,
        },
    }


def execute_database_collection_task(platform_task, collection_task, *, username='', trigger_mode='manual', runtime_config=None):
    with transaction.atomic():
        platform_task = platform_task.__class__.objects.select_for_update().get(pk=platform_task.pk)
        active_instance = TaskInstance.objects.select_for_update().filter(task=platform_task, status__in=['pending', 'running']).first()
        if active_instance is not None:
            active_instance = recover_stale_database_collection_instance(active_instance)
            if active_instance.status in ('pending', 'running'):
                return {
                    'ok': False,
                    'msg': '当前数据库已有进行中的整库采集任务，请等待当前运行结束后重试',
                    'data': _build_database_collection_run_payload(active_instance),
                }

        task_instance = _create_running_collection_instance(
            platform_task,
            collection_task,
            username=username,
            trigger_mode=trigger_mode,
            runtime_config=runtime_config,
        )
    _update_task_instance_progress(
        task_instance.id,
        result_summary=_build_collection_summary(collection_task=collection_task),
        error_message='',
    )
    worker = threading.Thread(
        target=_run_database_asset_sync,
        args=(
            task_instance.id,
            collection_task.id,
            {
                'id': collection_task.id,
                'task_name': collection_task.task_name,
                'data_source_id': collection_task.data_source_id,
                'collection_scope': collection_task.collection_scope,
                'database_name': collection_task.database_name,
                'table_name': collection_task.table_name,
                'continue_on_error': collection_task.continue_on_error,
            },
        ),
        daemon=True,
        name=f'ds-collect-{task_instance.instance_id[:8]}',
    )
    try:
        worker.start()
    except Exception as exc:
        safe_message = str(exc).strip() or public_error_message(exc)
        return _finalize_database_collection_start_failure(task_instance, collection_task, safe_message)
    task_instance.refresh_from_db()
    return {
        'ok': True,
        'msg': '整库异步采集已启动',
        'data': task_instance,
    }


def build_runtime_collection_task(platform_task, collection_task: DataSourceCollectionTask):
    task_config = TaskService.get_published_snapshot(platform_task)
    data_source_id = task_config.get('dataSourceId')
    if data_source_id in (None, ''):
        data_source_id = collection_task.data_source_id
    data_source = None
    if data_source_id not in (None, ''):
        data_source = DataSource.objects.filter(pk=data_source_id, del_flag='0').first()
    if data_source is None:
        data_source = collection_task.data_source
    return SimpleNamespace(
        id=collection_task.id,
        task_name=platform_task.task_name or collection_task.task_name,
        data_source_id=data_source_id,
        data_source=data_source,
        collection_scope=task_config.get('collectionScope') or collection_task.collection_scope,
        database_name=task_config.get('databaseName') or collection_task.database_name,
        table_name=task_config.get('tableName') or collection_task.table_name,
        continue_on_error=task_config.get('continueOnError', collection_task.continue_on_error),
    )


## 执行任务， TaskService.execute_task会调用这个函数，执行具体的采集逻辑
def execute_task(platform_task, collection_task: DataSourceCollectionTask, username: str = '', trigger_mode: str = 'manual', runtime_config: dict | None = None) -> ExecuteTaskResult:
    runtime_collection_task = build_runtime_collection_task(platform_task, collection_task)
    if runtime_collection_task.data_source_id is None or runtime_collection_task.data_source is None:
        return {'ok': False, 'msg': '采集任务绑定的数据源已删除或未配置，请重新绑定后再执行', 'data': None}
    if runtime_collection_task.collection_scope == DataSourceCollectionTask.CollectionScope.DATABASE:
        return execute_database_collection_task(
            platform_task,
            runtime_collection_task,
            username=username,
            trigger_mode=trigger_mode,
            runtime_config=runtime_config,
        )
    return execute_table_collection_task(
        platform_task,
        runtime_collection_task,
        username=username,
        trigger_mode=trigger_mode,
        runtime_config=runtime_config,
    )


## 注册源数据采集的handler到datatask模块
register_source_handler(
    SOURCE_MODULE,
    SourceHandler(
        load_source_record=get_source_record,
        sync_source_task=sync_source_task,
        sync_platform_snapshot=sync_platform_snapshot,
        execute_task=execute_task,
        normalize_task_instance=recover_stale_database_collection_instance,
        cleanup_stale_instances=cleanup_stale_instances,
    ),
)