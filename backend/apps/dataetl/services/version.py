"""
VersionService - ETL任务版本管理服务

处理ETL任务的版本创建、查询、回滚等
"""

import logging
from typing import List, Dict, Any, Optional
from django.db import transaction

from ..models import ETLTask, ETLTaskVersion

logger = logging.getLogger(__name__)


class VersionService:
    """
    ETL任务版本管理服务
    """

    @staticmethod
    @transaction.atomic
    def create_version(task: ETLTask, change_log: str, create_by: str) -> ETLTaskVersion:
        """
        创建任务版本快照

        Args:
            task: ETL任务实例
            change_log: 变更日志
            create_by: 创建者

        Returns:
            创建的版本实例
        """
        # 获取最新的版本号
        latest_version = ETLTaskVersion.objects.filter(
            task=task
        ).order_by('-version_number').first()
        version_number = (latest_version.version_number + 1) if latest_version else 1

        # 创建配置快照
        config_snapshot = VersionService._create_config_snapshot(task)

        # 取消所有旧版本的当前标记
        ETLTaskVersion.objects.filter(task=task).update(is_current=False)

        # 创建新版本
        version = ETLTaskVersion.objects.create(
            task=task,
            version_number=version_number,
            config_snapshot=config_snapshot,
            change_log=change_log,
            is_current=True,
            create_by=create_by
        )

        logger.info(f"创建任务版本: {task.task_name} - v{version_number}")

        return version

    @staticmethod
    def get_task_versions(task: ETLTask) -> List[ETLTaskVersion]:
        """
        获取任务的所有版本

        Args:
            task: ETL任务实例

        Returns:
            版本列表
        """
        return list(ETLTaskVersion.objects.filter(
            task=task
        ).order_by('-version_number'))

    @staticmethod
    @transaction.atomic
    def rollback_version(task: ETLTask, version_number: int) -> bool:
        """
        回滚到指定版本

        Args:
            task: ETL任务实例
            version_number: 要回滚到的版本号

        Returns:
            是否回滚成功

        Raises:
            ValueError: 版本不存在
        """
        # 获取目标版本
        try:
            version = ETLTaskVersion.objects.get(
                task=task,
                version_number=version_number
            )
        except ETLTaskVersion.DoesNotExist:
            raise ValueError(f'版本 {version_number} 不存在')

        # 恢复配置
        snapshot = version.config_snapshot
        task.task_name = snapshot.get('taskName', task.task_name)
        task.description = snapshot.get('description', task.description)
        task.etl_type = snapshot.get('etlType', task.etl_type)
        task.executor_type = snapshot.get('executorType', task.executor_type)
        task.execute_strategy = snapshot.get('executeStrategy', task.execute_strategy)
        task.source_datasource_id = snapshot.get('sourceDatasourceId', task.source_datasource_id)
        task.target_datasource_id = snapshot.get('targetDatasourceId', task.target_datasource_id)
        task.source_table_id = snapshot.get('sourceTableId', task.source_table_id)
        task.target_table = snapshot.get('targetTable', task.target_table)
        task.sql_config = snapshot.get('sqlConfig', task.sql_config)
        task.executor_params = snapshot.get('executorParams', task.executor_params)
        task.status = snapshot.get('status', task.status)
        task.save()

        logger.info(f"回滚任务版本: {task.task_name} -> v{version_number}")

        return True

    @staticmethod
    def get_current_version(task: ETLTask) -> Optional[ETLTaskVersion]:
        """
        获取任务的当前版本

        Args:
            task: ETL任务实例

        Returns:
            当前版本实例，如果不存在则返回None
        """
        try:
            return ETLTaskVersion.objects.filter(
                task=task,
                is_current=True
            ).first()
        except ETLTaskVersion.DoesNotExist:
            return None

    @staticmethod
    def _create_config_snapshot(task: ETLTask) -> Dict[str, Any]:
        """
        创建配置快照

        Args:
            task: ETL任务实例

        Returns:
            配置快照字典
        """
        return {
            'taskName': task.task_name,
            'taskCode': task.task_code,
            'description': task.description,
            'etlType': task.etl_type,
            'executorType': task.executor_type,
            'executeStrategy': task.execute_strategy,
            'sourceDatasourceId': task.source_datasource_id,
            'targetDatasourceId': task.target_datasource_id,
            'sourceTableId': task.source_table_id,
            'targetTable': task.target_table,
            'sqlConfig': task.sql_config,
            'executorParams': task.executor_params,
            'status': task.status,
            # 新字段
            'taskConfig': task.task_config if hasattr(task, 'task_config') else None,
            'executionConfig': task.execution_config if hasattr(task, 'execution_config') else None,
            'qualityConfig': task.quality_config if hasattr(task, 'quality_config') else None,
            'category': task.category if hasattr(task, 'category') else None,
            'tags': task.tags if hasattr(task, 'tags') else None,
        }
