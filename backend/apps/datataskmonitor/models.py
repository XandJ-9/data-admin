from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.system.models import BaseModel

class DataTask(BaseModel):
    TASK_TYPES = (
        ('collection', '数据采集'),
        ('sync', '数据同步'),
        ('calculation', '数据计算'),
        ('storage', '数据存储'),
    )
    SCHEDULE_TYPES = (
        ('cron', 'Cron表达式'),
        ('interval', '固定间隔'),
        ('once', '单次执行'),
    )
    STATUS_CHOICES = (
        ('running', '运行中'),
        ('paused', '暂停'),
        ('failed', '失败'),
        ('success', '成功'),
        ('idle', '空闲'),
    )
    ENABLE_CHOICES = (
        ('0', '启用'),
        ('1', '禁用'),
    )

    source_task = models.OneToOneField(
        'datastudio.DataStudioTask',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ops_task',
        verbose_name='来源任务',
    )
    task_name = models.CharField(max_length=128, verbose_name='任务名称')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, verbose_name='任务类型')
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='cron', verbose_name='调度类型')
    schedule_conf = models.CharField(max_length=256, verbose_name='调度配置', help_text='Cron表达式或间隔时间(秒)')
    enabled = models.CharField(max_length=1, choices=ENABLE_CHOICES, default='0', verbose_name='启用状态')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle', verbose_name='任务状态')
    last_run_time = models.DateTimeField(null=True, blank=True, verbose_name='上次运行时间')
    next_run_time = models.DateTimeField(null=True, blank=True, verbose_name='下次运行时间')
    description = models.TextField(blank=True, verbose_name='描述')

    class Meta:
        db_table = 'dt_task'
        verbose_name = '数据任务'
        verbose_name_plural = '数据任务'

    def __str__(self):
        return self.task_name

class TaskLog(BaseModel):
    STATUS_CHOICES = (
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
    )
    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, related_name='logs', verbose_name='关联任务')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='运行状态')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    message = models.TextField(blank=True, verbose_name='日志信息')

    class Meta:
        db_table = 'dt_task_log'
        verbose_name = '任务日志'
        verbose_name_plural = '任务日志'
        ordering = ['-create_time']

class AlertRule(BaseModel):
    RULE_TYPES = (
        ('failure', '任务失败'),
        ('timeout', '运行超时'),
    )
    CHANNELS = (
        ('email', '邮件'),
        ('sms', '短信'),
        ('wechat', '微信'),
    )

    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_rules', verbose_name='关联任务', help_text='为空则为全局规则')
    rule_name = models.CharField(max_length=128, verbose_name='规则名称')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, verbose_name='规则类型')
    threshold = models.IntegerField(default=0, verbose_name='阈值', help_text='超时时间(秒)或重试次数')
    notification_channels = models.CharField(max_length=128, verbose_name='通知渠道', help_text='逗号分隔')
    receivers = models.TextField(verbose_name='接收人', help_text='逗号分隔')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'dt_alert_rule'
        verbose_name = '报警规则'
        verbose_name_plural = '报警规则'

class AlertRecord(BaseModel):
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('handled', '已处理'),
        ('ignored', '已忽略'),
    )
    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, verbose_name='触发规则')
    task_name = models.CharField(max_length=128, verbose_name='相关任务')
    trigger_time = models.DateTimeField(auto_now_add=True, verbose_name='触发时间')
    content = models.TextField(verbose_name='报警内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    handle_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    handle_note = models.TextField(blank=True, verbose_name='处理备注')

    class Meta:
        db_table = 'dt_alert_record'
        verbose_name = '报警记录'
        verbose_name_plural = '报警记录'
        ordering = ['-trigger_time']


class TaskExecution(BaseModel):
    """
    通用任务执行记录 - 支持所有任务类型（ETL、元数据采集、质量检查等）
    为所有模块提供统一的执行状态跟踪
    """

    TASK_TYPE_CHOICES = (
        ('etl', 'ETL任务'),
        ('metadata_collection', '元数据采集'),
        ('quality_check', '质量检查'),
        ('data_sync', '数据同步'),
        ('calculation', '数据计算'),
    )

    STATUS_CHOICES = (
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )

    # 任务引用（多态关联，通过 task_type + task_id）
    task_type = models.CharField(
        max_length=30,
        choices=TASK_TYPE_CHOICES,
        verbose_name='任务类型',
        db_index=True
    )
    task_id = models.IntegerField(
        verbose_name='任务ID',
        db_index=True,
        help_text='实际任务的ID（如ETLTask.id、MetaCollectionTask.id等）'
    )

    # 时间线
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='执行时长(秒)',
        help_text='自动计算：end_time - start_time'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running',
        verbose_name='状态',
        db_index=True
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='进度百分比',
        help_text='0-100'
    )

    # 结果统计
    rows_read = models.BigIntegerField(null=True, blank=True, verbose_name='读取行数')
    rows_written = models.BigIntegerField(null=True, blank=True, verbose_name='写入行数')
    bytes_processed = models.BigIntegerField(null=True, blank=True, verbose_name='处理字节数')

    # 错误跟踪
    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')
    error_stack = models.TextField(blank=True, default='', verbose_name='错误堆栈')

    # 性能指标
    peak_memory_mb = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        verbose_name='峰值内存(MB)'
    )

    # 详细日志文件路径
    log_file_path = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name='日志文件路径'
    )

    # 执行器信息
    executor_type = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='执行器类型',
        help_text='如: datax, spark_sql'
    )

    # 执行参数快照（可选）
    execution_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='执行参数快照',
        help_text='执行时的任务配置快照'
    )

    class Meta:
        db_table = 'task_execution'
        verbose_name = '任务执行记录'
        verbose_name_plural = '任务执行记录'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['task_type', 'task_id', '-start_time']),
            models.Index(fields=['status', '-start_time']),
            models.Index(fields=['-start_time']),
        ]

    def __str__(self):
        return f"{self.get_task_type_display()} #{self.task_id} - {self.get_status_display()}"

    @property
    def is_running(self):
        return self.status == 'running'

    @property
    def is_successful(self):
        return self.status == 'success'

    @property
    def is_failed(self):
        return self.status == 'failed'

    def save(self, *args, **kwargs):
        # 自动计算执行时长
        if self.end_time and self.start_time:
            from django.utils import timezone
            if isinstance(self.end_time, str):
                from dateutil.parser import parse
                self.end_time = parse(self.end_time)
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
        super().save(*args, **kwargs)


class TaskExecutionLog(BaseModel):
    """
    任务执行日志详细条目 - 支持流式日志
    """

    LOG_LEVEL_CHOICES = (
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
    )

    execution = models.ForeignKey(
        TaskExecution,
        on_delete=models.CASCADE,
        related_name='log_entries',
        verbose_name='执行记录',
        db_index=True
    )
    log_level = models.CharField(
        max_length=10,
        choices=LOG_LEVEL_CHOICES,
        default='INFO',
        verbose_name='日志级别',
        db_index=True
    )
    message = models.TextField(verbose_name='日志消息')
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name='元数据',
        help_text='额外的上下文信息'
    )

    # timestamp 继承自 BaseModel 的 create_time

    class Meta:
        db_table = 'task_execution_log'
        verbose_name = '任务执行日志'
        verbose_name_plural = '任务执行日志'
        ordering = ['create_time']
        indexes = [
            models.Index(fields=['execution', 'create_time']),
            models.Index(fields=['execution', 'log_level']),
        ]

    def __str__(self):
        return f"[{self.log_level}] {self.execution} - {self.message[:50]}"
