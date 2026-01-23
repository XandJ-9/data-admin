"""
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

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
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
