import logging

from apps.dbutils import get_databases, get_table_info, get_table_schema, list_tables, list_tables_info

from .executor_info import build_executor_info

logger = logging.getLogger(__name__)


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
