"""
ETL Data Models

This module defines the data models for ETL task management.
"""

from django.db import models
from apps.system.models import BaseModel
from apps.dataasset.models import DataSource, MetaTable


class ETLTask(BaseModel):
    """
    ETL Task Model

    Manages ETL task configurations including source/target datasources,
    SQL configurations, and execution parameters.
    """

    # ETL Type Choices
    ETL_TYPE_CHOICES = [
        ('extract', 'STG采集'),
        ('transform', 'DWD转换'),
        ('load', 'ODS加载'),
        ('full', '全量ETL'),
    ]

    # Executor Type Choices
    EXECUTOR_TYPE_CHOICES = [
        ('mock', '模拟执行器'),
        ('datax', 'DataX'),
        ('spark', 'Spark SQL'),
        ('python', 'Python脚本'),
    ]

    # Execute Strategy Choices
    EXECUTE_STRATEGY_CHOICES = [
        ('full', '全量'),
        ('increment', '增量'),
    ]

    # Status Choices
    STATUS_CHOICES = [
        ('0', '启用'),
        ('1', '停用'),
    ]

    # Basic Information
    task_name = models.CharField(max_length=128, verbose_name='任务名称', help_text='ETL任务名称')
    task_code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='任务编码',
        help_text='唯一标识编码'
    )
    description = models.TextField(blank=True, null=True, verbose_name='任务描述', help_text='任务描述信息')

    # ETL Configuration
    etl_type = models.CharField(
        max_length=20,
        choices=ETL_TYPE_CHOICES,
        default='full',
        verbose_name='ETL类型',
        help_text='ETL任务类型'
    )
    executor_type = models.CharField(
        max_length=20,
        choices=EXECUTOR_TYPE_CHOICES,
        default='mock',
        verbose_name='执行器类型',
        help_text='执行器类型'
    )
    execute_strategy = models.CharField(
        max_length=20,
        choices=EXECUTE_STRATEGY_CHOICES,
        default='full',
        verbose_name='执行策略',
        help_text='执行策略：全量或增量'
    )

    # Source and Target Configuration
    source_datasource = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name='source_etl_tasks',
        verbose_name='源数据源',
        help_text='源数据源'
    )
    target_datasource = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name='target_etl_tasks',
        verbose_name='目标数据源',
        help_text='目标数据源'
    )
    source_table = models.ForeignKey(
        MetaTable,
        on_delete=models.PROTECT,
        related_name='source_etl_tasks',
        verbose_name='源表',
        help_text='源表信息'
    )
    target_table = models.CharField(
        max_length=256,
        verbose_name='目标表',
        help_text='目标表名'
    )

    # SQL Configuration
    sql_config = models.TextField(
        blank=True,
        null=True,
        verbose_name='SQL配置',
        help_text='SQL配置内容，支持采集、转换、加载SQL'
    )

    # Execution Configuration
    executor_params = models.JSONField(
        blank=True,
        null=True,
        verbose_name='执行参数',
        help_text='执行器参数配置（JSON格式）'
    )

    # Status
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='0',
        verbose_name='状态',
        help_text='任务状态：0-启用，1-停用'
    )

    # Remark (in addition to BaseModel fields)
    remark = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='备注'
    )

    class Meta:
        db_table = 'dataetl_task'
        verbose_name = 'ETL任务'
        verbose_name_plural = 'ETL任务'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task_name} ({self.task_code})"


class ETLTaskVersion(models.Model):
    """
    ETL Task Version Model

    Manages version history for ETL tasks.
    """

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='ETL任务',
        help_text='关联的ETL任务'
    )
    version_number = models.IntegerField(
        verbose_name='版本号',
        help_text='版本号'
    )
    config_snapshot = models.JSONField(
        verbose_name='配置快照',
        help_text='任务配置快照（JSON格式）'
    )
    change_log = models.TextField(
        verbose_name='变更日志',
        help_text='版本变更说明'
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name='当前版本',
        help_text='是否为当前使用的版本'
    )

    # Audit Fields
    create_by = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='创建者'
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        db_table = 'dataetl_task_version'
        verbose_name = 'ETL任务版本'
        verbose_name_plural = 'ETL任务版本'
        ordering = ['-version_number']
        unique_together = [['task', 'version_number']]

    def __str__(self):
        return f"{self.task.task_name} - v{self.version_number}"


class ETLFieldMapping(BaseModel):
    """
    ETL Field Mapping Model

    Manages field mappings between source and target tables.
    """

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='field_mappings',
        verbose_name='ETL任务',
        help_text='关联的ETL任务'
    )
    source_field_name = models.CharField(
        max_length=128,
        verbose_name='源字段名',
        help_text='源表字段名称'
    )
    target_field_name = models.CharField(
        max_length=128,
        verbose_name='目标字段名',
        help_text='目标表字段名称'
    )
    transform_rule = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='转换规则',
        help_text='字段转换规则表达式'
    )
    clean_rule = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='清洗规则',
        help_text='数据清洗规则'
    )
    data_type = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='数据类型',
        help_text='字段数据类型'
    )
    is_primary_key = models.BooleanField(
        default=False,
        verbose_name='是否主键',
        help_text='是否为主键字段'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='排序',
        help_text='字段排序'
    )

    # Remark (in addition to BaseModel fields)
    remark = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='备注'
    )

    class Meta:
        db_table = 'dataetl_field_mapping'
        verbose_name = 'ETL字段映射'
        verbose_name_plural = 'ETL字段映射'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.source_field_name} -> {self.target_field_name}"


class ETLExecutionLog(models.Model):
    """
    ETL Execution Log Model

    Records execution history and results of ETL tasks.
    """

    # Execution Status Choices
    STATUS_CHOICES = [
        ('pending', '等待执行'),
        ('running', '执行中'),
        ('success', '执行成功'),
        ('failed', '执行失败'),
        ('cancelled', '已取消'),
    ]

    # Trigger Type Choices
    TRIGGER_TYPE_CHOICES = [
        ('manual', '手动触发'),
        ('schedule', '调度触发'),
        ('api', 'API触发'),
    ]

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='execution_logs',
        verbose_name='ETL任务',
        help_text='关联的ETL任务'
    )
    execution_id = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='执行ID',
        help_text='唯一执行标识'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='执行状态',
        help_text='执行状态'
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPE_CHOICES,
        default='manual',
        verbose_name='触发方式',
        help_text='任务触发方式'
    )

    # Execution Information
    start_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='开始时间',
        help_text='任务开始执行时间'
    )
    end_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='结束时间',
        help_text='任务结束时间'
    )
    duration_seconds = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='执行时长(秒)',
        help_text='任务执行时长（秒）'
    )

    # Data Statistics
    total_rows = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='总行数',
        help_text='处理的总行数'
    )
    success_rows = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='成功行数',
        help_text='成功处理的行数'
    )
    failed_rows = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='失败行数',
        help_text='失败的行数'
    )

    # Error Information
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='错误信息',
        help_text='执行失败时的错误信息'
    )
    log_file = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='日志文件',
        help_text='日志文件路径'
    )

    # Execution Context
    executed_by = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='执行者',
        help_text='任务执行者'
    )
    executor_params = models.JSONField(
        blank=True,
        null=True,
        verbose_name='执行参数',
        help_text='本次执行的参数快照'
    )

    # Audit Fields
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        db_table = 'dataetl_execution_log'
        verbose_name = 'ETL执行日志'
        verbose_name_plural = 'ETL执行日志'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task.task_name} - {self.execution_id} ({self.status})"
