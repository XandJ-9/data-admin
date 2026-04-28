from django.db import models

from apps.system.models import BaseModel


class Task(BaseModel):
    """平台任务镜像。

    负责承载各业务模块正式任务定义映射后的平台公共字段，
    供统一调度、运维和实例管理使用。
    """

    TASK_TYPE_CHOICES = [
        ('DATA_SYNC', '数据同步'),
        ('SQL_COMPUTE', 'SQL计算'),
        ('ASSET_COLLECTION', '资产采集'),
    ]
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '启用'),
        ('paused', '暂停'),
        ('archived', '归档'),
    ]
    SCHEDULE_TYPE_CHOICES = [
        ('manual', '手动触发'),
        ('cron', '定时调度'),
        ('dependency', '依赖触发'),
    ]

    task_name = models.CharField(max_length=128, verbose_name='任务名称')
    task_code = models.CharField(max_length=128, unique=True, verbose_name='任务编码')
    task_type = models.CharField(max_length=32, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='任务状态',
    )
    source_module = models.CharField(max_length=64, blank=True, default='', verbose_name='来源模块')
    source_record_id = models.BigIntegerField(null=True, blank=True, verbose_name='来源记录ID')
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        default='manual',
        verbose_name='调度类型',
    )
    cron_expression = models.CharField(max_length=64, blank=True, default='', verbose_name='Cron表达式')
    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='负责人')
    task_config = models.JSONField(default=dict, blank=True, verbose_name='任务配置')
    last_instance_status = models.CharField(max_length=20, blank=True, default='', verbose_name='最近实例状态')
    last_instance_at = models.DateTimeField(null=True, blank=True, verbose_name='最近运行时间')
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'datatask_task'
        verbose_name = '统一任务'
        verbose_name_plural = '统一任务'
        ordering = ['-update_time', '-id']
        indexes = [
            models.Index(fields=['del_flag', 'task_type']),
            models.Index(fields=['del_flag', 'status']),
            models.Index(fields=['source_module', 'source_record_id']),
            models.Index(fields=['owner']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['source_module', 'source_record_id'],
                condition=(
                    models.Q(del_flag='0')
                    & models.Q(source_module__gt='')
                    & models.Q(source_record_id__isnull=False)
                ),
                name='datatask_unique_live_source_task',
            ),
        ]

    def __str__(self):
        return f'{self.task_name} ({self.task_code})'


class TaskDependency(BaseModel):
    """平台任务依赖关系。

    用于描述上游任务成功后如何触发下游任务，是依赖调度的拓扑基础。
    """

    TRIGGER_CONDITION_CHOICES = [
        ('SUCCESS', '上游成功'),
    ]

    upstream_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='downstream_dependencies',
        verbose_name='上游任务',
    )
    downstream_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='upstream_dependencies',
        verbose_name='下游任务',
    )
    trigger_condition = models.CharField(
        max_length=20,
        choices=TRIGGER_CONDITION_CHOICES,
        default='SUCCESS',
        verbose_name='触发条件',
    )
    lag_seconds = models.PositiveIntegerField(default=0, verbose_name='延迟秒数')
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'datatask_task_dependency'
        verbose_name = '任务依赖'
        verbose_name_plural = '任务依赖'
        ordering = ['upstream_task_id', 'downstream_task_id']
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['upstream_task', 'downstream_task']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['upstream_task', 'downstream_task'],
                condition=models.Q(del_flag='0'),
                name='datatask_unique_live_dependency',
            ),
            models.CheckConstraint(
                check=~models.Q(upstream_task=models.F('downstream_task')),
                name='datatask_dependency_not_self',
            ),
        ]

    def __str__(self):
        return f'{self.upstream_task.task_code} -> {self.downstream_task.task_code}'


class TaskInstance(models.Model):
    """统一任务执行实例。

    负责记录任务每次手动、定时或依赖触发执行的运行时状态、结果摘要和错误信息。
    """

    STATUS_CHOICES = [
        ('pending', '等待执行'),
        ('running', '执行中'),
        ('success', '执行成功'),
        ('failed', '执行失败'),
        ('cancelled', '已取消'),
    ]
    TRIGGER_MODE_CHOICES = [
        ('manual', '手动触发'),
        ('schedule', '定时触发'),
        ('dependency', '依赖触发'),
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name='所属任务',
    )
    instance_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='实例ID')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='实例状态',
    )
    trigger_mode = models.CharField(
        max_length=20,
        choices=TRIGGER_MODE_CHOICES,
        default='manual',
        verbose_name='触发方式',
    )
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='计划触发时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration_seconds = models.FloatField(null=True, blank=True, verbose_name='执行时长(秒)')
    runtime_config = models.JSONField(default=dict, blank=True, verbose_name='运行时配置')
    executor_type = models.CharField(max_length=32, blank=True, default='', verbose_name='执行器类型')
    result_summary = models.JSONField(null=True, blank=True, verbose_name='结果摘要')
    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')
    triggered_by = models.CharField(max_length=64, blank=True, default='', verbose_name='触发者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'datatask_task_instance'
        verbose_name = '任务实例'
        verbose_name_plural = '任务实例'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['task', 'status']),
            models.Index(fields=['trigger_mode']),
            models.Index(fields=['create_time']),
        ]

    def __str__(self):
        return f'{self.task.task_code} - {self.instance_id} ({self.status})'
