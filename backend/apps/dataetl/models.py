"""
<<<<<<< HEAD
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
        help_text='源表信息',
        null=True,
        blank=True
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

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='watermarks',
        verbose_name='ETL任务',
        help_text='关联的ETL任务'
    )
    increment_field = models.CharField(
        max_length=64,
        verbose_name='增量字段',
        help_text='用于增量抽取的字段名'
    )
    increment_type = models.CharField(
        max_length=20,
        choices=INCREMENT_TYPE_CHOICES,
        default='timestamp',
        verbose_name='增量类型',
        help_text='增量策略类型'
    )
    watermark_value = models.CharField(
        max_length=255,
        verbose_name='水印值',
        help_text='当前水印值（上次抽取的最大值）'
    )
    execution_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='执行ID',
        help_text='关联的执行ID'
    )

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
=======
数据集成/ETL模块 - 简化版模型设计
基于场景驱动的方式，简化用户操作
"""
from django.db import models
from apps.system.models import BaseModel


class ETLTask(BaseModel):
    """ETL任务主表 - 场景驱动设计"""

    SCENARIO_CHOICES = (
        ('biz_to_stg', '业务库 → STG层'),
        ('stg_to_ods', 'STG层 → ODS层'),
        ('warehouse_transform', '数仓层计算转换'),
        ('warehouse_to_biz', '数仓层 → 业务库'),
        ('db_to_db', '数据库互相同步'),
    )

    STATUS_CHOICES = (
        ('0', '正常'),
        ('1', '停用'),
    )

    EXECUTOR_CHOICES = (
        ('datax', 'DataX执行器'),
        ('spark_sql', 'Spark SQL执行器'),
    )

    SYNC_MODE_CHOICES = (
        ('full', '全量同步'),
        ('incremental', '增量同步'),
    )

    SCHEDULE_TYPE_CHOICES = (
        ('manual', '手动执行'),
        ('scheduled', '定时执行'),
    )

    # 执行方式（新的字段，用于区分手动/调度执行）
    EXECUTION_MODE_CHOICES = (
        ('manual', '手动执行'),
        ('scheduled', '定时执行'),
    )

    # ========== 基础信息 ==========
    name = models.CharField(max_length=255, verbose_name='任务名称', unique=True)
    scenario = models.CharField(
        max_length=30,
        choices=SCENARIO_CHOICES,
        verbose_name='场景类型',
        help_text='决定任务的默认配置和执行方式'
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0', verbose_name='状态')
    execution_mode = models.CharField(
        max_length=20,
        choices=EXECUTION_MODE_CHOICES,
        default='manual',
        verbose_name='执行方式',
        help_text='手动执行或定时执行'
    )
    remark = models.TextField(blank=True, default='', verbose_name='备注')

    # ========== 数据源配置 ==========
    source_datasource = models.ForeignKey(
        'datasource.DataSource',
        on_delete=models.CASCADE,
        related_name='etl_source_tasks',
        verbose_name='源数据源',
        null=True,
        blank=True,
        help_text='源数据源ID'
    )
    source_table = models.CharField(max_length=255, blank=True, default='', verbose_name='源表名')
    source_database = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name='源数据库名',
        help_text='某些数据源需要指定数据库'
    )
    source_filter = models.TextField(
        blank=True,
        default='',
        verbose_name='过滤条件',
        help_text='WHERE条件，如: status = 1'
    )

    target_datasource = models.ForeignKey(
        'datasource.DataSource',
        on_delete=models.CASCADE,
        related_name='etl_target_tasks',
        verbose_name='目标数据源',
        null=True,
        blank=True,
        help_text='目标数据源ID，为空表示Hive'
    )
    target_table = models.CharField(max_length=255, blank=True, default='', verbose_name='目标表名')
    target_database = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name='目标数据库名',
        help_text='目标数据库名或schema'
    )
    target_layer = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='目标层级',
        help_text='数仓层级: stg/ods/dwd/dws/ads'
    )

    # ========== 同步配置 ==========
    sync_mode = models.CharField(
        max_length=20,
        choices=SYNC_MODE_CHOICES,
        default='full',
        verbose_name='同步方式'
    )
    incremental_field = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name='增量字段',
        help_text='增量同步时使用的时间戳或ID字段'
    )

    # ========== 字段映射 ==========
    field_mappings = models.JSONField(
        default=list,
        blank=True,
        verbose_name='字段映射',
        help_text='格式: [{"source": "id", "target": "user_id"}]'
    )

    # ========== SQL脚本（数仓计算场景） ==========
    sql_script = models.TextField(
        blank=True,
        default='',
        verbose_name='SQL脚本',
        help_text='Spark SQL脚本，用于数仓计算场景'
    )
    transform_rules = models.TextField(
        blank=True,
        default='',
        verbose_name='转换规则',
        help_text='数据清洗和转换规则'
    )

    # ========== 执行配置 ==========
    executor_type = models.CharField(
        max_length=20,
        choices=EXECUTOR_CHOICES,
        default='datax',
        verbose_name='执行器类型'
    )
    batch_size = models.IntegerField(default=10000, verbose_name='批处理大小')
    concurrency = models.IntegerField(default=1, verbose_name='并发数')

    # ========== 调度配置 ==========
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        default='manual',
        verbose_name='执行方式'
    )
    schedule_cron = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Cron表达式',
        help_text='定时执行的cron表达式'
    )

    # ========== 高级配置（JSON格式） ==========
    advanced_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='高级配置',
        help_text='存储扩展配置，如分区信息、写入模式等'
    )

    # ========== 任务依赖 ==========
    depends_on_tasks = models.ManyToManyField(
        'self',
        through='ETLTaskDependency',
        through_fields=('successor', 'predecessor'),
        symmetrical=False,
        related_name='dependent_tasks',
        blank=True,
        verbose_name='依赖任务',
        help_text='此任务依赖的其他任务（必须先完成依赖任务才能执行此任务）'
    )

    class Meta:
        db_table = 'etl_task'
        verbose_name = 'ETL任务'
        verbose_name_plural = 'ETL任务'
        indexes = [
            models.Index(fields=['scenario']),
            models.Index(fields=['status']),
            models.Index(fields=['schedule_type']),
            models.Index(fields=['-create_time']),
        ]

    def __str__(self):
        return f"{self.get_scenario_display()} - {self.name}"


class ETLExecution(BaseModel):
    """
    ETL任务执行记录
    ETL特定的执行详情，链接到通用的TaskExecution
    """

    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )

    # 链接到通用的TaskExecution
    execution = models.OneToOneField(
        'datataskmonitor.TaskExecution',
        on_delete=models.CASCADE,
        related_name='etl_details',
        verbose_name='通用执行记录',
        null=True,  # 暂时允许为空以便迁移
        blank=True
    )
>>>>>>> origin/dev

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
<<<<<<< HEAD
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
=======
        related_name='executions',
        verbose_name='任务'
    )

    # ETL特定的统计信息（通用统计已移至TaskExecution）
    rows_read = models.BigIntegerField(default=0, verbose_name='源表行数')
    rows_written = models.BigIntegerField(default=0, verbose_name='目标表行数')
    rows_failed = models.IntegerField(default=0, verbose_name='拒绝行数')

    # 保留旧字段用于向后兼容（新数据应使用TaskExecution中的对应字段）
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(default=0, verbose_name='执行时长(秒)')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')

    # 当前阶段
    current_stage = models.CharField(max_length=255, blank=True, default='', verbose_name='当前阶段')

    # 执行日志（保留用于向后兼容，新日志应使用TaskExecutionLog）
    logs = models.JSONField(default=list, blank=True, verbose_name='执行日志')

    # 错误信息
    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')

    # 执行参数快照（保存任务执行时的配置）
    execution_snapshot = models.JSONField(default=dict, blank=True, verbose_name='执行参数快照')

    class Meta:
        db_table = 'etl_execution'
        verbose_name = 'ETL执行记录'
        verbose_name_plural = 'ETL执行记录'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['task', '-create_time']),
            models.Index(fields=['status']),
            models.Index(fields=['-create_time']),
        ]

    def __str__(self):
        return f"{self.task.name} - {self.get_status_display()}"

    @property
    def is_running(self):
        return self.status == 'running'


class ETLTaskDependency(BaseModel):
    """
    ETL任务依赖关系
    定义任务执行的前后依赖关系：successor 依赖于 predecessor（predecessor 必须先完成）
    """

    predecessor = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='dependency_successors',
        verbose_name='前置任务',
        help_text='需要先完成的任务'
    )
    successor = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='dependency_predecessors',
        verbose_name='后置任务',
        help_text='依赖前置任务的任务'
    )

    class Meta:
        db_table = 'etl_task_dependency'
        verbose_name = 'ETL任务依赖'
        verbose_name_plural = 'ETL任务依赖'
        unique_together = [['predecessor', 'successor']]
        indexes = [
            models.Index(fields=['predecessor']),
            models.Index(fields=['successor']),
        ]

    def __str__(self):
        return f"{self.successor.name} 依赖 {self.predecessor.name}"


class ETLTemplate(BaseModel):
    """ETL任务模板 - 常用配置保存为模板"""

    scenario = models.CharField(
        max_length=30,
        choices=ETLTask.SCENARIO_CHOICES,
        verbose_name='场景类型'
    )
    name = models.CharField(max_length=255, verbose_name='模板名称')
    description = models.TextField(blank=True, default='', verbose_name='模板描述')

    # 模板配置
    template_config = models.JSONField(
        verbose_name='模板配置',
        help_text='存储任务配置的JSON'
    )

    # 使用统计
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')

    is_system = models.BooleanField(
        default=False,
        verbose_name='系统模板',
        help_text='系统预设的模板'
    )

    class Meta:
        db_table = 'etl_template'
        verbose_name = 'ETL模板'
        verbose_name_plural = 'ETL模板'
        indexes = [
            models.Index(fields=['scenario']),
            models.Index(fields=['is_system']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_scenario_display()})"
>>>>>>> origin/dev
