"""
DataX 配置构建器。

面向当前 `DataIntegrationTask` 模型生成 DataX JSON 配置，
兼容关系库到关系库、关系库到 HDFS/Hive 的最小可用执行链路。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class DataXConfigBuilder:
    """根据当前数据集成任务配置生成 DataX 作业配置。"""

    READER_MAPPING = {
        'mysql': 'mysqlreader',
        'mariadb': 'mysqlreader',
        'starrocks': 'mysqlreader',
        'postgres': 'postgresqlreader',
        'postgresql': 'postgresqlreader',
        'oracle': 'oraclereader',
        'sqlserver': 'sqlserverreader',
        'sqlite': 'sqlitereader',
    }

    WRITER_MAPPING = {
        'mysql': 'mysqlwriter',
        'mariadb': 'mysqlwriter',
        'starrocks': 'mysqlwriter',
        'postgres': 'postgresqlwriter',
        'postgresql': 'postgresqlwriter',
        'oracle': 'oraclewriter',
        'sqlserver': 'sqlserverwriter',
        'hive': 'hdfswriter',
        'hdfs': 'hdfswriter',
    }

    WRITE_MODE_MAPPING = {
        'overwrite': 'replace',
        'append': 'insert',
        'upsert': 'update',
    }

    def __init__(self, task: Any, runtime_config: dict[str, Any] | None = None):
        self.task = task
        self.task_config = dict(getattr(task, 'task_config', {}) or {})
        self.runtime_config = runtime_config or {}

    def build(self, execution_date: str | None = None) -> dict[str, Any]:
        speed = {
            **getattr(settings, 'DATAX_DEFAULT_SPEED', {}),
            **(self.task_config.get('speed') or {}),
        }
        error_limit = {
            **getattr(settings, 'DATAX_ERROR_LIMIT', {}),
            **(self.task_config.get('errorLimit') or {}),
        }
        reader_config = dict(self.task_config.get('reader') or {})
        writer_config = dict(self.task_config.get('writer') or {})
        content = {
            'reader': {
                'name': self._get_reader_name(),
                'parameter': self._build_reader(reader_config),
            },
            'writer': {
                'name': self._get_writer_name(),
                'parameter': self._build_writer(writer_config, execution_date),
            },
        }
        return {
            'job': {
                'setting': {
                    'speed': speed,
                    'errorLimit': error_limit,
                },
                'content': [content],
            },
        }

    def validate_config(self) -> tuple[bool, str]:
        if not getattr(self.task, 'source_datasource', None):
            return False, '源数据源不能为空'
        if not getattr(self.task, 'target_datasource', None):
            return False, '目标数据源不能为空'

        source_type = self._normalize_db_type(self.task.source_datasource.db_type)
        target_type = self._normalize_db_type(self.task.target_datasource.db_type)
        if source_type not in self.READER_MAPPING:
            return False, f'不支持的源数据库类型: {self.task.source_datasource.db_type}'
        if target_type not in self.WRITER_MAPPING:
            return False, f'不支持的目标数据库类型: {self.task.target_datasource.db_type}'

        if not self._get_source_table_name() and not self._get_query_sql():
            return False, '未配置源表或 querySql，无法生成 DataX reader 配置'
        if target_type not in ('hive', 'hdfs') and not self._get_target_table_name():
            return False, '目标表不能为空'
        if target_type in ('hive', 'hdfs') and not self._resolve_hdfs_columns():
            return False, '目标为 Hive/HDFS 时，需在 taskConfig.columnMappings 或 taskConfig.writer.column 中提供列定义'
        return True, ''

    def _build_reader(self, reader_config: dict[str, Any]) -> dict[str, Any]:
        source_ds = self.task.source_datasource
        jdbc_url = self._build_jdbc_url(source_ds)
        query_sql = self._get_query_sql()
        where_clause = self._merge_where_clause(reader_config.get('where') or self.task_config.get('whereClause') or '')

        reader_params: dict[str, Any] = {
            'username': source_ds.username,
            'password': source_ds.password,
            'connection': [{
                'jdbcUrl': [jdbc_url],
                'table': [self._get_source_table_name()],
            }],
            'column': self._resolve_source_columns(),
        }
        if query_sql:
            reader_params['connection'] = [{
                'jdbcUrl': [jdbc_url],
                'querySql': [self._apply_incremental_filter(query_sql)],
            }]
            reader_params.pop('column', None)
        elif where_clause:
            reader_params['where'] = where_clause

        if reader_config.get('splitPk'):
            reader_params['splitPk'] = reader_config['splitPk']
        if reader_config.get('fetchSize'):
            reader_params['fetchSize'] = reader_config['fetchSize']
        if reader_config.get('session'):
            reader_params['session'] = reader_config['session']
        return reader_params

    def _build_writer(self, writer_config: dict[str, Any], execution_date: str | None) -> dict[str, Any]:
        target_ds = self.task.target_datasource
        target_type = self._normalize_db_type(target_ds.db_type)
        if target_type in ('hive', 'hdfs'):
            params = self._parse_datasource_params(target_ds.params)
            base_path = (
                writer_config.get('path')
                or self.task_config.get('path')
                or params.get('path')
                or f"/data/{self._get_target_table_name().replace('.', '/')}"
            )
            return {
                'defaultFS': writer_config.get('defaultFS') or params.get('defaultFS') or 'file:///',
                'path': self._build_hdfs_path(base_path, execution_date),
                'fileName': writer_config.get('fileName') or self.task.task_code,
                'fileType': writer_config.get('fileType') or params.get('fileType') or 'text',
                'writeMode': writer_config.get('writeMode') or 'append',
                'fieldDelimiter': writer_config.get('fieldDelimiter') or params.get('fieldDelimiter') or '\t',
                'nullFormat': writer_config.get('nullFormat') or params.get('nullFormat') or '\\N',
                'column': self._resolve_hdfs_columns(),
            }

        write_mode = writer_config.get('writeMode') or self.WRITE_MODE_MAPPING.get(getattr(self.task, 'write_mode', 'append'), 'insert')
        writer_params: dict[str, Any] = {
            'username': target_ds.username,
            'password': target_ds.password,
            'writeMode': write_mode,
            'column': self._resolve_target_columns(),
            'connection': [{
                'jdbcUrl': self._build_jdbc_url(target_ds),
                'table': [self._get_target_table_name()],
            }],
        }
        if writer_config.get('preSql'):
            writer_params['preSql'] = writer_config['preSql']
        if writer_config.get('postSql'):
            writer_params['postSql'] = writer_config['postSql']
        if writer_config.get('batchSize'):
            writer_params['batchSize'] = writer_config['batchSize']
        if writer_config.get('session'):
            writer_params['session'] = writer_config['session']
        return writer_params

    def _get_reader_name(self) -> str:
        return self.READER_MAPPING[self._normalize_db_type(self.task.source_datasource.db_type)]

    def _get_writer_name(self) -> str:
        return self.WRITER_MAPPING[self._normalize_db_type(self.task.target_datasource.db_type)]

    def _get_source_table_name(self) -> str:
        source_asset = getattr(self.task, 'source_asset', None)
        if source_asset and source_asset.object_name:
            return source_asset.object_name
        source_table_snapshot = getattr(self.task, 'source_table_snapshot', None)
        if source_table_snapshot and getattr(source_table_snapshot, 'table_name', ''):
            return str(source_table_snapshot.table_name).strip()
        source_table_name = str(getattr(self.task, 'source_table_name', '') or '').strip()
        if source_table_name:
            return source_table_name
        return str(self.task_config.get('sourceTableName') or '').strip()

    def _get_target_table_name(self) -> str:
        schema_name = str(getattr(self.task, 'target_schema_name', '') or '').strip()
        table_name = str(getattr(self.task, 'target_table_name', '') or '').strip()
        if not table_name:
            return ''
        return f'{schema_name}.{table_name}' if schema_name else table_name

    def _get_query_sql(self) -> str:
        reader_config = self.task_config.get('reader') or {}
        return str(reader_config.get('querySql') or self.task_config.get('querySql') or '').strip()

    def _resolve_column_mappings(self) -> list[dict[str, Any]]:
        return [item for item in (self.task_config.get('columnMappings') or []) if isinstance(item, dict)]

    def _resolve_source_columns(self) -> list[str]:
        mappings = self._resolve_column_mappings()
        mapped = [item.get('sourceColumn') or item.get('targetColumn') for item in mappings if item.get('sourceColumn') or item.get('targetColumn')]
        configured = self.task_config.get('columns') or (self.task_config.get('reader') or {}).get('column') or (self.task_config.get('reader') or {}).get('columns')
        if isinstance(configured, list) and configured:
            return configured
        return mapped or ['*']

    def _resolve_target_columns(self) -> list[str]:
        mappings = self._resolve_column_mappings()
        mapped = [item.get('targetColumn') or item.get('sourceColumn') for item in mappings if item.get('targetColumn') or item.get('sourceColumn')]
        configured = (self.task_config.get('writer') or {}).get('column') or self.task_config.get('columns')
        if isinstance(configured, list) and configured:
            if configured and isinstance(configured[0], dict):
                return [item.get('name') for item in configured if item.get('name')]
            return configured
        return mapped or ['*']

    def _resolve_hdfs_columns(self) -> list[dict[str, str]]:
        configured = (self.task_config.get('writer') or {}).get('column') or self.task_config.get('columns')
        if isinstance(configured, list) and configured:
            if isinstance(configured[0], dict):
                return [
                    {
                        'name': item.get('name'),
                        'type': item.get('type', 'string'),
                    }
                    for item in configured
                    if item.get('name')
                ]
            return [{'name': item, 'type': 'string'} for item in configured]

        columns = []
        for item in self._resolve_column_mappings():
            target_column = item.get('targetColumn') or item.get('sourceColumn')
            if not target_column:
                continue
            columns.append({
                'name': target_column,
                'type': item.get('dataType') or 'string',
            })
        return columns

    def _build_hdfs_path(self, base_path: str, execution_date: str | None) -> str:
        path = base_path.rstrip('/')
        partition_format = self.task_config.get('partitionFormat') or 'ds={execution_date}'
        if execution_date:
            path = f"{path}/{partition_format.format(execution_date=execution_date)}"
        return path

    def _merge_where_clause(self, base_where: str) -> str:
        incremental_field = str(self.task_config.get('incrementalField') or '').strip()
        incremental_value = self.runtime_config.get('incrementalValue', self.task_config.get('incrementalValue'))
        if getattr(self.task, 'load_type', 'full') != 'incremental' or not incremental_field or incremental_value in (None, ''):
            return base_where
        incremental_clause = f"{incremental_field} >= '{incremental_value}'"
        if not base_where:
            return incremental_clause
        return f"({base_where}) AND {incremental_clause}"

    def _apply_incremental_filter(self, sql: str) -> str:
        where_clause = self._merge_where_clause('')
        if not where_clause:
            return sql
        lowered = sql.lower()
        keyword = ' where ' if ' where ' not in lowered else ' and '
        return f'{sql}{keyword}{where_clause}'

    def _build_jdbc_url(self, datasource) -> str:
        db_type = self._normalize_db_type(datasource.db_type)
        if db_type in ('mysql', 'mariadb', 'starrocks'):
            return f'jdbc:mysql://{datasource.host}:{datasource.port}/{datasource.db_name}'
        if db_type in ('postgres', 'postgresql'):
            return f'jdbc:postgresql://{datasource.host}:{datasource.port}/{datasource.db_name}'
        if db_type == 'oracle':
            return f'jdbc:oracle:thin:@{datasource.host}:{datasource.port}:{datasource.db_name}'
        if db_type == 'sqlserver':
            return f'jdbc:sqlserver://{datasource.host}:{datasource.port};databaseName={datasource.db_name}'
        if db_type == 'sqlite':
            return f'jdbc:sqlite:{datasource.db_name}'
        raise ValueError(f'不支持的 JDBC 数据源类型: {datasource.db_type}')

    def _parse_datasource_params(self, raw_params: Any) -> dict[str, Any]:
        if not raw_params:
            return {}
        if isinstance(raw_params, dict):
            return raw_params
        if isinstance(raw_params, str):
            try:
                return json.loads(raw_params)
            except json.JSONDecodeError:
                logger.warning('数据源 params 不是合法 JSON，已忽略: task=%s', getattr(self.task, 'task_code', 'unknown'))
        return {}

    def _normalize_db_type(self, db_type: str) -> str:
        return str(db_type or '').strip().lower()
