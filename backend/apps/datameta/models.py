from django.db import models
from apps.system.models import BaseModel
from apps.datasource.models import DataSource


class MetaTable(BaseModel):
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=256)
    # 表注释/描述
    comment = models.CharField(max_length=1024, blank=True, default='')
    # 原始数据库名
    database = models.CharField(max_length=256, blank=True, default='')

    class Meta:
        db_table = 'datameta_table'
        unique_together = (('data_source', 'table_name', 'database'),)


class MetaColumn(BaseModel):
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    # 所属表
    table = models.ForeignKey(MetaTable, on_delete=models.CASCADE, related_name='columns',default=None)
    # table_name = models.CharField(max_length=256, blank=True, default='')
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256, blank=True, default='')
    notnull = models.BooleanField(default=False)
    default = models.CharField(max_length=512, blank=True, default='')
    primary = models.BooleanField(default=False)
    # 字段注释/描述
    comment = models.CharField(max_length=1024, blank=True, default='')

    class Meta:
        db_table = 'datameta_column'
        unique_together = (('data_source', 'table', 'name'),)


class MetaCollectionTask(BaseModel):
    """元数据采集任务追踪"""
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '采集中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )

    # 任务标识
    task_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='任务ID')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='collection_tasks')

    # 状态追踪
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True, verbose_name='状态')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    current_table = models.CharField(max_length=256, blank=True, verbose_name='当前处理表')

    # 采集统计
    total_tables = models.IntegerField(default=0, verbose_name='总表数')
    collected_tables = models.IntegerField(default=0, verbose_name='已采集表数')
    failed_tables = models.IntegerField(default=0, verbose_name='失败表数')

    # 配置
    database_name = models.CharField(max_length=256, blank=True, verbose_name='数据库名')

    # 结果
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    # 线程标识
    thread_id = models.CharField(max_length=64, blank=True, verbose_name='线程ID')

    class Meta:
        db_table = 'datameta_collection_task'
        verbose_name = '元数据采集任务'
        verbose_name_plural = '元数据采集任务'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['data_source', 'create_time']),
        ]
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task_id} - {self.get_status_display()}"
