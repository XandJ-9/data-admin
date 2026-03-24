"""
ETL Data Models

This module defines the data models for ETL task management.
"""

from django.db import models
from apps.system.models import BaseModel
from apps.datasource.models import DataSource
from apps.dataasset.models import MetaTable


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
    task_code = models.CharField(max_length=64, unique=True, verbose_name='任务编码', help_text='唯一标识编码')
    description = models.TextField(blank=True, null=True, verbose_name='任务描述', help_text='任务描述信息')

    # Template reference (optional)
    template = models.ForeignKey(
        'ETLTaskTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='关联模板',
        help_text='关联的任务模板'
    )

    # Extended Configuration Fields
    category = models.CharField(max_length=64, blank=True, null=True, verbose_name='分类', help_text='任务分类')
    tags = models.JSONField(default=list, blank=True, verbose_name='标签', help_text='任务标签列表')
    task_config = models.JSONField(default=dict, blank=True, null=True, verbose_name='任务配置', help_text='任务配置（JSON格式）')
    execution_config = models.JSONField(default=dict, blank=True, null=True, verbose_name='执行配置', help_text='执行配置（JSON格式）')
    quality_config = models.JSONField(default=list, blank=True, null=True, verbose_name='质检配置', help_text='质检规则配置列表')

    # ETL Configuration (legacy fields for backward compatibility)
    etl_type = models.CharField(max_length=20, choices=ETL_TYPE_CHOICES, default='full', verbose_name='ETL类型', help_text='ETL任务类型')
    executor_type = models.CharField(max_length=20, choices=EXECUTOR_TYPE_CHOICES, default='mock', verbose_name='执行器类型', help_text='执行器类型')
    execute_strategy = models.CharField(max_length=20, choices=EXECUTE_STRATEGY_CHOICES, default='full', verbose_name='执行策略', help_text='执行策略：全量或增量')

    # Source and Target Configuration
    source_datasource = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='source_etl_tasks', verbose_name='源数据源', help_text='源数据源')
    target_datasource = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='target_etl_tasks', verbose_name='目标数据源', help_text='目标数据源')
    source_table = models.ForeignKey(MetaTable, on_delete=models.PROTECT, related_name='source_etl_tasks', verbose_name='源表', help_text='源表信息', null=True, blank=True)
    target_table = models.CharField(max_length=256, verbose_name='目标表', help_text='目标表名')

    # SQL Configuration
    sql_config = models.TextField(blank=True, null=True, verbose_name='SQL配置', help_text='SQL配置内容，支持采集、转换、加载SQL')

    # Execution Configuration
    executor_params = models.JSONField(blank=True, null=True, verbose_name='执行参数', help_text='执行器参数配置（JSON格式）')

    # Status
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0', verbose_name='状态', help_text='任务状态：0-启用，1-停用')

    # Remark (in addition to BaseModel fields)
    remark = models.CharField(max_length=500, blank=True, null=True, verbose_name='备注')

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

    task = models.ForeignKey(ETLTask, on_delete=models.CASCADE, related_name='versions', verbose_name='ETL任务', help_text='关联的ETL任务')
    version_number = models.IntegerField(verbose_name='版本号', help_text='版本号')
    config_snapshot = models.JSONField(verbose_name='配置快照', help_text='任务配置快照（JSON格式）')
    change_log = models.TextField(verbose_name='变更日志', help_text='版本变更说明')
    is_current = models.BooleanField(default=False, verbose_name='当前版本', help_text='是否为当前使用的版本')

    # Audit Fields
    create_by = models.CharField(max_length=64, blank=True, null=True, verbose_name='创建者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

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

    task = models.ForeignKey(ETLTask, on_delete=models.CASCADE, related_name='field_mappings', verbose_name='ETL任务', help_text='关联的ETL任务')
    source_field_name = models.CharField(max_length=128, verbose_name='源字段名', help_text='源表字段名称')
    target_field_name = models.CharField(max_length=128, verbose_name='目标字段名', help_text='目标表字段名称')
    transform_rule = models.CharField(max_length=512, blank=True, null=True, verbose_name='转换规则', help_text='字段转换规则表达式')
    clean_rule = models.CharField(max_length=512, blank=True, null=True, verbose_name='清洗规则', help_text='数据清洗规则')
    data_type = models.CharField(max_length=64, blank=True, null=True, verbose_name='数据类型', help_text='字段数据类型')
    is_primary_key = models.BooleanField(default=False, verbose_name='是否主键', help_text='是否为主键字段')
    sort_order = models.IntegerField(default=0, verbose_name='排序', help_text='字段排序')

    # Remark (in addition to BaseModel fields)
    remark = models.CharField(max_length=500, blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'dataetl_field_mapping'
        verbose_name = 'ETL字段映射'
        verbose_name_plural = 'ETL字段映射'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.source_field_name} -> {self.target_field_name}"


class ETLWatermark(BaseModel):
    """
    ETL Watermark Model

    Manages watermark values for incremental ETL tasks.
    Tracks the last extracted value for incremental extraction.
    """

    INCREMENT_TYPE_CHOICES = [
        ('timestamp', '时间戳'),
        ('id', '自增ID'),
        ('cdc', '变更数据'),
    ]

    task = models.ForeignKey(ETLTask, on_delete=models.CASCADE, related_name='watermarks', verbose_name='ETL任务', help_text='关联的ETL任务')
    increment_field = models.CharField(max_length=64, verbose_name='增量字段', help_text='用于增量抽取的字段名')
    increment_type = models.CharField(max_length=20, choices=INCREMENT_TYPE_CHOICES, default='timestamp', verbose_name='增量类型', help_text='增量策略类型')
    watermark_value = models.CharField(max_length=255, verbose_name='水印值', help_text='当前水印值（上次抽取的最大值）')
    execution_id = models.CharField(max_length=64, blank=True, null=True, verbose_name='执行ID', help_text='关联的执行ID')

    class Meta:
        db_table = 'dataetl_watermark'
        verbose_name = 'ETL水印'
        verbose_name_plural = 'ETL水印'
        ordering = ['-update_time']

    def __str__(self):
        return f"{self.task.task_code} - {self.increment_field}: {self.watermark_value}"


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

    task = models.ForeignKey(ETLTask, on_delete=models.CASCADE, related_name='execution_logs', verbose_name='ETL任务', help_text='关联的ETL任务')
    execution_id = models.CharField(max_length=64, unique=True, verbose_name='执行ID', help_text='唯一执行标识')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='执行状态', help_text='执行状态')
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPE_CHOICES, default='manual', verbose_name='触发方式', help_text='任务触发方式')

    # Execution Information
    start_time = models.DateTimeField(blank=True, null=True, verbose_name='开始时间', help_text='任务开始执行时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name='结束时间', help_text='任务结束时间')
    duration_seconds = models.IntegerField(blank=True, null=True, verbose_name='执行时长(秒)', help_text='任务执行时长（秒）')

    # Data Statistics
    total_rows = models.IntegerField(blank=True, null=True, verbose_name='总行数', help_text='处理的总行数')
    success_rows = models.IntegerField(blank=True, null=True, verbose_name='成功行数', help_text='成功处理的行数')
    failed_rows = models.IntegerField(blank=True, null=True, verbose_name='失败行数', help_text='失败的行数')

    # Error Information
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息', help_text='执行失败时的错误信息')
    log_file = models.CharField(max_length=512, blank=True, null=True, verbose_name='日志文件', help_text='日志文件路径')

    # Execution Context
    executed_by = models.CharField(max_length=64, blank=True, null=True, verbose_name='执行者', help_text='任务执行者')
    executor_params = models.JSONField(blank=True, null=True, verbose_name='执行参数', help_text='本次执行的参数快照')

    # Audit Fields
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'dataetl_execution_log'
        verbose_name = 'ETL执行日志'
        verbose_name_plural = 'ETL执行日志'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task.task_name} - {self.execution_id} ({self.status})"


class ETLTaskTemplate(BaseModel):
    """
    ETL任务模板
    支持快速创建同类任务
    """

    # ETL Type Choices
    ETL_TYPE_CHOICES = [
        ('extract', 'STG采集'),
        ('transform', 'DWD转换'),
        ('load', 'ODS加载'),
        ('full', '全量ETL'),
    ]

    template_name = models.CharField(max_length=128, verbose_name='模板名称', help_text='任务模板名称')
    template_code = models.CharField(max_length=64, unique=True, verbose_name='模板编码', help_text='唯一标识编码')
    task_type = models.CharField(max_length=20, choices=ETL_TYPE_CHOICES, verbose_name='任务类型', help_text='模板适用的任务类型')
    template_config = models.JSONField(verbose_name='模板配置', help_text='JSON格式的任务配置')
    category = models.CharField(max_length=64, verbose_name='分类', help_text='如：数据同步、SQL转换等')
    tags = models.JSONField(default=list, verbose_name='标签', help_text='标签列表')
    description = models.TextField(blank=True, null=True, verbose_name='模板描述', help_text='模板描述信息')
    is_system = models.BooleanField(default=False, verbose_name='系统模板', help_text='是否为系统预置模板')
    usage_count = models.IntegerField(default=0, verbose_name='使用次数', help_text='模板被使用的次数')

    class Meta:
        db_table = 'dataetl_task_template'
        verbose_name = 'ETL任务模板'
        verbose_name_plural = 'ETL任务模板'
        ordering = ['-is_system', '-usage_count', '-create_time']

    def __str__(self):
        return f"{self.template_name} ({self.template_code})"


class ETLQualityRule(BaseModel):
    """
    数据质量规则
    支持多种质量检查类型
    """

    RULE_TYPE_CHOICES = [
        ('null_check', '空值检查'),
        ('unique_check', '唯一性检查'),
        ('range_check', '范围检查'),
        ('consistency_check', '一致性检查'),
        ('custom_sql', '自定义SQL检查'),
    ]

    ERROR_LEVEL_CHOICES = [
        ('warning', '警告'),
        ('error', '错误'),
    ]

    rule_name = models.CharField(max_length=128, verbose_name='规则名称', help_text='质检规则名称')
    rule_code = models.CharField(max_length=64, unique=True, verbose_name='规则编码', help_text='唯一标识编码')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, verbose_name='规则类型', help_text='质检规则类型')
    table = models.ForeignKey(MetaTable, on_delete=models.CASCADE, related_name='quality_rules', verbose_name='关联表', help_text='质检目标表')
    field_name = models.CharField(max_length=128, blank=True, null=True, verbose_name='字段名', help_text='质检目标字段名')
    rule_config = models.JSONField(default=dict, verbose_name='规则配置', help_text='规则参数配置（JSON格式）')
    sql_expression = models.TextField(blank=True, null=True, verbose_name='SQL表达式', help_text='自定义SQL检查表达式')
    threshold_min = models.FloatField(null=True, blank=True, verbose_name='最小阈值', help_text='最小阈值（用于范围检查）')
    threshold_max = models.FloatField(null=True, blank=True, verbose_name='最大阈值', help_text='最大阈值（用于范围检查）')
    error_level = models.CharField(max_length=20, choices=ERROR_LEVEL_CHOICES, default='error', verbose_name='错误级别', help_text='质检失败时的错误级别')
    enabled = models.BooleanField(default=True, verbose_name='是否启用', help_text='规则是否启用')
    description = models.TextField(blank=True, null=True, verbose_name='规则描述', help_text='规则描述信息')

    class Meta:
        db_table = 'dataetl_quality_rule'
        verbose_name = 'ETL质检规则'
        verbose_name_plural = 'ETL质检规则'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.rule_name} ({self.rule_code}) - {self.get_rule_type_display()}"


class ETLQualityResult(BaseModel):
    """
    数据质检执行结果
    记录每次质量检查的结果
    """

    STATUS_CHOICES = [
        ('passed', '通过'),
        ('failed', '失败'),
        ('warning', '警告'),
    ]

    rule = models.ForeignKey(ETLQualityRule, on_delete=models.CASCADE, related_name='check_results', verbose_name='质检规则', help_text='关联的质检规则')
    execution_id = models.CharField(max_length=64, verbose_name='执行ID', help_text='关联的ETL任务执行ID')
    task = models.ForeignKey(ETLTask, on_delete=models.CASCADE, related_name='quality_results', verbose_name='ETL任务', help_text='关联的ETL任务')
    check_time = models.DateTimeField(auto_now_add=True, verbose_name='检查时间', help_text='质检执行时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='检查状态', help_text='质检结果状态')
    total_rows = models.IntegerField(default=0, verbose_name='总行数', help_text='检查的总行数')
    error_rows = models.IntegerField(default=0, verbose_name='错误行数', help_text='不符合规则的行数')
    warning_rows = models.IntegerField(default=0, verbose_name='警告行数', help_text='产生警告的行数')
    error_details = models.JSONField(default=list, verbose_name='错误详情', help_text='详细的错误信息列表')
    pass_rate = models.FloatField(default=0.0, verbose_name='通过率', help_text='数据通过率（百分比）')
    check_duration = models.IntegerField(blank=True, null=True, verbose_name='检查耗时(毫秒)', help_text='质检执行耗时')

    class Meta:
        db_table = 'dataetl_quality_result'
        verbose_name = 'ETL质检结果'
        verbose_name_plural = 'ETL质检结果'
        ordering = ['-check_time']
        indexes = [
            models.Index(fields=['execution_id']),
            models.Index(fields=['task']),
        ]

    def __str__(self):
        return f"{self.rule.rule_name} - {self.execution_id} ({self.status})"


class ETLExecutionProgress(BaseModel):
    """
    ETL执行进度
    实时跟踪任务执行进度
    """

    execution = models.OneToOneField(ETLExecutionLog, on_delete=models.CASCADE, related_name='progress', verbose_name='执行记录', help_text='关联的执行日志')
    current_stage = models.CharField(max_length=64, default='initializing', verbose_name='当前阶段', help_text='如：数据抽取、数据转换、数据加载')
    progress_percentage = models.IntegerField(default=0, verbose_name='进度百分比', help_text='执行进度百分比（0-100）')
    processed_rows = models.IntegerField(default=0, verbose_name='已处理行数', help_text='已处理的数据行数')
    total_rows = models.IntegerField(default=0, verbose_name='总行数', help_text='需要处理的总行数')
    speed_rows_per_sec = models.FloatField(default=0.0, verbose_name='处理速度(行/秒)', help_text='当前数据处理速度')
    estimated_remaining_seconds = models.IntegerField(default=0, verbose_name='预计剩余时间(秒)', help_text='预计任务剩余时间')
    checkpoint_data = models.JSONField(blank=True, null=True, verbose_name='检查点数据', help_text='用于断点续传的检查点信息')
    heartbeat_time = models.DateTimeField(auto_now=True, verbose_name='心跳时间', help_text='最后心跳更新时间')

    class Meta:
        db_table = 'dataetl_execution_progress'
        verbose_name = 'ETL执行进度'
        verbose_name_plural = 'ETL执行进度'
        ordering = ['-heartbeat_time']

    def __str__(self):
        return f"{self.execution.execution_id} - {self.progress_percentage}% ({self.current_stage})"


class ETLTaskDependency(models.Model):
    """
    ETL任务依赖关系模型

    管理任务之间的依赖关系，用于任务编排和执行顺序控制
    """

    predecessor = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='successor_dependencies',
        verbose_name='前置任务',
        help_text='被依赖的任务（必须先执行）'
    )
    successor = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='predecessor_dependencies',
        verbose_name='后置任务',
        help_text='依赖前置任务的任务'
    )
    dependency_type = models.CharField(
        max_length=20,
        choices=[
            ('success', '执行成功'),
            ('completion', '执行完成'),
        ],
        default='success',
        verbose_name='依赖类型',
        help_text='依赖类型：success-前置任务必须成功，completion-前置任务完成即可'
    )

    # Audit Fields
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_by = models.CharField(max_length=64, blank=True, null=True, verbose_name='创建者')

    class Meta:
        db_table = 'dataetl_task_dependency'
        verbose_name = 'ETL任务依赖'
        verbose_name_plural = 'ETL任务依赖'
        unique_together = [['predecessor', 'successor']]
        ordering = ['predecessor__task_code', 'successor__task_code']

    def __str__(self):
        return f"{self.successor.task_name} depends on {self.predecessor.task_name}"
