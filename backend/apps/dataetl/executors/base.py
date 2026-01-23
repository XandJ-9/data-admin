"""
ETL执行器基类

定义所有执行器的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import logging
import uuid
from datetime import datetime

from django.utils import timezone
from apps.dataetl.models import ETLTask, ETLExecution, DataLineage
from apps.datataskmonitor.services.execution import TaskExecutionService
from apps.datataskmonitor.models import TaskExecution

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """
    ETL执行器抽象基类

    所有具体执行器（DataX、Spark SQL等）必须继承此类并实现抽象方法

    新架构说明：
    - 使用 TaskExecution 跟踪通用执行状态（跨所有任务类型）
    - 使用 ETLExecution 存储 ETL 特定指标
    - 使用 TaskExecutionLog 流式记录日志
    """

    def __init__(self, task: ETLTask, etl_execution: ETLExecution):
        """
        初始化执行器

        Args:
            task: ETL任务实例
            etl_execution: ETL执行记录实例（关联到TaskExecution）
        """
        self.task = task
        self.etl_execution = etl_execution
        # 获取关联的通用执行记录
        self.task_execution = etl_execution.execution
        self.config = task.executor_config or {}

    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """
        验证任务配置是否有效

        Returns:
            (is_valid, error_message): 是否有效，错误信息
        """
        pass

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        执行ETL任务

        Returns:
            执行结果字典:
            {
                'status': 'success' | 'failed',
                'rows_read': int,
                'rows_written': int,
                'rows_failed': int,
                'bytes_processed': int,
                'error_message': str (if failed),
                'log_file_path': str
            }
        """
        pass

    @abstractmethod
    def cancel(self) -> bool:
        """
        取消正在执行的任务

        Returns:
            是否成功取消
        """
        pass

    def _generate_execution_id(self) -> str:
        """
        生成唯一执行ID

        Returns:
            执行ID字符串
        """
        return f"{self.task.id}_{uuid.uuid4().hex[:12]}"

    def update_progress(self, progress: int, message: str = '', current_stage: str = ''):
        """
        更新执行进度

        Args:
            progress: 进度百分比 (0-100)
            message: 进度消息
            current_stage: 当前阶段描述
        """
        try:
            TaskExecutionService.update_progress(
                self.task_execution.id,
                progress,
                message
            )
        except Exception as e:
            logger.error(f"更新进度失败: {str(e)}")

    def add_log(self, log_level: str, message: str, metadata: Dict = None):
        """
        添加执行日志

        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            message: 日志消息
            metadata: 额外元数据
        """
        try:
            TaskExecutionService.add_log(
                self.task_execution.id,
                log_level,
                message,
                metadata
            )
        except Exception as e:
            logger.error(f"添加日志失败: {str(e)}")

    def complete_execution(self, status: str, rows_read: int = None, rows_written: int = None,
                          rows_failed: int = 0, bytes_processed: int = None,
                          error_message: str = '', log_file_path: str = ''):
        """
        完成执行（成功或失败）

        Args:
            status: 执行状态 (success, failed, cancelled)
            rows_read: 读取行数
            rows_written: 写入行数
            rows_failed: 失败行数
            bytes_processed: 处理字节数
            error_message: 错误消息
            log_file_path: 日志文件路径
        """
        try:
            # 更新通用执行记录
            TaskExecutionService.complete_execution(
                self.task_execution.id,
                status,
                rows_read=rows_read,
                rows_written=rows_written,
                bytes_processed=bytes_processed,
                error_message=error_message
            )

            # 更新ETL特定执行记录
            self.etl_execution.rows_read = rows_read or 0
            self.etl_execution.rows_written = rows_written or 0
            self.etl_execution.rows_failed = rows_failed
            self.etl_execution.error_message = error_message
            self.etl_execution.log_file_path = log_file_path
            self.etl_execution.end_time = timezone.now()
            self.etl_execution.save(update_fields=[
                'rows_read', 'rows_written', 'rows_failed',
                'error_message', 'log_file_path', 'end_time', 'update_time'
            ])

        except Exception as e:
            logger.error(f"完成执行记录失败: {str(e)}")

    def _sync_lineage(self):
        """
        执行后同步血缘关系

        根据任务配置自动提取表级和字段级血缘关系
        """
        try:
            # 删除旧血缘
            DataLineage.objects.filter(source_task=self.task).delete()

            # 创建表级血缘
            if self.task.source_datasource and self.task.target_datasource:
                DataLineage.objects.create(
                    source_task=self.task,
                    lineage_type='table',
                    source_datasource=self.task.source_datasource,
                    source_table=self.task.source_table,
                    target_datasource=self.task.target_datasource,
                    target_table=self.task.target_table,
                    transform_rule=f'{self.task.executor_type} task',
                    create_by=self.task_execution.create_by,
                    update_by=self.task_execution.create_by,
                )

            # 创建字段级血缘
            if self.task.field_mappings and self.task.source_datasource and self.task.target_datasource:
                for mapping in self.task.field_mappings:
                    source_field = mapping.get('source')
                    target_field = mapping.get('target')

                    if source_field and target_field:
                        DataLineage.objects.create(
                            source_task=self.task,
                            lineage_type='field',
                            source_datasource=self.task.source_datasource,
                            source_table=self.task.source_table,
                            source_field=source_field,
                            target_datasource=self.task.target_datasource,
                            target_table=self.task.target_table,
                            target_field=target_field,
                            transform_rule=mapping.get('transform', 'direct'),
                            create_by=self.task_execution.create_by,
                            update_by=self.task_execution.create_by,
                        )

            logger.info(f"血缘关系同步成功: 任务={self.task.name}")

        except Exception as e:
            logger.error(f"血缘关系同步失败: {str(e)}")

    def _trigger_quality_check(self):
        """
        触发质量检查

        ETL执行后自动触发数据质量检查（待实现）

        TODO: 集成Quality模块
        """
        # TODO: 集成Quality模块，触发质量检查
        # 1. 查找绑定到目标表的质量规则
        # 2. 异步执行质量检查
        # 3. 记录检查结果
        pass

    def update_execution_log(self, result: Dict[str, Any]):
        """
        更新执行日志（兼容旧方法，委托给complete_execution）

        Args:
            result: execute()方法返回的执行结果
        """
        self.complete_execution(
            status=result.get('status', 'failed'),
            rows_read=result.get('rows_read', 0),
            rows_written=result.get('rows_written', 0),
            rows_failed=result.get('rows_error', 0),
            bytes_processed=result.get('bytes_transferred', 0),
            error_message=result.get('error_message', ''),
            log_file_path=result.get('log_path', '')
        )

