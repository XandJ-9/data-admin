"""
ETL Executor Base Classes

This module defines the abstract base class and factory for ETL executors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseETLExecutor(ABC):
    """
    Abstract base class for ETL executors.

    All executor implementations must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, task: Any, config: Dict[str, Any] = None):
        """
        Initialize executor with task and configuration.

        Args:
            task: ETLTask instance
            config: Executor configuration dictionary
        """
        self.task = task
        self.config = config or {}
        self._is_cancelled = False

    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """
        Validate task configuration before execution.

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if configuration is valid
            - error_message: Error message if validation fails, empty string if valid
        """
        pass

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the ETL task.

        Returns:
            Dictionary containing execution results with keys:
            - status: 'success' or 'failed'
            - total_rows: Total number of rows processed
            - success_rows: Number of successfully processed rows
            - failed_rows: Number of failed rows
            - duration_seconds: Execution duration in seconds
            - error_message: Error message if execution failed
        """
        pass

    @abstractmethod
    def cancel(self) -> bool:
        """
        Cancel the running ETL task.

        Returns:
            True if cancellation was successful, False otherwise
        """
        pass

    def is_cancelled(self) -> bool:
        """Check if the task has been cancelled."""
        return self._is_cancelled

    def _mark_cancelled(self):
        """Mark the task as cancelled."""
        self._is_cancelled = True


class ExecutorFactory:
    """
    Factory class for creating executor instances.

    This factory manages executor registration and instantiation.
    """

    _executors = {
        'mock': None,  # Will be set after MockETLExecutor is defined
        # Future executors:
        # 'datax': None,
        # 'spark': None,
        # 'python': None,
    }

    @classmethod
    def register_executor(cls, executor_type: str, executor_class: type):
        """
        Register an executor class.

        Args:
            executor_type: Executor type identifier (e.g., 'mock', 'datax', 'spark')
            executor_class: Executor class (must inherit from BaseETLExecutor)
        """
        if not issubclass(executor_class, BaseETLExecutor):
            raise ValueError(f"Executor class must inherit from BaseETLExecutor")
        cls._executors[executor_type] = executor_class
        logger.info(f"Registered executor: {executor_type} -> {executor_class.__name__}")

    @classmethod
    def create_executor(cls, executor_type: str, task: Any, config: Dict[str, Any] = None) -> BaseETLExecutor:
        """
        Create an executor instance.

        Args:
            executor_type: Type of executor to create
            task: ETLTask instance
            config: Executor configuration

        Returns:
            Executor instance

        Raises:
            ValueError: If executor type is not registered
        """
        executor_class = cls._executors.get(executor_type)
        if executor_class is None:
            raise ValueError(f"Unknown executor type: {executor_type}. "
                           f"Available types: {list(cls._executors.keys())}")

        return executor_class(task, config)

    @classmethod
    def list_executors(cls) -> list:
        """List all registered executor types."""
        return list(cls._executors.keys())
