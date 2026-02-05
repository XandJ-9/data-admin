"""
ETL Executors Package

This package provides executor implementations for different ETL engines:
- BaseETLExecutor: Abstract base class for all executors
- MockETLExecutor: Mock executor for development and testing
- (Future) DataXExecutor: DataX executor
- (Future) SparkExecutor: Spark SQL executor
"""

from .base import BaseETLExecutor, ExecutorFactory
from .mock import MockETLExecutor

__all__ = [
    'BaseETLExecutor',
    'ExecutorFactory',
    'MockETLExecutor',
]
