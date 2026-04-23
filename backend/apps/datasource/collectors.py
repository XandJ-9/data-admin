import logging
import threading
import uuid
from datetime import timedelta

from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from apps.dbutils import get_databases, get_table_info, get_table_schema, list_tables, list_tables_info

from .executor_info import build_executor_info
from .models import SourceColumnSnapshot, SourceMetadataCollectionTask, SourceTableSnapshot
from .utils import public_error_message

logger = logging.getLogger(__name__)
ACTIVE_TASK_STALE_MINUTES = 30


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


def _mark_task_cancelled(task, current_table=''):
    task.status = 'cancelled'
    task.current_table = current_table
    task.finished_at = timezone.now()
    task.save(update_fields=['status', 'current_table', 'finished_at', 'update_time'])


def _upsert_table_snapshot(data_source, table_row):
    table_snapshot, _ = SourceTableSnapshot.objects.update_or_create(
        data_source=data_source,
        database_name=table_row['databaseName'],
        table_name=table_row['tableName'],
        del_flag='0',
        defaults={
            'table_type': table_row['tableType'],
            'table_comment': table_row['tableComment'],
            'source_create_time': table_row['createTime'],
            'source_update_time': table_row['updateTime'],
            'raw_payload': table_row['rawPayload'],
        },
    )
    return table_snapshot


def _upsert_column_snapshots(table_snapshot, column_rows):
    active_column_names = [row['name'] for row in column_rows if row['name']]
    SourceColumnSnapshot.objects.filter(table_snapshot=table_snapshot, del_flag='0').exclude(
        column_name__in=active_column_names
    ).update(del_flag='1', update_time=timezone.now())
    for row in column_rows:
        if not row['name']:
            continue
        SourceColumnSnapshot.objects.update_or_create(
            table_snapshot=table_snapshot,
            column_name=row['name'],
            del_flag='0',
            defaults={
                'ordinal_position': row['order'],
                'data_type': row['type'],
                'column_type': row['type'],
                'is_nullable': 'NO' if row['notnull'] else 'YES',
                'column_default': row['default'],
                'column_key': 'PRI' if row['primary'] else '',
                'column_comment': row['comment'],
                'raw_payload': row['rawPayload'],
            },
        )


def _create_task(data_source, collection_scope, run_mode, database_name='', table_name=''):
    with transaction.atomic():
        stale_before = timezone.now() - timedelta(minutes=ACTIVE_TASK_STALE_MINUTES)
        SourceMetadataCollectionTask.objects.select_for_update().filter(
            data_source=data_source,
            del_flag='0',
            status__in=['pending', 'running'],
        ).filter(
            Q(started_at__lt=stale_before) | Q(started_at__isnull=True, create_time__lt=stale_before)
        ).update(
            status='failed',
            error_message='检测到过期采集任务，已自动关闭，请重新发起',
            finished_at=timezone.now(),
            update_time=timezone.now(),
        )
        has_active_task = SourceMetadataCollectionTask.objects.select_for_update().filter(
            data_source=data_source,
            del_flag='0',
            status__in=['pending', 'running'],
        ).exists()
        if has_active_task:
            raise ValueError('当前数据源已有进行中的采集任务，请等待完成后再试')
        return SourceMetadataCollectionTask.objects.create(
            task_id=uuid.uuid4().hex,
            data_source=data_source,
            collection_scope=collection_scope,
            run_mode=run_mode,
            database_name=database_name,
            table_name=table_name,
        )


def _prepare_table_jobs(data_source, task):
    if task.collection_scope == 'table':
        database_name = task.database_name or data_source.db_name
        table_rows = discover_tables(data_source, database_name)
        matched_row = next((row for row in table_rows if row['tableName'] == task.table_name), None)
        if matched_row is None:
            raise ValueError(f'源端不存在数据表：{task.table_name}')
        return [(database_name, matched_row)], {database_name: {task.table_name}}

    discovered_tables = {}
    database_names = [task.database_name] if task.database_name else discover_databases(data_source)
    if task.collection_scope == 'full':
        existing_database_names = list(
            SourceTableSnapshot.objects.filter(data_source=data_source, del_flag='0')
            .values_list('database_name', flat=True)
            .distinct()
        )
        for database_name in existing_database_names:
            if database_name not in database_names:
                database_names.append(database_name)

    jobs = []
    for database_name in database_names:
        discovered_tables.setdefault(database_name, set())
        for table_row in discover_tables(data_source, database_name):
            jobs.append((database_name, table_row))
    return jobs, discovered_tables


def run_collection_task(task_id):
    close_old_connections()
    task = SourceMetadataCollectionTask.objects.filter(task_id=task_id, del_flag='0').select_related('data_source').first()
    if task is None:
        close_old_connections()
        return

    updated = SourceMetadataCollectionTask.objects.filter(
        pk=task.pk,
        del_flag='0',
        status='pending',
    ).update(
        status='running',
        started_at=timezone.now(),
        error_message='',
        finished_at=None,
        current_table='',
        collected_tables=0,
        total_tables=0,
        update_time=timezone.now(),
    )
    if updated == 0:
        close_old_connections()
        return

    task.refresh_from_db()

    try:
        jobs, discovered_tables = _prepare_table_jobs(task.data_source, task)
        task.total_tables = len(jobs)
        task.save(update_fields=['total_tables', 'update_time'])

        for database_name, table_row in jobs:
            task.refresh_from_db(fields=['cancel_requested', 'status'])
            if task.cancel_requested:
                _mark_task_cancelled(task, current_table=task.current_table or table_row['tableName'])
                return

            discovered_tables.setdefault(database_name, set()).add(table_row['tableName'])

            current_table = table_row['tableName']
            task.current_table = current_table
            task.save(update_fields=['current_table', 'update_time'])

            column_rows = discover_columns(task.data_source, current_table, database_name)
            with transaction.atomic():
                table_snapshot = _upsert_table_snapshot(task.data_source, table_row)
                _upsert_column_snapshots(table_snapshot, column_rows)
            task.collected_tables += 1
            task.result_summary = {
                'databaseName': database_name,
                'tableName': current_table,
                'columnCount': len(column_rows),
            }
            task.save(update_fields=['collected_tables', 'result_summary', 'update_time'])

        if task.collection_scope in ('full', 'database'):
            for database_name, active_table_names in discovered_tables.items():
                stale_tables = list(
                    SourceTableSnapshot.objects.filter(
                        data_source=task.data_source,
                        database_name=database_name,
                        del_flag='0',
                    ).exclude(table_name__in=active_table_names)
                )
                if stale_tables:
                    stale_ids = [item.id for item in stale_tables]
                    SourceColumnSnapshot.objects.filter(table_snapshot_id__in=stale_ids, del_flag='0').update(
                        del_flag='1',
                        update_time=timezone.now(),
                    )
                    SourceTableSnapshot.objects.filter(id__in=stale_ids, del_flag='0').update(
                        del_flag='1',
                        update_time=timezone.now(),
                    )

        task.status = 'completed'
        task.finished_at = timezone.now()
        task.current_table = ''
        task.save(update_fields=['status', 'finished_at', 'current_table', 'update_time'])
    except Exception as exc:
        logger.exception('源数据采集失败: task_id=%s', task.task_id)
        task.status = 'failed'
        task.error_message = public_error_message(exc)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'finished_at', 'update_time'])
    finally:
        close_old_connections()


def start_collection_task(task):
    worker = threading.Thread(target=run_collection_task, args=(task.task_id,), daemon=True)
    worker.start()
    return worker


def create_sync_task(data_source, collection_scope, database_name='', table_name=''):
    task = _create_task(data_source, collection_scope, 'sync', database_name=database_name, table_name=table_name)
    run_collection_task(task.task_id)
    task.refresh_from_db()
    return task


def create_async_task(data_source, collection_scope, database_name='', table_name=''):
    task = _create_task(data_source, collection_scope, 'async', database_name=database_name, table_name=table_name)
    start_collection_task(task)
    return task
