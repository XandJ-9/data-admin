"""
TaskService - ETL任务管理服务

提供任务的创建、验证、模板管理等功能
"""

import logging
from typing import Tuple, List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import ETLTask, ETLTaskTemplate, ETLFieldMapping

logger = logging.getLogger(__name__)


class TaskService:
    """
    ETL任务管理服务
    """

    @staticmethod
    @transaction.atomic
    def create_task_from_template(template_id: int, params: Dict[str, Any]) -> ETLTask:
        """
        从模板创建任务

        Args:
            template_id: 模板ID
            params: 创建参数，包括：
                - task_name: 任务名称
                - task_code: 任务编码
                - config: 自定义配置（会覆盖模板配置）

        Returns:
            创建的ETLTask实例

        Raises:
            ValidationError: 参数验证失败
        """
        try:
            template = ETLTaskTemplate.objects.get(id=template_id)
        except ETLTaskTemplate.DoesNotExist:
            raise ValidationError(f"任务模板不存在: {template_id}")

        # 验证必填参数
        if 'task_name' not in params:
            raise ValidationError("缺少必填参数: task_name")
        if 'task_code' not in params:
            raise ValidationError("缺少必填参数: task_code")

        # 检查task_code唯一性
        if ETLTask.objects.filter(task_code=params['task_code']).exists():
            raise ValidationError(f"任务编码已存在: {params['task_code']}")

        # 合并模板配置和自定义参数
        template_config = template.template_config.copy()
        custom_config = params.get('config', {})

        # 深度合并配置
        task_config = TaskService._deep_merge_dict(template_config, custom_config)

        # 创建任务
        task = ETLTask.objects.create(
            task_name=params['task_name'],
            task_code=params['task_code'],
            description=params.get('description', template.description),
            template=template,
            task_config=task_config,
            execution_config=params.get('execution_config', {}),
            quality_config=params.get('quality_config', []),
            category=template.category,
            tags=params.get('tags', template.tags),
            # 保留旧字段以兼容现有代码
            etl_type=task_config.get('taskType', 'full'),
            executor_type=task_config.get('executorType', 'mock'),
            execute_strategy=task_config.get('executeStrategy', 'full'),
            source_datasource_id=task_config.get('source', {}).get('datasourceId'),
            target_datasource_id=task_config.get('target', {}).get('datasourceId'),
            target_table=task_config.get('target', {}).get('table', ''),
        )

        # 增加模板使用次数
        template.usage_count += 1
        template.save(update_fields=['usage_count'])

        logger.info(f"从模板创建任务: {task.task_name} (模板: {template.template_name})")

        return task

    @staticmethod
    def validate_task_config(task_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证任务配置

        Args:
            task_config: 任务配置字典

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        # 检查必填字段
        required_fields = ['taskType', 'source', 'target']
        for field in required_fields:
            if field not in task_config:
                errors.append(f"缺少必填字段: {field}")

        # 检查taskType
        if 'taskType' in task_config:
            valid_types = ['extract', 'transform', 'load', 'full']
            if task_config['taskType'] not in valid_types:
                errors.append(f"无效的taskType: {task_config['taskType']}，有效值: {valid_types}")

        # 检查executorType
        if 'executorType' in task_config:
            valid_executors = ['mock', 'datax', 'spark_sql', 'python']
            if task_config['executorType'] not in valid_executors:
                errors.append(f"无效的executorType: {task_config['executorType']}，有效值: {valid_executors}")

        # 检查source配置
        if 'source' in task_config:
            source = task_config['source']
            if 'datasourceId' not in source:
                errors.append("source配置缺少datasourceId")

        # 检查target配置
        if 'target' in task_config:
            target = task_config['target']
            if 'datasourceId' not in target:
                errors.append("target配置缺少datasourceId")
            if 'table' not in target and 'tableId' not in target:
                errors.append("target配置缺少table或tableId")

        return len(errors) == 0, errors

    @staticmethod
    def create_field_mapping_batch(task_id: int, mappings: List[Dict[str, Any]]) -> int:
        """
        批量创建字段映射

        Args:
            task_id: 任务ID
            mappings: 字段映射列表

        Returns:
            创建的映射数量

        Raises:
            ValidationError: 参数验证失败
        """
        try:
            task = ETLTask.objects.get(id=task_id)
        except ETLTask.DoesNotExist:
            raise ValidationError(f"任务不存在: {task_id}")

        # 删除旧的映射
        ETLFieldMapping.objects.filter(task=task).delete()

        # 批量创建新映射
        field_mappings = []
        for idx, mapping_data in enumerate(mappings):
            field_mappings.append(
                ETLFieldMapping(
                    task=task,
                    source_field_name=mapping_data.get('source_field_name', ''),
                    target_field_name=mapping_data.get('target_field_name', ''),
                    transform_rule=mapping_data.get('transform_rule', ''),
                    clean_rule=mapping_data.get('clean_rule', ''),
                    data_type=mapping_data.get('data_type', ''),
                    is_primary_key=mapping_data.get('is_primary_key', False),
                    sort_order=idx,
                    remark=mapping_data.get('remark', ''),
                )
            )

        ETLFieldMapping.objects.bulk_create(field_mappings, batch_size=100)

        logger.info(f"为任务 {task.task_name} 创建了 {len(mappings)} 个字段映射")

        return len(mappings)

    @staticmethod
    def clone_task(task_id: int, new_task_name: str, new_task_code: str) -> ETLTask:
        """
        克隆任务

        Args:
            task_id: 原任务ID
            new_task_name: 新任务名称
            new_task_code: 新任务编码

        Returns:
            克隆的新任务

        Raises:
            ValidationError: 参数验证失败
        """
        try:
            original_task = ETLTask.objects.get(id=task_id)
        except ETLTask.DoesNotExist:
            raise ValidationError(f"任务不存在: {task_id}")

        # 检查task_code唯一性
        if ETLTask.objects.filter(task_code=new_task_code).exists():
            raise ValidationError(f"任务编码已存在: {new_task_code}")

        # 克隆任务
        new_task = ETLTask(
            task_name=new_task_name,
            task_code=new_task_code,
            description=original_task.description,
            template=original_task.template,
            task_config=original_task.task_config,
            execution_config=original_task.execution_config,
            quality_config=original_task.quality_config,
            category=original_task.category,
            tags=original_task.tags,
            # 保留旧字段
            etl_type=original_task.etl_type,
            executor_type=original_task.executor_type,
            execute_strategy=original_task.execute_strategy,
            source_datasource=original_task.source_datasource,
            target_datasource=original_task.target_datasource,
            source_table=original_task.source_table,
            target_table=original_task.target_table,
            sql_config=original_task.sql_config,
            executor_params=original_task.executor_params,
            status='1',  # 新任务默认停用
            remark=f'克隆自任务: {original_task.task_name}',
        )
        new_task.save()

        # 克隆字段映射
        original_mappings = ETLFieldMapping.objects.filter(task=original_task)
        for mapping in original_mappings:
            ETLFieldMapping.objects.create(
                task=new_task,
                source_field_name=mapping.source_field_name,
                target_field_name=mapping.target_field_name,
                transform_rule=mapping.transform_rule,
                clean_rule=mapping.clean_rule,
                data_type=mapping.data_type,
                is_primary_key=mapping.is_primary_key,
                sort_order=mapping.sort_order,
                remark=mapping.remark,
            )

        logger.info(f"克隆任务: {original_task.task_name} -> {new_task_name}")

        return new_task

    @staticmethod
    def _deep_merge_dict(base_dict: Dict, update_dict: Dict) -> Dict:
        """
        深度合并字典

        Args:
            base_dict: 基础字典
            update_dict: 更新字典

        Returns:
            合并后的字典
        """
        result = base_dict.copy()

        for key, value in update_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = TaskService._deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result
