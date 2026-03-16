"""
TaskExecutionService - 通用任务执行跟踪服务
为所有模块提供统一的执行记录、进度更新、日志记录功能
"""

import logging
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from apps.datataskmonitor.models import TaskExecution, TaskExecutionLog

logger = logging.getLogger(__name__)


class TaskExecutionService:
    """
    通用任务执行服务
    提供统一的执行跟踪、日志记录、进度更新功能
    """

    @staticmethod
    def create_execution(
        task_type: str,
        task_id: int,
        executor_type: str = '',
        execution_params: Optional[Dict[str, Any]] = None
    ) -> TaskExecution:
        """
        创建新的任务执行记录

        Args:
            task_type: 任务类型 (etl, metadata_collection, quality_check, etc.)
            task_id: 任务ID
            executor_type: 执行器类型 (datax, spark_sql, etc.)
            execution_params: 执行参数快照

        Returns:
            TaskExecution: 创建的执行记录
        """
        execution = TaskExecution.objects.create(
            task_type=task_type,
            task_id=task_id,
            executor_type=executor_type,
            execution_params=execution_params or {},
            status='running',
            progress=0
        )
        logger.info(f"Created TaskExecution #{execution.id} for {task_type} #{task_id}")
        return execution

    @staticmethod
    def update_progress(execution_id: int, progress: int, message: str = '') -> bool:
        """
        更新任务执行进度

        Args:
            execution_id: 执行记录ID
            progress: 进度百分比 (0-100)
            message: 可选的进度消息

        Returns:
            bool: 更新是否成功
        """
        try:
            execution = TaskExecution.objects.get(id=execution_id)
            if execution.status == 'cancelled':
                return False

            execution.progress = max(0, min(100, progress))
            execution.save(update_fields=['progress'])

            # 如果提供了消息，记录日志
            if message:
                TaskExecutionService.add_log(execution_id, 'INFO', message)

            return True
        except TaskExecution.DoesNotExist:
            logger.error(f"TaskExecution #{execution_id} not found")
            return False

    @staticmethod
    def complete_execution(
        execution_id: int,
        status: str,
        rows_read: Optional[int] = None,
        rows_written: Optional[int] = None,
        bytes_processed: Optional[int] = None,
        error_message: str = '',
        error_stack: str = ''
    ) -> bool:
        """
        完成任务执行

        Args:
            execution_id: 执行记录ID
            status: 最终状态 (success, failed, cancelled)
            rows_read: 读取行数
            rows_written: 写入行数
            bytes_processed: 处理字节数
            error_message: 错误信息
            error_stack: 错误堆栈

        Returns:
            bool: 更新是否成功
        """
        try:
            with transaction.atomic():
                execution = TaskExecution.objects.select_for_update().get(id=execution_id)

                # 只允许完成 running 状态的任务
                if execution.status != 'running':
                    logger.warning(f"TaskExecution #{execution_id} is not running, current status: {execution.status}")
                    return False

                execution.end_time = timezone.now()
                execution.status = status

                if rows_read is not None:
                    execution.rows_read = rows_read
                if rows_written is not None:
                    execution.rows_written = rows_written
                if bytes_processed is not None:
                    execution.bytes_processed = bytes_processed

                if error_message:
                    execution.error_message = error_message
                if error_stack:
                    execution.error_stack = error_stack

                execution.progress = 100 if status == 'success' else execution.progress
                execution.save()

                logger.info(f"Completed TaskExecution #{execution_id} with status: {status}")
                return True

        except TaskExecution.DoesNotExist:
            logger.error(f"TaskExecution #{execution_id} not found")
            return False

    @staticmethod
    def add_log(
        execution_id: int,
        log_level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskExecutionLog]:
        """
        添加执行日志

        Args:
            execution_id: 执行记录ID
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            message: 日志消息
            metadata: 可选的元数据

        Returns:
            TaskExecutionLog: 创建的日志条目，失败返回 None
        """
        try:
            log_entry = TaskExecutionLog.objects.create(
                execution_id=execution_id,
                log_level=log_level,
                message=message,
                metadata=metadata
            )
            return log_entry
        except Exception as e:
            logger.error(f"Failed to add log to TaskExecution #{execution_id}: {e}")
            return None

    @staticmethod
    def get_execution(execution_id: int) -> Optional[TaskExecution]:
        """
        获取执行记录

        Args:
            execution_id: 执行记录ID

        Returns:
            TaskExecution: 执行记录，不存在返回 None
        """
        try:
            return TaskExecution.objects.get(id=execution_id)
        except TaskExecution.DoesNotExist:
            return None

    @staticmethod
    def get_executions_by_task(
        task_type: str,
        task_id: int,
        limit: int = 10
    ) -> List[TaskExecution]:
        """
        获取任务的所有执行记录

        Args:
            task_type: 任务类型
            task_id: 任务ID
            limit: 返回记录数量

        Returns:
            List[TaskExecution]: 执行记录列表
        """
        return list(
            TaskExecution.objects.filter(
                task_type=task_type,
                task_id=task_id
            ).order_by('-start_time')[:limit]
        )

    @staticmethod
    def get_logs(
        execution_id: int,
        log_level: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskExecutionLog]:
        """
        获取执行日志

        Args:
            execution_id: 执行记录ID
            log_level: 过滤日志级别 (可选)
            limit: 返回记录数量

        Returns:
            List[TaskExecutionLog]: 日志条目列表
        """
        queryset = TaskExecutionLog.objects.filter(execution_id=execution_id)

        if log_level:
            queryset = queryset.filter(log_level=log_level)

        return list(queryset.order_by('create_time')[:limit])

    @staticmethod
    def cancel_execution(execution_id: int) -> bool:
        """
        取消正在运行的任务

        Args:
            execution_id: 执行记录ID

        Returns:
            bool: 取消是否成功
        """
        try:
            execution = TaskExecution.objects.get(id=execution_id)
            if execution.status == 'running':
                execution.status = 'cancelled'
                execution.end_time = timezone.now()
                execution.save()
                TaskExecutionService.add_log(execution_id, 'WARNING', 'Task execution cancelled')
                return True
            return False
        except TaskExecution.DoesNotExist:
            return False

    @staticmethod
    def get_running_executions(task_type: Optional[str] = None) -> List[TaskExecution]:
        """
        获取所有正在运行的执行记录

        Args:
            task_type: 可选的任务类型过滤

        Returns:
            List[TaskExecution]: 正在运行的执行记录列表
        """
        queryset = TaskExecution.objects.filter(status='running')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        return list(queryset.order_by('start_time'))


# 便捷函数别名
create_execution = TaskExecutionService.create_execution
update_progress = TaskExecutionService.update_progress
complete_execution = TaskExecutionService.complete_execution
add_log = TaskExecutionService.add_log
get_execution = TaskExecutionService.get_execution
get_executions_by_task = TaskExecutionService.get_executions_by_task
get_logs = TaskExecutionService.get_logs
cancel_execution = TaskExecutionService.cancel_execution
get_running_executions = TaskExecutionService.get_running_executions
