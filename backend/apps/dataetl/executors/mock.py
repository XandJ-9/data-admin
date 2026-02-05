"""
Mock ETL Executor

This module provides a mock executor for development and testing purposes.
"""

import time
import random
from typing import Dict, Any, Tuple
from datetime import datetime
import logging

from .base import BaseETLExecutor, ExecutorFactory

logger = logging.getLogger(__name__)


class MockETLExecutor(BaseETLExecutor):
    """
    Mock ETL executor for development and testing.

    This executor simulates ETL task execution without actually
    connecting to data sources or processing data.
    """

    def validate(self) -> Tuple[bool, str]:
        """
        Validate task configuration.

        For mock executor, validation always passes as long as
        basic fields are present.
        """
        # Check if task has required fields
        if not self.task.task_code:
            return False, "任务编码不能为空"

        if not self.task.source_datasource_id:
            return False, "源数据源不能为空"

        if not self.task.target_datasource_id:
            return False, "目标数据源不能为空"

        # Mock validation always passes for basic configuration
        logger.info(f"Mock validation passed for task: {self.task.task_code}")
        return True, ""

    def execute(self) -> Dict[str, Any]:
        """
        Simulate ETL task execution.

        This method simulates execution with randomized results:
        - 90% success rate
        - Random duration between 1-5 seconds
        - Random row counts
        """
        logger.info(f"Mock execution started for task: {self.task.task_code}")

        start_time = time.time()

        # Simulate execution time (1-5 seconds)
        duration = random.uniform(1, 5)
        time.sleep(duration)

        # Simulate success/failure (90% success rate)
        success = random.random() < 0.9

        # Generate random row counts
        total_rows = random.randint(1000, 100000)

        if success:
            success_rows = total_rows
            failed_rows = 0
            status = 'success'
            error_message = None
        else:
            success_rows = random.randint(0, int(total_rows * 0.8))
            failed_rows = total_rows - success_rows
            status = 'failed'
            error_message = "模拟执行失败：随机生成错误（用于测试失败场景）"

        end_time = time.time()
        duration_seconds = int(end_time - start_time)

        result = {
            'status': status,
            'total_rows': total_rows,
            'success_rows': success_rows,
            'failed_rows': failed_rows,
            'duration_seconds': duration_seconds,
            'error_message': error_message,
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
        }

        logger.info(f"Mock execution completed for task: {self.task.task_code}, "
                   f"status: {status}, rows: {total_rows}, duration: {duration_seconds}s")

        return result

    def cancel(self) -> bool:
        """
        Cancel the mock execution.

        For mock executor, cancellation is always successful
        but only effective if called before execution completes.
        """
        self._mark_cancelled()
        logger.info(f"Mock execution cancelled for task: {self.task.task_code}")
        return True


# Register the mock executor
ExecutorFactory.register_executor('mock', MockETLExecutor)
