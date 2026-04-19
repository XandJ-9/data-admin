"""executors 模块回归测试。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from .base import ExecutorFactory
from .datax_config_builder import DataXConfigBuilder
from .datax_executor import DataXExecutor
from .mock import MockETLExecutor
from .sparksql_executor import SparkSQLExecutor


def make_integration_task(**overrides):
    source_datasource = SimpleNamespace(
        db_type='mysql',
        host='127.0.0.1',
        port=3306,
        db_name='biz',
        username='root',
        password='secret',
        params='',
    )
    target_datasource = SimpleNamespace(
        db_type='mysql',
        host='127.0.0.1',
        port=3307,
        db_name='warehouse',
        username='root',
        password='secret',
        params='',
    )
    source_asset = SimpleNamespace(object_name='order_info')
    defaults = {
        'id': 1,
        'task_code': 'sync_order_info',
        'source_datasource': source_datasource,
        'target_datasource': target_datasource,
        'source_asset': source_asset,
        'target_schema_name': 'ods',
        'target_table_name': 'ods_order_info',
        'load_type': 'full',
        'write_mode': 'overwrite',
        'task_config': {},
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_script(**overrides):
    datasource = SimpleNamespace(
        db_type='spark',
        params='{}',
    )
    defaults = {
        'script_code': 'dwd_order_summary',
        'task_config': {'sqlText': 'SELECT 1 AS order_cnt', 'datasourceType': 'spark'},
        'datasource': datasource,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class ExecutorFactoryTests(TestCase):
    def test_registered_executors_include_real_engines(self):
        executors = ExecutorFactory.list_executors()
        self.assertIn('mock', executors)
        self.assertIn('datax', executors)
        self.assertIn('spark', executors)
        self.assertIn('hive', executors)

    def test_create_registered_executor(self):
        executor = ExecutorFactory.create_executor('mock', make_integration_task())
        self.assertIsInstance(executor, MockETLExecutor)


class DataXConfigBuilderTests(TestCase):
    def test_build_mysql_to_mysql_job(self):
        task = make_integration_task(task_config={'speed': {'channel': 2}})
        builder = DataXConfigBuilder(task)

        config = builder.build('20260419')

        content = config['job']['content'][0]
        self.assertEqual(content['reader']['name'], 'mysqlreader')
        self.assertEqual(content['writer']['name'], 'mysqlwriter')
        self.assertEqual(content['writer']['parameter']['connection'][0]['table'], ['ods.ods_order_info'])
        self.assertEqual(config['job']['setting']['speed']['channel'], 2)

    def test_validate_hdfs_target_requires_columns(self):
        hive_target = SimpleNamespace(
            db_type='hive',
            host='127.0.0.1',
            port=9000,
            db_name='warehouse',
            username='hive',
            password='secret',
            params='{"defaultFS": "hdfs://localhost:9000"}',
        )
        task = make_integration_task(target_datasource=hive_target)
        builder = DataXConfigBuilder(task)

        is_valid, message = builder.validate_config()

        self.assertFalse(is_valid)
        self.assertIn('Hive/HDFS', message)


@override_settings(DATAX_HOME='/opt/datax', DATAX_PYTHON='/usr/bin/python3', DATAX_JOB_DIR='/tmp/datax_jobs_test')
class DataXExecutorTests(TestCase):
    @patch('apps.executors.datax_executor.os.path.exists', return_value=True)
    @patch('apps.executors.datax_executor.subprocess.run')
    def test_validate_checks_environment(self, mock_run, mock_exists):
        mock_run.return_value = MagicMock(returncode=0, stdout='Python 3.12', stderr='')
        executor = DataXExecutor(make_integration_task())

        is_valid, message = executor.validate()

        self.assertTrue(is_valid)
        self.assertEqual(message, '')


@override_settings(
    SPARK_MASTER='spark://localhost:7077',
    SPARK_SQL_BIN='/opt/spark/bin/spark-sql',
    HIVE_BIN='/opt/hive/bin/hive',
)
class SparkSQLExecutorTests(TestCase):
    @patch('apps.executors.sparksql_executor.os.path.exists', return_value=True)
    def test_validate_spark_executor(self, mock_exists):
        executor = SparkSQLExecutor(make_script())

        is_valid, message = executor.validate()

        self.assertTrue(is_valid)
        self.assertEqual(message, '')

    @patch('apps.executors.sparksql_executor.os.path.exists', return_value=True)
    def test_build_spark_command_contains_master_and_file(self, mock_exists):
        executor = SparkSQLExecutor(make_script())

        command = executor._build_command('spark', '/tmp/demo.sql')

        self.assertIn('/opt/spark/bin/spark-sql', command)
        self.assertIn('spark://localhost:7077', command)
        self.assertIn('/tmp/demo.sql', command)

    @patch('apps.executors.sparksql_executor.os.path.exists', return_value=True)
    def test_build_hive_command_contains_outputformat(self, mock_exists):
        executor = SparkSQLExecutor(make_script(config={'engine': 'hive'}), config={'engine': 'hive'})

        command = executor._build_command('hive', '/tmp/demo.sql')

        self.assertIn('/opt/hive/bin/hive', command)
        self.assertIn('--outputformat=tsv2', command)

    def test_parse_query_output_tsv(self):
        executor = SparkSQLExecutor(make_script())

        columns, rows = executor._parse_query_output('order_cnt\tamount\n1\t99.5\n')

        self.assertEqual(columns, ['order_cnt', 'amount'])
        self.assertEqual(rows, [{'order_cnt': '1', 'amount': '99.5'}])
