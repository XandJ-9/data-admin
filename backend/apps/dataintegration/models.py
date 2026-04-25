from django.db import models

from apps.datasource.models import DataSource, SourceTableSnapshot
from apps.system.models import BaseModel


class DataIntegrationTask(BaseModel):
    """Phase 2：数据集成任务配置。"""

    LOAD_TYPE_CHOICES = [
        ('full', '全量'),
        ('incremental', '增量'),
    ]
    WRITE_MODE_CHOICES = [
        ('overwrite', '覆盖'),
        ('append', '追加'),
        ('upsert', '更新插入'),
    ]
    EXECUTOR_TYPE_CHOICES = [
        ('mock', '模拟执行器'),
        ('datax', 'DataX执行器'),
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
    ]

    task_name = models.CharField(max_length=128, verbose_name='任务名称')
    task_code = models.CharField(max_length=128, unique=True, verbose_name='任务编码')
    source_datasource = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name='source_integration_tasks',
        verbose_name='源数据源',
    )
    target_datasource = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name='target_integration_tasks',
        verbose_name='目标数据源',
    )
    source_table_snapshot = models.ForeignKey(
        SourceTableSnapshot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='integration_tasks',
        verbose_name='源表快照',
    )
    source_database_name = models.CharField(max_length=256, blank=True, default='', verbose_name='源数据库名')
    source_table_name = models.CharField(max_length=256, blank=True, default='', verbose_name='源表名')
    target_schema_name = models.CharField(max_length=128, blank=True, default='', verbose_name='目标Schema')
    target_table_name = models.CharField(max_length=128, verbose_name='目标表名')
    load_type = models.CharField(max_length=20, choices=LOAD_TYPE_CHOICES, default='full', verbose_name='加载类型')
    write_mode = models.CharField(max_length=20, choices=WRITE_MODE_CHOICES, default='overwrite', verbose_name='写入模式')
    executor_type = models.CharField(max_length=20, choices=EXECUTOR_TYPE_CHOICES, default='mock', verbose_name='执行器类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='manual', verbose_name='调度类型')
    cron_expression = models.CharField(max_length=64, blank=True, default='', verbose_name='Cron表达式')
    task_config = models.JSONField(default=dict, blank=True, verbose_name='任务配置')
    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='负责人')
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'dataintegration_task'
        verbose_name = '数据集成任务'
        verbose_name_plural = '数据集成任务'
        ordering = ['-update_time', '-id']
        indexes = [
            models.Index(fields=['del_flag', 'status']),
            models.Index(fields=['source_datasource']),
            models.Index(fields=['target_datasource']),
            models.Index(fields=['executor_type']),
        ]

    def __str__(self):
        return f'{self.task_name} ({self.task_code})'
