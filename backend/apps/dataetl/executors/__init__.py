"""
ETL执行器模块

支持多种执行引擎：
- BaseExecutor: 执行器基类
- DataXExecutor: DataX数据同步执行器
- SparkSQLExecutor: Spark SQL执行器
"""

from .base import BaseExecutor
from .datax_executor import DataXExecutor
from .sparksql_executor import SparkSQLExecutor
from .factory import get_executor

__all__ = [
    'BaseExecutor',
    'DataXExecutor',
    'SparkSQLExecutor',
    'get_executor',
]
