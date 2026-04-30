import logging

from django.utils import timezone

from apps.dataasset.facades import collect_table_metadata_via_facade
from apps.dbutils import get_databases, get_table_info, get_table_schema, list_tables, list_tables_info

from .executor_info import build_executor_info

logger = logging.getLogger(__name__)
SUPPORTED_COLLECTION_TABLE_TYPES = {'BASE TABLE', 'TABLE'}


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
