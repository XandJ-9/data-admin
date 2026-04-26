from __future__ import annotations

import hashlib
import re

from django.db import IntegrityError, transaction

from apps.datatask.models import Task
from apps.datatask.source_registry import SourceHandler, register_source_handler
from apps.datatask.services import TaskService

from .collectors import execute_database_collection_task, execute_table_collection_task
from .models import DataSourceCollectionTask

SOURCE_MODULE = 'datasource.collection'


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
        'schedule_type': 'manual',
        'owner': username,
        'task_config': {},
        'create_by': username,
        'update_by': username,
    }
    collection_task = DataSourceCollectionTask.objects.filter(task_code=task_code).first()
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


def build_task_config(collection_task: DataSourceCollectionTask) -> dict:
    return {
        'dataSourceId': collection_task.data_source_id,
        'dataSourceName': collection_task.data_source.name if collection_task.data_source else '',
        'collectionScope': collection_task.collection_scope,
        'databaseName': collection_task.database_name,
        'tableName': collection_task.table_name,
        'continueOnError': collection_task.continue_on_error,
        'scheduleType': collection_task.schedule_type,
        'cronExpression': collection_task.cron_expression,
        'taskConfig': collection_task.task_config or {},
    }


def get_source_record(source_record_id: int) -> DataSourceCollectionTask | None:
    return DataSourceCollectionTask.objects.select_related('data_source').filter(pk=source_record_id, del_flag='0').first()


def sync_source_task(collection_task: DataSourceCollectionTask, *, username: str = ''):
    existing_task = Task.objects.filter(
        source_module=SOURCE_MODULE,
        source_record_id=collection_task.id,
    ).first()
    default_status = collection_task.status
    preserved_status, preserved_schedule_type, preserved_cron_expression = TaskService.get_task_governance_defaults(existing_task)
    task, _ = TaskService.upsert_source_task(
        task_name=collection_task.task_name,
        task_type='ASSET_COLLECTION',
        source_module=SOURCE_MODULE,
        source_record_id=collection_task.id,
        status=existing_task.status if existing_task else default_status,
        schedule_type=preserved_schedule_type,
        cron_expression=preserved_cron_expression,
        owner=collection_task.owner or username,
        task_config=build_task_config(collection_task),
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
    if task.schedule_type != 'dependency':
        if 'schedule_type' in changed_fields and collection_task.schedule_type != task.schedule_type:
            collection_task.schedule_type = task.schedule_type
            update_fields.append('schedule_type')
        expected_cron_expression = task.cron_expression if task.schedule_type == 'cron' else ''
        if 'cron_expression' in changed_fields and collection_task.cron_expression != expected_cron_expression:
            collection_task.cron_expression = expected_cron_expression
            update_fields.append('cron_expression')
    if not update_fields:
        return
    collection_task.update_by = username
    collection_task.save(update_fields=update_fields + ['update_by', 'update_time'])


def execute_task(platform_task, collection_task: DataSourceCollectionTask, username: str = '', trigger_mode: str = 'manual', runtime_config: dict | None = None) -> dict:
    if collection_task.data_source_id is None or collection_task.data_source is None:
        return {'ok': False, 'msg': '采集任务绑定的数据源已删除或未配置，请重新绑定后再执行', 'data': None}
    if collection_task.collection_scope == DataSourceCollectionTask.CollectionScope.DATABASE:
        return execute_database_collection_task(
            platform_task,
            collection_task,
            username=username,
            trigger_mode=trigger_mode,
            runtime_config=runtime_config,
        )
    return execute_table_collection_task(
        platform_task,
        collection_task,
        username=username,
        trigger_mode=trigger_mode,
        runtime_config=runtime_config,
    )


register_source_handler(
    SOURCE_MODULE,
    SourceHandler(
        load_source_record=get_source_record,
        sync_source_task=sync_source_task,
        sync_platform_snapshot=sync_platform_snapshot,
        execute_task=execute_task,
    ),
)
