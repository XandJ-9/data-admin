"""
执行器单元测试

覆盖 SparkSQLExecutor、MockETLExecutor、ExecutorFactory 的核心逻辑。
"""

import os
import tempfile
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from .base import BaseExecutor, ExecutorFactory
from .mock import MockETLExecutor
from .sparksql_executor import SparkSQLExecutor


def _make_task(**overrides):
    """构造一个轻量级的 task 替身对象"""
    defaults = {
        'id': 1,
        'task_code': 'test_spark_task',
        'target_datasource': SimpleNamespace(name='spark_ds'),
        'target_table': 'dwd.user_order',
        'sql_config': 'SELECT * FROM ods.raw_user_order',
        'source_datasource_id': 1,
        'target_datasource_id': 2,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── ExecutorFactory ──────────────────────────────

class ExecutorFactoryTests(TestCase):
    """测试执行器工厂注册与实例化"""

    def test_registered_executors_include_spark_and_mock(self):
        types = ExecutorFactory.list_executors()
        self.assertIn('spark', types)
        self.assertIn('mock', types)

    def test_create_spark_executor(self):
        task = _make_task()
        executor = ExecutorFactory.create_executor('spark', task)
        self.assertIsInstance(executor, SparkSQLExecutor)

    def test_create_mock_executor(self):
        task = _make_task()
        executor = ExecutorFactory.create_executor('mock', task)
        self.assertIsInstance(executor, MockETLExecutor)

    def test_create_unknown_executor_raises(self):
        task = _make_task()
        with self.assertRaises(ValueError):
            ExecutorFactory.create_executor('nonexistent', task)


# ── SparkSQLExecutor.validate ────────────────────

class SparkSQLValidateTests(TestCase):
    """测试 Spark SQL 执行器的配置校验"""

    def test_validate_success(self):
        task = _make_task()
        executor = SparkSQLExecutor(task)
        is_valid, msg = executor.validate()
        self.assertTrue(is_valid)
        self.assertEqual(msg, '')

    def test_validate_missing_target_datasource(self):
        task = _make_task(target_datasource=None)
        executor = SparkSQLExecutor(task)
        is_valid, msg = executor.validate()
        self.assertFalse(is_valid)
        self.assertIn('目标数据源', msg)

    def test_validate_missing_target_table(self):
        task = _make_task(target_table='')
        executor = SparkSQLExecutor(task)
        is_valid, msg = executor.validate()
        self.assertFalse(is_valid)
        self.assertIn('目标表', msg)

    def test_validate_missing_sql_config(self):
        task = _make_task(sql_config='')
        executor = SparkSQLExecutor(task)
        is_valid, msg = executor.validate()
        self.assertFalse(is_valid)
        self.assertIn('SQL', msg)


# ── SparkSQLExecutor.execute ─────────────────────

class SparkSQLExecuteTests(TestCase):
    """测试 Spark SQL 执行器的执行逻辑（通过 mock subprocess）"""

    @patch('apps.executors.sparksql_executor.subprocess.run')
    @patch('apps.executors.sparksql_executor.os.makedirs')
    def test_execute_success(self, mock_makedirs, mock_run):
        """正常执行成功，返回 status=success"""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        task = _make_task()
        executor = SparkSQLExecutor(task)

        # mock 日志解析返回空（无错误）
        with patch.object(executor, '_parse_spark_output', return_value={}):
            result = executor.execute()

        self.assertEqual(result['status'], 'success')
        self.assertIsNone(result.get('error_message'))
        self.assertIn('duration_seconds', result)
        mock_run.assert_called_once()

    @patch('apps.executors.sparksql_executor.subprocess.run')
    @patch('apps.executors.sparksql_executor.os.makedirs')
    def test_execute_failure(self, mock_makedirs, mock_run):
        """spark-submit 返回非零退出码，结果为 failed"""
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')

        task = _make_task()
        executor = SparkSQLExecutor(task)

        with patch.object(executor, '_parse_spark_output', return_value={
            'errorMessage': 'AnalysisException: Table not found',
        }):
            result = executor.execute()

        self.assertEqual(result['status'], 'failed')
        self.assertIn('Table not found', result['error_message'])

    @patch('apps.executors.sparksql_executor.subprocess.run')
    @patch('apps.executors.sparksql_executor.os.makedirs')
    def test_execute_timeout(self, mock_makedirs, mock_run):
        """执行超时返回 failed 和超时提示"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='spark-submit', timeout=14400)

        task = _make_task()
        executor = SparkSQLExecutor(task)
        result = executor.execute()

        self.assertEqual(result['status'], 'failed')
        self.assertIn('timeout', result['error_message'].lower())

    @patch('apps.executors.sparksql_executor.subprocess.run')
    @patch('apps.executors.sparksql_executor.os.makedirs')
    def test_execute_exception(self, mock_makedirs, mock_run):
        """执行期间抛异常，返回 failed"""
        mock_run.side_effect = OSError('No such file or directory')

        task = _make_task()
        executor = SparkSQLExecutor(task)
        result = executor.execute()

        self.assertEqual(result['status'], 'failed')
        self.assertIn('No such file', result['error_message'])

    @patch('apps.executors.sparksql_executor.subprocess.run')
    @patch('apps.executors.sparksql_executor.os.makedirs')
    def test_execute_cleans_up_sql_file(self, mock_makedirs, mock_run):
        """执行完成后临时 SQL 文件被清理"""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        task = _make_task()
        executor = SparkSQLExecutor(task)

        with patch.object(executor, '_parse_spark_output', return_value={}):
            executor.execute()

        # 验证 /tmp 下没有残留的 spark_job_*.sql 文件
        tmp_sql_files = [f for f in os.listdir('/tmp') if f.startswith('spark_job_') and f.endswith('.sql')]
        self.assertEqual(len(tmp_sql_files), 0)


# ── SparkSQLExecutor.cancel ──────────────────────

class SparkSQLCancelTests(TestCase):
    """测试 Spark SQL 执行器的取消逻辑"""

    def test_cancel_without_process(self):
        """没有运行中的进程，cancel 返回 False"""
        task = _make_task()
        executor = SparkSQLExecutor(task)
        self.assertFalse(executor.cancel())

    def test_cancel_running_process(self):
        """有运行中的进程，cancel 终止并返回 True"""
        task = _make_task()
        executor = SparkSQLExecutor(task)
        executor.process = MagicMock()
        executor.process.poll.return_value = None  # 进程还在运行
        executor.process.wait.return_value = None

        self.assertTrue(executor.cancel())
        executor.process.terminate.assert_called_once()
        self.assertTrue(executor.is_cancelled())

    def test_cancel_finished_process(self):
        """进程已结束，cancel 返回 False"""
        task = _make_task()
        executor = SparkSQLExecutor(task)
        executor.process = MagicMock()
        executor.process.poll.return_value = 0  # 已退出

        self.assertFalse(executor.cancel())


# ── SparkSQLExecutor._build_spark_submit_command ─

class SparkSQLCommandTests(TestCase):
    """测试 spark-submit 命令构建"""

    def test_command_contains_spark_submit(self):
        task = _make_task()
        executor = SparkSQLExecutor(task)
        cmd = executor._build_spark_submit_command('/tmp/test.sql', '/var/log/spark/test.log')
        self.assertIn('spark-submit', cmd)

    def test_command_contains_sql_file(self):
        task = _make_task()
        executor = SparkSQLExecutor(task)
        cmd = executor._build_spark_submit_command('/tmp/test.sql', '/var/log/spark/test.log')
        self.assertIn('/tmp/test.sql', cmd)

    def test_command_contains_log_redirect(self):
        task = _make_task()
        executor = SparkSQLExecutor(task)
        cmd = executor._build_spark_submit_command('/tmp/test.sql', '/var/log/spark/test.log')
        self.assertIn('/var/log/spark/test.log', cmd)


# ── SparkSQLExecutor._parse_spark_output ─────────

class SparkSQLParseOutputTests(TestCase):
    """测试 Spark 日志解析"""

    def test_parse_clean_log(self):
        """无错误的日志解析为空字典"""
        task = _make_task()
        executor = SparkSQLExecutor(task)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write('INFO: Spark job completed successfully\nINFO: Rows written: 1000\n')
            f.flush()
            result = executor._parse_spark_output(f.name)

        os.unlink(f.name)
        self.assertNotIn('errorMessage', result)

    def test_parse_error_log(self):
        """包含 ERROR 或 Exception 的日志提取错误信息"""
        task = _make_task()
        executor = SparkSQLExecutor(task)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write('INFO: Starting\nERROR: AnalysisException: Table not found\n')
            f.flush()
            result = executor._parse_spark_output(f.name)

        os.unlink(f.name)
        self.assertIn('errorMessage', result)
        self.assertIn('Table not found', result['errorMessage'])

    def test_parse_nonexistent_log(self):
        """日志文件不存在返回空字典"""
        task = _make_task()
        executor = SparkSQLExecutor(task)
        result = executor._parse_spark_output('/nonexistent/path.log')
        self.assertEqual(result, {})


# ── MockETLExecutor ──────────────────────────────

class MockExecutorTests(TestCase):
    """测试 Mock 执行器基本功能"""

    def test_validate_success(self):
        task = _make_task()
        executor = MockETLExecutor(task)
        is_valid, msg = executor.validate()
        self.assertTrue(is_valid)

    def test_validate_missing_task_code(self):
        task = _make_task(task_code='')
        executor = MockETLExecutor(task)
        is_valid, msg = executor.validate()
        self.assertFalse(is_valid)

    def test_cancel(self):
        task = _make_task()
        executor = MockETLExecutor(task)
        self.assertTrue(executor.cancel())
        self.assertTrue(executor.is_cancelled())
