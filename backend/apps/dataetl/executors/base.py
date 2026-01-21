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
from apps.dataetl.models import IntegrationTask, TaskExecutionLog, DataLineage

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """
    ETL执行器抽象基类

    所有具体执行器（DataX、Spark SQL等）必须继承此类并实现抽象方法
    """

    def __init__(self, task: IntegrationTask, execution_log: TaskExecutionLog):
        """
        初始化执行器

        Args:
            task: ETL任务实例
            execution_log: 执行日志实例
        """
        self.task = task
        self.execution_log = execution_log
        self.config = task.detail  # 或从专门的配置表读取

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
                'rows_error': int,
                'bytes_transferred': int,
                'error_message': str (if failed),
                'log_path': str
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
                    create_by=self.execution_log.create_by,
                    update_by=self.execution_log.create_by,
                )

            # 创建字段级血缘
            if self.task.field_mapping and self.task.source_datasource and self.task.target_datasource:
                for mapping in self.task.field_mapping:
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
                            create_by=self.execution_log.create_by,
                            update_by=self.execution_log.create_by,
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
        更新执行日志

        Args:
            result: execute()方法返回的执行结果
        """
        try:
            end_time = timezone.now()
            duration = int((end_time - self.execution_log.start_time).total_seconds()) if self.execution_log.start_time else 0

            self.execution_log.end_time = end_time
            self.execution_log.duration_seconds = duration
            self.execution_log.status = result.get('status', 'failed')
            self.execution_log.rows_read = result.get('rows_read', 0)
            self.execution_log.rows_written = result.get('rows_written', 0)
            self.execution_log.rows_error = result.get('rows_error', 0)
            self.execution_log.bytes_transferred = result.get('bytes_transferred', 0)
            self.execution_log.log_path = result.get('log_path', '')
            self.execution_log.error_message = result.get('error_message', '')
            self.execution_log.save(update_fields=[
                'end_time', 'duration_seconds', 'status',
                'rows_read', 'rows_written', 'rows_error', 'bytes_transferred',
                'log_path', 'error_message', 'update_time'
            ])

        except Exception as e:
            logger.error(f"更新执行日志失败: {str(e)}")
