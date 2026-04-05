"""
ConfigService - ETL任务配置服务

处理任务配置验证、生成、预览等
"""

import logging
from typing import Tuple, Dict, Any
from datetime import datetime

from ..models import ETLTask
from apps.executors.datax_config_builder import DataXConfigBuilder

logger = logging.getLogger(__name__)


class ConfigService:
    """
    ETL任务配置服务
    """

    def validate_datax_config(self, task: ETLTask) -> Tuple[bool, list, Dict]:
        """
        验证DataX配置

        Args:
            task: ETL任务实例

        Returns:
            (是否有效, 警告列表, 配置字典)
        """
        if task.executor_type != 'datax':
            raise ValueError('仅支持DataX执行器的配置验证')

        try:
            config_builder = DataXConfigBuilder(task)
            is_valid, error_msg = config_builder.validate_config()

            if is_valid:
                # 生成配置用于预览
                execution_date = datetime.now().strftime('%Y%m%d')
                config = config_builder.build(execution_date)

                return True, [], config
            else:
                return False, [error_msg], None

        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}", exc_info=True)
            raise

    def generate_datax_config(self, task: ETLTask, execution_date: str = None) -> Dict:
        """
        生成DataX JSON配置

        Args:
            task: ETL任务实例
            execution_date: 执行日期（YYYYMMDD格式）

        Returns:
            包含配置和执行日期的字典
        """
        if task.executor_type != 'datax':
            raise ValueError('仅支持DataX执行器')

        if not execution_date:
            execution_date = datetime.now().strftime('%Y%m%d')

        config_builder = DataXConfigBuilder(task)
        config = config_builder.build(execution_date)

        return {
            'config': config,
            'executionDate': execution_date
        }

    def dry_run(self, task: ETLTask) -> Dict[str, Any]:
        """
        模拟执行（不实际写入数据）

        Args:
            task: ETL任务实例

        Returns:
            执行计划和预估信息
        """
        if task.executor_type != 'datax':
            raise ValueError('仅支持DataX执行器')

        # 验证配置
        is_valid, error_msg, config = self.validate_datax_config(task)

        if not is_valid:
            raise ValueError(f'配置验证失败: {error_msg}')

        # 返回执行计划
        return {
            'message': '模拟执行成功',
            'executionPlan': {
                'taskName': task.task_name,
                'taskCode': task.task_code,
                'executorType': 'DataX',
                'sourceDatasource': task.source_datasource.name,
                'targetDatasource': task.target_datasource.name,
                'sourceTable': task.source_table.table_name if task.source_table else None,
                'targetTable': task.target_table,
                'executionDate': datetime.now().strftime('%Y%m%d'),
                'estimatedTime': '根据数据量预估',
            },
            'config': config
        }
