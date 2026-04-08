"""
通用执行器基类与工厂。

该模块位于 apps.executors，供各业务模块复用。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """执行器抽象基类。"""

    def __init__(self, task: Any, config: Dict[str, Any] | None = None):
        self.task = task
        self.config = config or {}
        self._is_cancelled = False

    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """执行前校验，返回 (是否通过, 错误信息)。"""

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行任务并返回标准结果字典。"""

    @abstractmethod
    def cancel(self) -> bool:
        """取消执行。"""

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def _mark_cancelled(self):
        self._is_cancelled = True


class ExecutorFactory:
    """执行器工厂，管理执行器注册与实例化。"""

    _executors: Dict[str, type[BaseExecutor]] = {}

    @classmethod
    def register_executor(cls, executor_type: str, executor_class: type[BaseExecutor]):
        if not issubclass(executor_class, BaseExecutor):
            raise ValueError("Executor class must inherit from BaseExecutor")
        cls._executors[executor_type] = executor_class
        logger.info("Registered executor: %s -> %s", executor_type, executor_class.__name__)

    @classmethod
    def create_executor(
        cls,
        executor_type: str,
        task: Any,
        config: Dict[str, Any] | None = None,
    ) -> BaseExecutor:
        executor_class = cls._executors.get(executor_type)
        if executor_class is None:
            raise ValueError(
                f"Unknown executor type: {executor_type}. "
                f"Available types: {list(cls._executors.keys())}"
            )

        return executor_class(task, config)

    @classmethod
    def list_executors(cls) -> list[str]:
        return list(cls._executors.keys())


# 向后兼容别名：历史模块使用 BaseETLExecutor 名称
BaseETLExecutor = BaseExecutor

__all__ = [
    'BaseExecutor',
    'BaseETLExecutor',
    'ExecutorFactory',
]
