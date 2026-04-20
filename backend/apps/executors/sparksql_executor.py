"""Spark SQL / Hive SQL 执行器。"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

from django.conf import settings

from .base import BaseETLExecutor, ExecutorFactory

logger = logging.getLogger(__name__)


class SparkSQLExecutor(BaseETLExecutor):
    """通过 spark-sql / hive CLI 执行 SQL，并尽量解析结构化结果。"""

    def __init__(self, task: Any, config: dict[str, Any] | None = None):
        super().__init__(task, config)
        self.process: subprocess.Popen[str] | None = None

    def validate(self) -> tuple[bool, str]:
        sql = self._get_sql_text()
        if not sql:
            return False, 'SQL 脚本不能为空'
        engine = self._get_engine_type()
        if engine not in ('spark', 'hive'):
            return False, f'不支持的 SQL 执行引擎: {engine or "unknown"}'
        command = self._resolve_cli_binary(engine)
        if not command:
            cli_name = 'spark-sql' if engine == 'spark' else 'hive'
            return False, f'未找到 {cli_name} 可执行文件，请检查 settings 或环境变量'
        return True, ''

    def execute(self) -> dict[str, Any]:
        start_time = time.time()
        sql_file = None
        try:
            engine = self._get_engine_type()
            sql_file = self._write_sql_file(self._get_sql_text())
            command = self._build_command(engine, sql_file)
            logger.info('执行 %s SQL 命令: %s', engine, ' '.join(command))
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            timeout_seconds = int(self.config.get('timeoutSeconds') or 14400)
            stdout, stderr = self.process.communicate(timeout=timeout_seconds)
            duration_seconds = int(time.time() - start_time)
            if self.process.returncode != 0:
                error_message = (stderr or stdout or '').strip() or f'{engine} SQL 执行失败'
                return {
                    'status': 'failed',
                    'columns': [],
                    'rows': [],
                    'rowCount': 0,
                    'duration_seconds': duration_seconds,
                    'error_message': error_message,
                    'raw_output': stdout,
                    'raw_error': stderr,
                    'engine': engine,
                }
            columns, rows = self._parse_query_output(stdout)
            return {
                'status': 'success',
                'columns': columns,
                'rows': rows,
                'rowCount': len(rows),
                'duration_seconds': duration_seconds,
                'error_message': None,
                'raw_output': stdout,
                'raw_error': stderr,
                'engine': engine,
            }
        except subprocess.TimeoutExpired:
            if self.process and self.process.poll() is None:
                self.process.kill()
            return {
                'status': 'failed',
                'columns': [],
                'rows': [],
                'rowCount': 0,
                'duration_seconds': int(time.time() - start_time),
                'error_message': 'SQL 执行超时',
                'raw_output': '',
                'raw_error': '',
                'engine': self._get_engine_type(),
            }
        except Exception as exc:
            logger.exception('SQL 执行器异常: engine=%s', self._get_engine_type())
            return {
                'status': 'failed',
                'columns': [],
                'rows': [],
                'rowCount': 0,
                'duration_seconds': int(time.time() - start_time),
                'error_message': str(exc),
                'raw_output': '',
                'raw_error': '',
                'engine': self._get_engine_type(),
            }
        finally:
            if sql_file and os.path.exists(sql_file):
                os.remove(sql_file)

    def cancel(self) -> bool:
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                logger.exception('取消 SQL 执行失败')
                return False
            self._mark_cancelled()
            return True
        return False

    def _get_sql_text(self) -> str:
        if self.config.get('sql'):
            return str(self.config['sql']).strip()
        task_config = getattr(self.task, 'task_config', {}) or {}
        if task_config.get('sqlText'):
            return str(task_config['sqlText']).strip()
        return str(getattr(self.task, 'sql_config', '') or '').strip()

    def _get_engine_type(self) -> str:
        configured_engine = str(self.config.get('engine') or '').strip().lower()
        if configured_engine:
            return self._normalize_engine_type(configured_engine)
        datasource = self.config.get('datasource') or getattr(self.task, 'datasource', None)
        if datasource is not None:
            return self._normalize_engine_type(getattr(datasource, 'db_type', ''))
        task_config = getattr(self.task, 'task_config', {}) or {}
        return self._normalize_engine_type(task_config.get('datasourceType') or '')

    def _normalize_engine_type(self, value: str) -> str:
        normalized = str(value or '').strip().lower()
        if normalized in ('spark', 'spark-sql', 'sparksql'):
            return 'spark'
        if normalized in ('hive', 'hiveserver2', 'hive2'):
            return 'hive'
        return normalized

    def _resolve_cli_binary(self, engine: str) -> str | None:
        if engine == 'spark':
            configured = getattr(settings, 'SPARK_SQL_BIN', '') or os.path.join(getattr(settings, 'SPARK_HOME', '/opt/spark'), 'bin', 'spark-sql')
        else:
            configured = getattr(settings, 'HIVE_BIN', '') or 'hive'
        if configured and os.path.exists(configured):
            return configured
        return shutil.which(configured) if configured else None

    def _build_command(self, engine: str, sql_file: str) -> list[str]:
        binary = self._resolve_cli_binary(engine)
        if not binary:
            cli_name = 'spark-sql' if engine == 'spark' else 'hive'
            raise FileNotFoundError(f'未找到 {cli_name} 可执行文件')
        if engine == 'spark':
            command = [binary, '--master', getattr(settings, 'SPARK_MASTER', 'local[*]')]
            command.extend(['--conf', 'spark.sql.cli.print.header=true'])
            for key, value in (self._get_engine_conf('sparkConf') or {}).items():
                command.extend(['--conf', f'{key}={value}'])
            command.extend(['-S', '-f', sql_file])
            return command
        command = [binary, '--hiveconf', 'hive.cli.print.header=true', '--outputformat=tsv2']
        for key, value in (self._get_engine_conf('hiveConf') or {}).items():
            command.extend(['--hiveconf', f'{key}={value}'])
        command.extend(['-S', '-f', sql_file])
        return command

    def _get_engine_conf(self, key: str) -> dict[str, Any]:
        datasource = self.config.get('datasource') or getattr(self.task, 'datasource', None)
        raw_params = getattr(datasource, 'params', '') if datasource is not None else ''
        parsed_params = {}
        if isinstance(raw_params, dict):
            parsed_params = raw_params
        elif isinstance(raw_params, str) and raw_params.strip():
            try:
                parsed_params = json.loads(raw_params)
            except json.JSONDecodeError:
                logger.warning('数据源 params 不是合法 JSON，忽略引擎额外参数')
        return parsed_params.get(key) or self.config.get(key) or {}

    def _write_sql_file(self, sql_text: str) -> str:
        task_identity = getattr(self.task, 'task_code', None) or getattr(self.task, 'script_code', 'sql_task')
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.sql',
            prefix=f'{task_identity}_',
            delete=False,
            encoding='utf-8',
        ) as file_obj:
            file_obj.write(sql_text)
            return file_obj.name

    def _parse_query_output(self, stdout: str) -> tuple[list[str], list[dict[str, Any]]]:
        lines = []
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(('SLF4J', 'INFO', 'WARN', 'Picked up JAVA_TOOL_OPTIONS')):
                continue
            if re.match(r'^[0-9]{2,4}[/-][0-9]{1,2}[/-][0-9]{1,2}', line):
                continue
            lines.append(raw_line.rstrip())
        if not lines:
            return [], []
        if '	' in lines[0]:
            header = lines[0].split('	')
            rows = []
            for row_line in lines[1:]:
                row_values = row_line.split('	')
                rows.append(dict(zip(header, row_values)))
            return header, rows
        if len(lines) == 1:
            return ['result'], [{'result': lines[0]}]
        split_lines = [re.split(r'\s{2,}', line.strip()) for line in lines]
        if len(split_lines[0]) > 1:
            header = split_lines[0]
            rows = [dict(zip(header, values)) for values in split_lines[1:] if values]
            return header, rows
        return ['result'], [{'result': line} for line in lines]


ExecutorFactory.register_executor('spark', SparkSQLExecutor)
ExecutorFactory.register_executor('hive', SparkSQLExecutor)
