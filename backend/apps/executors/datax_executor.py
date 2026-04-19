"""DataX 执行器实现。"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings

from .base import BaseETLExecutor, ExecutorFactory
from .datax_config_builder import DataXConfigBuilder

logger = logging.getLogger(__name__)


class DataXExecutor(BaseETLExecutor):
    """面向当前 `DataIntegrationTask` 的 DataX 执行器。"""

    def __init__(self, task: Any, config: dict[str, Any] | None = None):
        super().__init__(task, config)
        self.config_builder = DataXConfigBuilder(task, runtime_config=self.config)
        self.process: subprocess.Popen[str] | None = None
        self.config_file: str | None = None
        self.log_file: str | None = None
        self.datax_home = getattr(settings, 'DATAX_HOME', '/opt/datax')
        self.datax_python = getattr(settings, 'DATAX_PYTHON', 'python3')
        self.datax_job_dir = getattr(settings, 'DATAX_JOB_DIR', '/tmp/datax_jobs')
        Path(self.datax_job_dir).mkdir(parents=True, exist_ok=True)

    def validate(self) -> tuple[bool, str]:
        is_valid, error_message = self._validate_environment()
        if not is_valid:
            return False, error_message
        return self.config_builder.validate_config()

    def execute(self) -> dict[str, Any]:
        start_time = time.time()
        execution_id = self._generate_execution_id()
        execution_date = str(
            self.config.get('executionDate')
            or self.config.get('execution_date')
            or datetime.now().strftime('%Y%m%d')
        )
        try:
            config = self.config_builder.build(execution_date=execution_date)
            self.config_file = self._write_config(config, execution_id)
            self.log_file = os.path.join(self.datax_job_dir, f'datax_{execution_id}.log')
            command = [
                self.datax_python,
                os.path.join(self.datax_home, 'bin', 'datax.py'),
                self.config_file,
            ]
            logger.info('执行 DataX 命令: %s', ' '.join(command))
            with open(self.log_file, 'w', encoding='utf-8') as log_file:
                self.process = subprocess.Popen(
                    command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                return_code = self.process.wait()
            duration_seconds = int(time.time() - start_time)
            if return_code == 0:
                total_rows, success_rows, failed_rows = self._parse_datax_log()
                return {
                    'status': 'success',
                    'total_rows': total_rows,
                    'success_rows': success_rows,
                    'failed_rows': failed_rows,
                    'duration_seconds': duration_seconds,
                    'error_message': None,
                    'log_file': self.log_file,
                    'engine': 'datax',
                }
            error_message = self._parse_error_log() or f'DataX 进程退出码: {return_code}'
            return {
                'status': 'failed',
                'total_rows': 0,
                'success_rows': 0,
                'failed_rows': 0,
                'duration_seconds': duration_seconds,
                'error_message': error_message,
                'log_file': self.log_file,
                'engine': 'datax',
            }
        except Exception as exc:
            logger.exception('DataX 执行异常: task=%s', getattr(self.task, 'task_code', 'unknown'))
            return {
                'status': 'failed',
                'total_rows': 0,
                'success_rows': 0,
                'failed_rows': 0,
                'duration_seconds': int(time.time() - start_time),
                'error_message': str(exc),
                'log_file': self.log_file,
                'engine': 'datax',
            }
        finally:
            self._cleanup()

    def cancel(self) -> bool:
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                logger.exception('取消 DataX 任务失败: task=%s', getattr(self.task, 'task_code', 'unknown'))
                return False
            self._mark_cancelled()
            return True
        return False

    def _validate_environment(self) -> tuple[bool, str]:
        datax_script = os.path.join(self.datax_home, 'bin', 'datax.py')
        if not os.path.exists(self.datax_home):
            return False, f'DataX 安装目录不存在: {self.datax_home}'
        if not os.path.exists(datax_script):
            return False, f'DataX 脚本不存在: {datax_script}'
        try:
            version_check = subprocess.run(
                [self.datax_python, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as exc:
            return False, f'DataX Python 不可用: {exc}'
        if version_check.returncode != 0:
            return False, f'DataX Python 执行失败: {version_check.stderr or version_check.stdout}'
        return True, ''

    def _write_config(self, config: dict[str, Any], execution_id: str) -> str:
        config_file = os.path.join(self.datax_job_dir, f'datax_{execution_id}.json')
        with open(config_file, 'w', encoding='utf-8') as file_obj:
            json.dump(config, file_obj, ensure_ascii=False, indent=2)
        return config_file

    def _parse_datax_log(self) -> tuple[int, int, int]:
        if not self.log_file or not os.path.exists(self.log_file):
            return 0, 0, 0
        content = Path(self.log_file).read_text(encoding='utf-8', errors='ignore')
        total_rows = self._extract_last_metric(content, ['总记录数', 'Total records'])
        success_rows = self._extract_last_metric(content, ['成功读取', '成功写入', 'Success'])
        failed_rows = self._extract_last_metric(content, ['失败读取', '失败写入', 'Failed'])
        if total_rows == 0 and success_rows:
            total_rows = success_rows
        return total_rows, success_rows, failed_rows

    def _extract_last_metric(self, content: str, keywords: list[str]) -> int:
        matched_value = 0
        for line in content.splitlines():
            if not any(keyword in line for keyword in keywords):
                continue
            numbers = re.findall(r'(\d+)', line)
            if numbers:
                matched_value = int(numbers[-1])
        return matched_value

    def _parse_error_log(self) -> str:
        if not self.log_file or not os.path.exists(self.log_file):
            return '未找到 DataX 日志文件'
        lines = Path(self.log_file).read_text(encoding='utf-8', errors='ignore').splitlines()
        error_lines = [
            line.strip()
            for line in lines
            if any(keyword in line for keyword in ['ERROR', 'Exception', 'Error', '错误'])
        ]
        if not error_lines:
            return 'DataX 执行失败，请查看日志'
        return '\n'.join(error_lines[-5:])

    def _cleanup(self):
        if self.config_file and os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except OSError:
                logger.warning('清理 DataX 配置文件失败: %s', self.config_file)

    def _generate_execution_id(self) -> str:
        task_code = getattr(self.task, 'task_code', 'datax_task')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f'{task_code}_{timestamp}'


ExecutorFactory.register_executor('datax', DataXExecutor)
