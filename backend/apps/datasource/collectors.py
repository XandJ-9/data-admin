import logging
import threading
from datetime import timedelta
from types import SimpleNamespace

from django.db import close_old_connections, transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from apps.dataasset.facades import collect_table_metadata_via_facade
from apps.datatask.models import TaskInstance
from apps.datatask.services import TaskService
from apps.dbutils import get_databases, get_table_info, get_table_schema, list_tables, list_tables_info

from .executor_info import build_executor_info
from .utils import public_error_message

logger = logging.getLogger(__name__)
SUPPORTED_COLLECTION_TABLE_TYPES = {'BASE TABLE', 'TABLE'}
DATABASE_COLLECTION_HEARTBEAT_TIMEOUT = timedelta(minutes=30)


def _normalize_database_names(data_source):
    base_info = build_executor_info(data_source)
    database_names = get_databases(base_info)
    if database_names:
        return [str(name) for name in database_names if str(name).strip()]
    fallback_name = str(data_source.db_name or '').strip()
    return [fallback_name] if fallback_name else ['']


def _normalize_table_info_rows(rows, database_name=''):
    normalized_rows = []
    for row in rows or []:
        table_name = str(row.get('tableName') or '').strip()
        if not table_name:
            continue
        comment = row.get('tableComment')
        if comment is None:
            comment = row.get('comment') or ''
        normalized_rows.append(
            {
                'tableName': table_name,
                'databaseName': str(row.get('databaseName') or database_name or '').strip(),
                'tableType': str(row.get('tableType') or row.get('type') or 'TABLE'),
                'tableComment': str(comment or ''),
                'comment': str(comment or ''),
                'createTime': str(row.get('createTime') or ''),
                'updateTime': str(row.get('updateTime') or ''),
                'rawPayload': row,
            }
        )
    return normalized_rows


def _normalize_column_rows(rows):
    normalized_rows = []
    for index, row in enumerate(rows or [], start=1):
        normalized_rows.append(
            {
                'order': int(row.get('order') or index),
                'name': str(row.get('name') or ''),
                'type': str(row.get('type') or ''),
                'notnull': bool(row.get('notnull')),
                'default': '' if row.get('default') is None else str(row.get('default')),
                'primary': bool(row.get('primary')),
                'comment': str(row.get('comment') or ''),
                'rawPayload': row,
            }
        )
    return normalized_rows


def normalize_table_type(value):
    return str(value or 'TABLE').strip().upper()


def is_collectable_table_type(value):
    return normalize_table_type(value) in SUPPORTED_COLLECTION_TABLE_TYPES


def _build_fallback_table_info(database_name, table_name, table_type='TABLE'):
    return {
        'tableName': str(table_name or '').strip(),
        'databaseName': str(database_name or '').strip(),
        'tableType': normalize_table_type(table_type),
        'tableComment': '',
        'comment': '',
        'createTime': '',
        'updateTime': '',
        'rawPayload': {},
    }


def get_collect_table_context(data_source, database_name, table_name):
    executor_info = build_executor_info(data_source, database_name)
    table_info = get_table_info(executor_info, table_name) or {}
    normalized_rows = _normalize_table_info_rows([table_info], database_name=database_name or data_source.db_name)
    normalized_table_info = normalized_rows[0] if normalized_rows else _build_fallback_table_info(database_name, table_name)
    table_type = normalize_table_type(normalized_table_info.get('tableType') or normalized_table_info.get('type'))
    return executor_info, normalized_table_info, table_type


def collect_table_to_asset(data_source, database_name, table_name, user=None):
    executor_info, table_info, table_type = get_collect_table_context(data_source, database_name, table_name)
    if not is_collectable_table_type(table_type):
        raise ValueError(f'当前仅支持采集真实数据表，暂不支持对象类型: {table_type}')
    meta_table = collect_table_metadata_via_facade(
        executor_info,
        data_source.id,
        table_name,
        user=user,
    )
    return meta_table, table_info


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


def _build_collection_task_from_snapshot(collection_task_snapshot):
    from .models import DataSource

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
    from .models import DataSourceCollectionTask

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
                logger.warning(
                    '整库异步采集跳过异常表: datasource_id=%s database=%s table=%s error=%s',
                    collection_task.data_source_id,
                    collection_task.database_name,
                    table_name,
                    exc,
                )
                if not collection_task.continue_on_error:
                    raise
            except Exception as exc:
                failed_tables += 1
                safe_message = public_error_message(exc)
                failure_details.append({'tableName': table_name, 'error': safe_message})
                logger.exception(
                    '整库异步采集表失败: datasource_id=%s database=%s table=%s',
                    collection_task.data_source_id,
                    collection_task.database_name,
                    table_name,
                )
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
        logger.warning(
            '整库异步采集被业务校验拒绝: datasource_id=%s database=%s error=%s',
            collection_task.data_source_id,
            collection_task.database_name,
            exc,
        )
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
        logger.exception(
            '整库异步采集失败: datasource_id=%s database=%s',
            collection_task.data_source_id,
            collection_task.database_name,
        )
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


def execute_table_collection_task(platform_task, collection_task, *, username='', trigger_mode='manual', runtime_config=None):
    runtime_payload = _build_collection_runtime_config(collection_task, runtime_config=runtime_config)
    task_instance = TaskService.create_task_instance(
        task=platform_task,
        trigger_mode=trigger_mode,
        runtime_config=runtime_payload,
        triggered_by=username or trigger_mode,
        executor_type='asset_collection',
    )
    TaskService.mark_instance_running(task_instance, executor_type='asset_collection')
    try:
        meta_table, _ = collect_table_to_asset(
            collection_task.data_source,
            collection_task.database_name,
            collection_task.table_name,
            user=None,
        )
    except ValueError as exc:
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            result_summary=_build_collection_summary(
                collection_task=collection_task,
                failed_tables=1,
                extra={'metaTableId': None},
            ),
            error_message=str(exc),
        )
        return {
            'ok': False,
            'msg': str(exc),
            'data': {
                'taskInstanceId': task_instance.id,
                'executionId': task_instance.instance_id,
                'status': 'failed',
            },
        }
    except Exception as exc:
        safe_message = public_error_message(exc)
        TaskService.finalize_instance(
            instance=task_instance,
            status='failed',
            result_summary=_build_collection_summary(
                collection_task=collection_task,
                failed_tables=1,
                extra={'metaTableId': None},
            ),
            error_message=safe_message,
        )
        return {
            'ok': False,
            'msg': safe_message,
            'data': {
                'taskInstanceId': task_instance.id,
                'executionId': task_instance.instance_id,
                'status': 'failed',
            },
        }

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
                return {'ok': False, 'msg': '当前数据库已有进行中的整库采集任务', 'data': None}

        runtime_payload = _build_collection_runtime_config(collection_task, runtime_config=runtime_config)
        task_instance = TaskService.create_task_instance(
            task=platform_task,
            trigger_mode=trigger_mode,
            runtime_config=runtime_payload,
            triggered_by=username or trigger_mode,
            executor_type='asset_collection',
        )
    TaskService.mark_instance_running(task_instance, executor_type='asset_collection')
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
    worker.start()
    task_instance.refresh_from_db()
    return {
        'ok': True,
        'msg': '整库异步采集已启动',
        'data': task_instance,
    }


def discover_databases(data_source):
    return _normalize_database_names(data_source)


def discover_tables(data_source, database_name=''):
    info = build_executor_info(data_source, database_name)
    rows = list_tables_info(info)
    if rows:
        return _normalize_table_info_rows(rows, database_name=database_name or data_source.db_name)
    table_names = list_tables(info)
    fallback_rows = [get_table_info(info, table_name) for table_name in table_names]
    return _normalize_table_info_rows(fallback_rows, database_name=database_name or data_source.db_name)


def discover_columns(data_source, table_name, database_name=''):
    info = build_executor_info(data_source, database_name)
    return _normalize_column_rows(get_table_schema(info, table_name))
