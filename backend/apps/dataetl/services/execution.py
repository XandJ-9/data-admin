"""
ExecutionService - ETL任务执行服务

处理ETL任务的执行、进度跟踪、状态管理
"""

import uuid
import threading
import logging
from typing import Dict, Any
from django.utils import timezone

from ..models import ETLTask, ETLExecutionLog, ETLExecutionProgress
from ..executors import ExecutorFactory
from .quality import QualityService

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    ETL任务执行服务
    处理任务执行的生命周期管理
    """

    def __init__(self):
        self.quality_service = QualityService()

    def submit_task(self, task: ETLTask, executed_by: str, trigger_type: str = 'manual') -> str:
        """
        提交任务执行

        Args:
            task: ETL任务实例
            executed_by: 执行者
            trigger_type: 触发类型

        Returns:
            执行ID
        """
        # 检查任务状态
        if task.status != '0':
            raise ValueError('任务已停用，无法执行')

        # 生成执行ID
        execution_id = f"ETL-{uuid.uuid4().hex[:16].upper()}"

        # 创建执行日志
        log = ETLExecutionLog.objects.create(
            task=task,
            execution_id=execution_id,
            status='pending',
            trigger_type=trigger_type,
            executed_by=executed_by,
            executor_params=task.executor_params
        )

        # 异步执行任务
        thread = threading.Thread(
            target=self._execute_async,
            args=(task, log)
        )
        thread.daemon = True
        thread.start()

        return execution_id

    def _execute_async(self, task: ETLTask, log: ETLExecutionLog):
        """
        异步执行ETL任务

        Args:
            task: ETLTask实例
            log: ETLExecutionLog实例
        """
        # 创建进度跟踪
        progress = ETLExecutionProgress.objects.create(
            execution=log,
            current_stage='initializing',
            progress_percentage=0,
        )

        try:
            # 更新状态为执行中
            log.status = 'running'
            log.start_time = timezone.now()
            log.save()

            progress.current_stage = 'validating'
            progress.progress_percentage = 10
            progress.save()

            # 执行前质检
            quality_passed, quality_errors = self.quality_service.run_pre_check(task)
            if not quality_passed:
                raise Exception(f"数据质量检查失败: {'; '.join(quality_errors)}")

            progress.current_stage = 'executing'
            progress.progress_percentage = 20
            progress.save()

            # 创建执行器实例
            executor = ExecutorFactory.create_executor(
                task.executor_type,
                task,
                task.executor_params
            )

            # 验证配置
            is_valid, error_message = executor.validate()
            if not is_valid:
                raise Exception(f"任务配置验证失败: {error_message}")

            # 执行任务
            result = executor.execute()

            progress.current_stage = 'finalizing'
            progress.progress_percentage = 90
            progress.save()

            # 执行后质检
            self.quality_service.run_post_check(task, log.execution_id)

            # 更新执行日志
            log.status = result.get('status', 'failed')
            log.end_time = timezone.now()
            log.duration_seconds = result.get('duration_seconds')
            log.total_rows = result.get('total_rows')
            log.success_rows = result.get('success_rows')
            log.failed_rows = result.get('failed_rows')
            log.error_message = result.get('error_message')
            log.save()

            progress.current_stage = 'completed'
            progress.progress_percentage = 100
            progress.heartbeat_time = timezone.now()
            progress.save()

        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}", exc_info=True)

            # 执行失败
            log.status = 'failed'
            log.end_time = timezone.now()
            if log.start_time:
                log.duration_seconds = int((log.end_time - log.start_time).total_seconds())
            log.error_message = str(e)
            log.save()

            progress.current_stage = 'failed'
            progress.heartbeat_time = timezone.now()
            progress.save()

    def cancel_execution(self, execution: ETLExecutionLog) -> bool:
        """
        取消执行

        Args:
            execution: 执行日志实例

        Returns:
            是否成功取消
        """
        if execution.status != 'running':
            return False

        try:
            # TODO: 实现真正的取消逻辑
            # 需要在执行器中实现cancel方法，并在此调用
            execution.status = 'cancelled'
            execution.end_time = timezone.now()
            execution.save()

            # 更新进度
            if hasattr(execution, 'progress'):
                progress = execution.progress
                progress.current_stage = 'cancelled'
                progress.save()

            return True
        except Exception as e:
            logger.error(f"取消执行失败: {str(e)}", exc_info=True)
            return False

    def create_progress(self, execution: ETLExecutionLog,
                       current_stage: str = 'initializing',
                       progress_percentage: int = 0) -> ETLExecutionProgress:
        """
        创建执行进度记录

        Args:
            execution: 执行日志实例
            current_stage: 当前阶段
            progress_percentage: 进度百分比

        Returns:
            执行进度实例
        """
        return ETLExecutionProgress.objects.create(
            execution=execution,
            current_stage=current_stage,
            progress_percentage=progress_percentage,
        )

    def update_progress(self, execution: ETLExecutionLog, **kwargs) -> bool:
        """
        更新执行进度

        Args:
            execution: 执行日志实例
            **kwargs: 要更新的字段

        Returns:
            是否更新成功
        """
        try:
            progress = ETLExecutionProgress.objects.get(execution=execution)
            for key, value in kwargs.items():
                setattr(progress, key, value)
            progress.save()
            return True
        except ETLExecutionProgress.DoesNotExist:
            return False
