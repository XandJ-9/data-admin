"""
DataX Configuration Builder

This module builds DataX JSON configurations from ETL task settings.
"""

import json
import logging
from typing import Dict, Any, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class DataXConfigBuilder:
    """
    DataX configuration builder.

    Builds DataX JSON configurations based on ETL task configuration
    and datasource information.
    """

    # Database type mappings to DataX reader names
    READER_MAPPING = {
        'mysql': 'mysqlreader',
        'postgresql': 'postgresqlreader',
        'oracle': 'oraclereader',
        'sqlserver': 'sqlserverreader',
        'sqlite': 'sqlitereader',
    }

    # Database type mappings to DataX writer names
    WRITER_MAPPING = {
        'mysql': 'mysqlwriter',
        'postgresql': 'postgresqlwriter',
        'oracle': 'oraclewriter',
        'sqlserver': 'sqlserverwriter',
        'hive': 'hdfswriter',
        'hdfs': 'hdfswriter',
    }

    def __init__(self, task):
        """
        Initialize config builder with ETL task.

        Args:
            task: ETLTask instance
        """
        self.task = task
        self.executor_params = task.executor_params or {}

    def build(self, execution_date: str = None) -> Dict[str, Any]:
        """
        Build DataX JSON configuration.

        Args:
            execution_date: Execution date for partition (format: YYYYMMDD)

        Returns:
            DataX configuration dictionary
        """
        # Get executor-specific parameters
        datax_config = self.executor_params.get('datax', {})
        multi_tenant = self.executor_params.get('multi_tenant', {})
        incremental = self.executor_params.get('incremental', {})

        # Build reader configuration
        reader = self._build_reader(
            datax_config.get('reader', {}),
            incremental
        )

        # Build writer configuration
        writer = self._build_writer(
            datax_config.get('writer', {}),
            execution_date,
            multi_tenant
        )

        # Build speed configuration
        speed = datax_config.get('speed', {
            'channel': 1,
            'byte': 1048576,  # 1MB
            'record': 100000
        })

        # Build full DataX configuration
        config = {
            'job': {
                'setting': {
                    'speed': speed,
                    'errorLimit': {
                        'record': 0,
                        'percentage': 0.02
                    }
                },
                'content': [{
                    'reader': {
                        'name': self._get_reader_name(),
                        'parameter': reader
                    },
                    'writer': {
                        'name': self._get_writer_name(),
                        'parameter': writer
                    }
                }]
            }
        }

        logger.info(f"Built DataX config for task: {self.task.task_code}")
        return config

    def _get_reader_name(self) -> str:
        """Get DataX reader name based on source datasource type."""
        db_type = self.task.source_datasource.db_type.lower()
        reader_name = self.READER_MAPPING.get(db_type, 'mysqlreader')
        logger.debug(f"Reader name for {db_type}: {reader_name}")
        return reader_name

    def _get_writer_name(self) -> str:
        """Get DataX writer name based on target datasource type."""
        db_type = self.task.target_datasource.db_type.lower()
        writer_name = self.WRITER_MAPPING.get(db_type, 'hdfswriter')
        logger.debug(f"Writer name for {db_type}: {writer_name}")
        return writer_name

    def _build_reader(self, reader_config: Dict, incremental: Dict) -> Dict[str, Any]:
        """
        Build reader configuration.

        Args:
            reader_config: Reader configuration from executor_params
            incremental: Incremental configuration

        Returns:
            Reader parameter dictionary
        """
        # Get datasource connection info
        source_ds = self.task.source_datasource

        # Build connection configuration
        connection = {
            'jdbcUrl': [f"jdbc:{self._get_jdbc_url(source_ds)}"],
            'table': [self.task.source_table.table_name]
        }

        # Build authentication
        username = source_ds.username
        password = source_ds.password  # Note: DataX requires plaintext password

        # Build column list
        # If field mappings exist, use target field names; otherwise use source columns
        if self.task.field_mappings.exists():
            column = [fm.target_field_name for fm in self.task.field_mappings.all()]
        else:
            # Fetch from source metadata
            column = reader_config.get('column', ['*'])

        # Build query SQL
        if self.task.sql_config:
            # Support incremental extraction
            query_sql = self.task.sql_config
            if incremental.get('enabled') and incremental.get('field'):
                # Apply incremental filter
                watermark = self._get_watermark_value()
                query_sql = self._apply_incremental_filter(
                    query_sql,
                    incremental['field'],
                    watermark
                )
            query_sql = [query_sql]
        else:
            query_sql = None

        # Build reader parameters
        reader_params = {
            'username': username,
            'password': password,
            'connection': [connection] if not query_sql else [],
            'column': column,
        }

        # Add query SQL if present
        if query_sql:
            reader_params['connection'] = [{
                'jdbcUrl': [f"jdbc:{self._get_jdbc_url(source_ds)}"],
                'querySql': query_sql
            }]
            reader_params.pop('column', None)  # Remove column when using querySql

        # Merge with custom reader config
        reader_params.update(reader_config)

        return reader_params

    def _build_writer(
        self,
        writer_config: Dict,
        execution_date: str,
        multi_tenant: Dict
    ) -> Dict[str, Any]:
        """
        Build writer configuration.

        Args:
            writer_config: Writer configuration from executor_params
            execution_date: Execution date for partition
            multi_tenant: Multi-tenant configuration

        Returns:
            Writer parameter dictionary
        """
        target_ds = self.task.target_datasource
        target_table = self.task.target_table

        # HDFS/Hive writer
        if target_ds.db_type.lower() in ['hive', 'hdfs']:
            # Build HDFS path with partition
            path = self._build_hdfs_path(target_table, execution_date, multi_tenant)

            # Get field mappings or default columns
            if self.task.field_mappings.exists():
                columns = []
                for fm in self.task.field_mappings.all():
                    columns.append({
                        'name': fm.target_field_name,
                        'type': fm.data_type or 'string'
                    })
            else:
                columns = writer_config.get('column', [])

            writer_params = {
                'path': path,
                'fileName': execution_date or datetime.now().strftime('%Y%m%d'),
                'writeMode': writer_config.get('writeMode', 'append'),
                'column': columns,
                'compress': writer_config.get('compress', 'gzip'),
                'fieldDelimiter': writer_config.get('fieldDelimiter', ','),
            }

            # Add format (textfile or orc)
            if 'fileType' in writer_config:
                writer_params['fileType'] = writer_config['fileType']

        # Relational database writer
        else:
            connection = {
                'jdbcUrl': f"jdbc:{self._get_jdbc_url(target_ds)}",
                'table': [target_table]
            }

            # Build column list from field mappings
            if self.task.field_mappings.exists():
                column = [fm.target_field_name for fm in self.task.field_mappings.all()]
            else:
                column = writer_config.get('column', ['*'])

            writer_params = {
                'username': target_ds.username,
                'password': target_ds.password,
                'writeMode': writer_config.get('writeMode', 'insert'),
                'connection': [connection],
                'column': column
            }

        # Merge with custom writer config
        writer_params.update(writer_config)

        return writer_params

    def _build_hdfs_path(
        self,
        base_path: str,
        execution_date: str,
        multi_tenant: Dict
    ) -> str:
        """
        Build HDFS path with partition.

        Args:
            base_path: Base HDFS path
            execution_date: Execution date
            multi_tenant: Multi-tenant configuration

        Returns:
            Full HDFS path with partitions
        """
        path = base_path.rstrip('/')

        # Add multi-tenant partition if enabled
        if multi_tenant.get('enabled'):
            tenant_id = multi_tenant.get('tenant_id', 'default')
            path = f"{path}/tenant_id={tenant_id}"

        # Add date partition
        if execution_date:
            path = f"{path}/ds={execution_date}"

        return path

    def _get_jdbc_url(self, datasource) -> str:
        """
        Build JDBC URL from datasource connection.

        Args:
            datasource: DataSource instance

        Returns:
            JDBC URL string
        """
        db_type = datasource.db_type.lower()

        if db_type == 'mysql':
            return f"mysql://{datasource.host}:{datasource.port}/{datasource.db_name}"
        elif db_type == 'postgresql':
            return f"postgresql://{datasource.host}:{datasource.port}/{datasource.db_name}"
        elif db_type == 'oracle':
            return f"oracle:thin:@{datasource.host}:{datasource.port}:{datasource.db_name}"
        elif db_type == 'sqlserver':
            return f"sqlserver://{datasource.host}:{datasource.port};databaseName={datasource.db_name}"
        else:
            # Default to MySQL format
            return f"mysql://{datasource.host}:{datasource.port}/{datasource.db_name}"

    def _apply_incremental_filter(
        self,
        sql: str,
        increment_field: str,
        watermark_value: Union[str, int, None]
    ) -> str:
        """
        Apply incremental filter to SQL query.

        Args:
            sql: Original SQL query
            increment_field: Field name for incremental extraction
            watermark_value: Watermark value (last extracted value)

        Returns:
            SQL with incremental filter applied
        """
        if watermark_value is None:
            # First time execution, no filter
            return sql

        # Add WHERE clause for incremental extraction
        if 'where' in sql.lower():
            # SQL already has WHERE clause, add AND
            incremental_filter = f" AND {increment_field} >= '{watermark_value}'"
            sql = sql + incremental_filter
        else:
            # Add WHERE clause
            incremental_filter = f" WHERE {increment_field} >= '{watermark_value}'"
            sql = sql + incremental_filter

        logger.debug(f"Applied incremental filter: {incremental_filter}")
        return sql

    def _get_watermark_value(self):
        """
        Get watermark value for incremental extraction.

        Returns:
            Watermark value or None if first execution
        """
        logger.debug(
            "Watermark lookup skipped for task %s because dataetl persistence has been removed",
            self.task.task_code,
        )
        return None

    def validate_config(self) -> tuple:
        """
        Validate DataX configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate executor_params exists
        if not self.executor_params:
            return False, "执行器参数不能为空"

        # Validate datax configuration
        if 'datax' not in self.executor_params:
            return False, "DataX配置不存在，请在executor_params.datax中配置"

        datax_config = self.executor_params['datax']

        # Validate reader and writer configuration
        if 'reader' not in datax_config or 'writer' not in datax_config:
            return False, "DataX配置缺少reader或writer配置"

        # Validate source and target datasources
        if not self.task.source_datasource:
            return False, "源数据源不能为空"

        if not self.task.target_datasource:
            return False, "目标数据源不能为空"

        # Validate source table
        if not self.task.source_table:
            return False, "源表不能为空"

        # Validate target table
        if not self.task.target_table:
            return False, "目标表不能为空"

        # Validate database types
        source_db_type = self.task.source_datasource.db_type.lower()
        if source_db_type not in self.READER_MAPPING:
            return False, f"不支持的源数据库类型: {source_db_type}"

        target_db_type = self.task.target_datasource.db_type.lower()
        if target_db_type not in self.WRITER_MAPPING:
            return False, f"不支持的目标数据库类型: {target_db_type}"

        logger.info(f"DataX configuration validation passed for task: {self.task.task_code}")
        return True, ""
