"""
执行器工厂 - 向后兼容模块

注意：此模块保留用于向后兼容。新代码应使用 base.ExecutorFactory

已弃用：请使用 base.ExecutorFactory 代替
"""

import logging
from typing import Dict, Any
from .base import BaseETLExecutor

logger = logging.getLogger(__name__)


# 保留此模块用于向后兼容，但重定向到新的 ExecutorFactory
from .base import ExecutorFactory

__all__ = ['ExecutorFactory', 'get_supported_executors']


def get_supported_executors() -> list:
    """
    获取支持的执行器类型列表

    Returns:
        执行器类型列表
    """
    return [
        {'value': 'mock', 'label': '模拟执行器', 'description': '用于开发和测试'},
        {'value': 'datax', 'label': 'DataX执行器', 'description': '用于数据同步，支持多种数据源'},
        {'value': 'spark', 'label': 'Spark SQL执行器', 'description': '用于 Spark 集群 SQL 开发执行'},
        {'value': 'hive', 'label': 'Hive SQL执行器', 'description': '用于 Hive SQL 开发执行'},
        {'value': 'python', 'label': 'Python脚本执行器', 'description': '执行自定义Python脚本'},
    ]
