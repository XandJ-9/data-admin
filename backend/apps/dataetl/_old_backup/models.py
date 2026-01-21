from django.db import models
from apps.system.models import BaseModel


class IntegrationTask(BaseModel):
    """数据集成/ETL任务"""
    TASK_TYPE_CHOICES = (
        ('dbToDb', '数据库同步'),
        ('dbToHive', '数据库同步到Hive'),
        ('hiveToDb', 'Hive同步到数据库'),
    )

    LAYER_CHOICES = (
        ('stg', 'STG缓冲层'),
        ('ods', 'ODS原始层'),
        ('dwd', 'DWD明细层'),
        ('dws', 'DWS汇总层'),
        ('ads', 'ADS应用层'),
    )

    EXECUTOR_CHOICES = (
        ('datax', 'DataX执行器'),
        ('spark_sql', 'Spark SQL执行器'),
        ('python', 'Python脚本'),
    )

    INCREMENTAL_CHOICES = (
        ('full', '全量'),
        ('incremental_addtime', '按新增时间'),
        ('incremental_updatetime', '按更新时间'),
        ('incremental_id', '按自增ID'),
    )

    # 基础字段
    name = models.CharField(max_length=255, verbose_name='任务名称')
    type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')

    # 【新增】目标层级和执行器类型
    target_layer = models.CharField(max_length=10, choices=LAYER_CHOICES, blank=True, default='',
                                   verbose_name='目标层级', help_text='数据仓库层级')
    executor_type = models.CharField(max_length=20, choices=EXECUTOR_CHOICES, default='datax',
                                    verbose_name='执行器类型')

    # 【新增】数据源配置
    source_datasource = models.ForeignKey(
        'datasource.DataSource',
        on_delete=models.CASCADE,
        related_name='etl_source_tasks',
        verbose_name='源数据源',
        null=True,
        blank=True
    )
    source_table = models.CharField(max_length=256, blank=True, default='',
                                   verbose_name='源表名')
    source_filter = models.TextField(blank=True, default='',
                                    verbose_name='源表过滤条件', help_text='WHERE条件，如: update_time > "2026-01-01"')

    # 【新增】【5000+租户优化】多库采集配置
    is_multi_db_task = models.BooleanField(default=False, verbose_name='是否多库采集任务',
                                          help_text='同一数据源下的多个租户库合并采集')
    source_databases = models.JSONField(default=list, blank=True,
                                       verbose_name='源数据库列表',
                                       help_text='多库采集时使用，如: ["tenant_db_001", "tenant_db_002"]')
    tenant_id_field = models.CharField(max_length=128, blank=True, default='',
                                      verbose_name='租户ID字段',
                                      help_text='用于标识租户的字段名，为空则从数据库名提取')

    # 【新增】目标配置
    target_datasource = models.ForeignKey(
        'datasource.DataSource',
        on_delete=models.CASCADE,
        related_name='etl_target_tasks',
        verbose_name='目标数据源',
        null=True,
        blank=True
    )
    target_table = models.CharField(max_length=256, blank=True, default='',
                                   verbose_name='目标表名')
    target_partition = models.JSONField(default=dict, blank=True,
                                       verbose_name='分区配置',
                                       help_text='如: {"type": "date", "field": "ds", "format": "yyyyMMdd"}')

    # 【新增】增量策略
    incremental_strategy = models.CharField(max_length=30, choices=INCREMENTAL_CHOICES,
                                           default='full', verbose_name='增量策略')
    incremental_field = models.CharField(max_length=128, blank=True, default='',
                                        verbose_name='增量字段')

    # 【新增】字段映射
    field_mapping = models.JSONField(default=list, blank=True,
                                     verbose_name='字段映射',
                                     help_text='[{"source":"id","target":"user_id","type":"int"}]')

    # 【新增】执行配置
    batch_size = models.IntegerField(default=10000, verbose_name='批处理大小')
    concurrency = models.IntegerField(default=1, verbose_name='并发度')

    # 【新增】预处理/后处理SQL
    pre_sql = models.TextField(blank=True, default='', verbose_name='执行前SQL')
    post_sql = models.TextField(blank=True, default='', verbose_name='执行后SQL')

    # 【新增】DataX配置扩展
    datax_config = models.JSONField(default=dict, blank=True,
                                    verbose_name='DataX配置扩展')

    # 保留原有字段（向后兼容）
    schedule = models.JSONField(default=dict, verbose_name='调度配置')
    detail = models.JSONField(default=dict, verbose_name='任务详情')
    status = models.CharField(max_length=1, choices=[('0', '正常'), ('1', '停用')], default='0', verbose_name='状态')
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'dataetl_task'
        verbose_name = '数据集成任务'
        verbose_name_plural = '数据集成任务'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['type']),
            models.Index(fields=['target_layer']),
            models.Index(fields=['executor_type']),
            models.Index(fields=['status']),
            models.Index(fields=['del_flag']),
            models.Index(fields=['source_datasource']),
            models.Index(fields=['target_datasource']),
        ]

    def __str__(self):
        return f"{self.name}({self.type})"


class IntegrationTaskVersion(BaseModel):
    """ETL任务版本管理"""
    task = models.ForeignKey(
        IntegrationTask,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='关联任务'
    )
    version = models.CharField(max_length=20, verbose_name='版本号', help_text='如: v1.0.0')
    config_snapshot = models.JSONField(verbose_name='配置快照', help_text='完整任务配置的JSON快照')
    change_log = models.TextField(verbose_name='变更日志')
    is_active = models.BooleanField(default=False, verbose_name='是否当前激活版本')

    class Meta:
        db_table = 'dataetl_task_version'
        verbose_name = 'ETL任务版本'
        verbose_name_plural = 'ETL任务版本'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['task', 'version']),
            models.Index(fields=['is_active']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.task.name} - {self.version}"


class TaskExecutionLog(BaseModel):
    """任务执行详细日志"""
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )

    task = models.ForeignKey(
        IntegrationTask,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='关联任务'
    )
    version = models.ForeignKey(
        IntegrationTaskVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='任务版本'
    )
    execution_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='执行ID')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name='耗时(秒)')

    # 统计信息
    rows_read = models.BigIntegerField(default=0, verbose_name='读取行数')
    rows_written = models.BigIntegerField(default=0, verbose_name='写入行数')
    rows_error = models.BigIntegerField(default=0, verbose_name='错误行数')
    bytes_transferred = models.BigIntegerField(default=0, verbose_name='传输字节数')

    # 日志
    log_path = models.CharField(max_length=512, blank=True, default='', verbose_name='日志文件路径')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    stack_trace = models.TextField(blank=True, verbose_name='错误堆栈')

    # 执行上下文
    execution_params = models.JSONField(default=dict, verbose_name='执行参数')
    triggered_by = models.CharField(max_length=64, blank=True, verbose_name='触发方式')

    class Meta:
        db_table = 'dataetl_execution_log'
        verbose_name = '任务执行日志'
        verbose_name_plural = '任务执行日志'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['task', '-create_time']),
            models.Index(fields=['status']),
            models.Index(fields=['execution_id']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.task.name} - {self.execution_id}"


class DataLineage(BaseModel):
    """数据血缘关系"""
    LINEAGE_TYPE = (
        ('table', '表级血缘'),
        ('field', '字段级血缘'),
    )

    source_task = models.ForeignKey(
        IntegrationTask,
        on_delete=models.CASCADE,
        related_name='lineage_outputs',
        verbose_name='源任务'
    )
    lineage_type = models.CharField(max_length=10, choices=LINEAGE_TYPE, verbose_name='血缘类型')

    # 源端信息
    source_datasource = models.ForeignKey(
        'datasource.DataSource',
        on_delete=models.CASCADE,
        related_name='lineage_sources',
        verbose_name='源数据源'
    )
    source_table = models.CharField(max_length=256, verbose_name='源表')
    source_field = models.CharField(max_length=256, blank=True, verbose_name='源字段',
                                   help_text='字段级血缘时必填')

    # 目标端信息
    target_datasource = models.ForeignKey(
        'datasource.DataSource',
        on_delete=models.CASCADE,
        related_name='lineage_targets',
        verbose_name='目标数据源'
    )
    target_table = models.CharField(max_length=256, verbose_name='目标表')
    target_field = models.CharField(max_length=256, blank=True, verbose_name='目标字段',
                                   help_text='字段级血缘时必填')

    # 转换信息
    transform_rule = models.TextField(blank=True, verbose_name='转换规则说明')

    class Meta:
        db_table = 'dataetl_lineage'
        verbose_name = '数据血缘'
        verbose_name_plural = '数据血缘'
        unique_together = [('source_task', 'lineage_type', 'source_table', 'target_table')]
        indexes = [
            models.Index(fields=['source_datasource', 'source_table']),
            models.Index(fields=['target_datasource', 'target_table']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        if self.lineage_type == 'table':
            return f"{self.source_table} -> {self.target_table}"
        else:
            return f"{self.source_table}.{self.source_field} -> {self.target_table}.{self.target_field}"


class MultiTenantAggregationTask(BaseModel):
    """多租户聚合任务配置"""

    # 汇聚所有租户STG数据到ODS
    ods_task = models.OneToOneField(
        IntegrationTask,
        on_delete=models.CASCADE,
        related_name='aggregation_config',
        verbose_name='ODS聚合任务'
    )

    # 参与聚合的租户STG任务
    stg_tasks = models.ManyToManyField(
        IntegrationTask,
        related_name='aggregated_by',
        verbose_name='STG任务列表'
    )

    # 聚合配置
    deduplication_fields = models.JSONField(
        default=list,
        verbose_name='去重字段列表',
        help_text='如: ["user_id", "tenant_id"]'
    )

    # 数据标准化规则
    standardization_rules = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='标准化规则'
    )

    class Meta:
        db_table = 'dataetl_multitenant_agg'
        verbose_name = '多租户聚合配置'
        verbose_name_plural = '多租户聚合配置'
        indexes = [
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.ods_task.name} - 聚合配置"

