"""
执行器工厂

根据任务配置返回对应的执行器实例
"""

from typing import Union
from .base import BaseExecutor
from .datax_executor import DataXExecutor
from .sparksql_executor import SparkSQLExecutor
from apps.dataetl.models import IntegrationTask, TaskExecutionLog


def get_executor(task: IntegrationTask, execution_log: TaskExecutionLog) -> BaseExecutor:
    """
    执行器工厂方法

    根据任务的executor_type返回对应的执行器实例

    Args:
        task: ETL任务实例
        execution_log: 执行日志实例

    Returns:
        执行器实例

    Raises:
        ValueError: 不支持的执行器类型
    """
    executor_type = task.executor_type.lower() if task.executor_type else 'datax'

    if executor_type == 'datax':
        return DataXExecutor(task, execution_log)
    elif executor_type == 'spark_sql':
        return SparkSQLExecutor(task, execution_log)
    else:
        raise ValueError(f"不支持的执行器类型: {executor_type}")


def get_supported_executors() -> list:
    """
    获取支持的执行器类型列表

    Returns:
        执行器类型列表
    """
    return [
        {'value': 'datax', 'label': 'DataX执行器', 'description': '用于数据同步，支持多种数据源'},
        {'value': 'spark_sql', 'label': 'Spark SQL执行器', 'description': '用于大数据处理和复杂转换'},
    ]
