from django.db import models
from apps.system.models import BaseModel
from apps.datasource.models import DataSource


class MetaTable(BaseModel):
    """元数据表"""
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='meta_tables')
    table_name = models.CharField(max_length=256, verbose_name='表名')
    # 表注释/描述
    comment = models.CharField(max_length=1024, blank=True, default='', verbose_name='表注释')
    # 原始数据库名
    database = models.CharField(max_length=256, blank=True, default='', verbose_name='数据库名')

    class Meta:
        db_table = 'dataasset_meta_table'
        verbose_name = '元数据表'
        verbose_name_plural = '元数据表'
        unique_together = (('data_source', 'table_name', 'database'),)
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['data_source', 'table_name']),
        ]

    def __str__(self):
        return f"{self.data_source.name}.{self.table_name}"


class MetaColumn(BaseModel):
    """元数据字段"""
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='meta_columns')
    # 所属表
    table = models.ForeignKey(MetaTable, on_delete=models.CASCADE, related_name='columns')
    order = models.IntegerField(default=0, verbose_name='字段顺序')
    name = models.CharField(max_length=256, verbose_name='字段名')
    type = models.CharField(max_length=256, blank=True, default='', verbose_name='字段类型')
    notnull = models.BooleanField(default=False, verbose_name='是否可空')
    default = models.CharField(max_length=512, blank=True, default='', verbose_name='默认值')
    primary = models.BooleanField(default=False, verbose_name='是否主键')
    # 字段注释/描述
    comment = models.CharField(max_length=1024, blank=True, default='', verbose_name='字段注释')

    class Meta:
        db_table = 'dataasset_meta_column'
        verbose_name = '元数据字段'
        verbose_name_plural = '元数据字段'
        unique_together = (('data_source', 'table', 'name'),)
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['table', 'order']),
        ]

    def __str__(self):
        return f"{self.table.table_name}.{self.name}"


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
        db_table = 'dataasset_collection_task'
        verbose_name = '元数据采集任务'
        verbose_name_plural = '元数据采集任务'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['data_source', 'create_time']),
        ]
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task_id} - {self.get_status_display()}"


class TableLineage(BaseModel):
    """表血缘关系"""
    LINEAGE_TYPE_CHOICES = (
        ('upstream', '上游'),
        ('downstream', '下游'),
    )

    source_table = models.ForeignKey(
        MetaTable,
        on_delete=models.CASCADE,
        related_name='downstream_lineages',
        verbose_name='源表'
    )
    target_table = models.ForeignKey(
        MetaTable,
        on_delete=models.CASCADE,
        related_name='upstream_lineages',
        verbose_name='目标表'
    )
    lineage_type = models.CharField(
        max_length=20,
        choices=LINEAGE_TYPE_CHOICES,
        default='upstream',
        verbose_name='血缘类型'
    )
    description = models.CharField(max_length=1024, blank=True, default='', verbose_name='描述')

    class Meta:
        db_table = 'dataasset_table_lineage'
        verbose_name = '表血缘关系'
        verbose_name_plural = '表血缘关系'
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['source_table', 'target_table']),
            models.Index(fields=['lineage_type']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(source_table=models.F('target_table')),
                name='source_target_not_same'
            )
        ]

    def __str__(self):
        return f"{self.source_table.table_name} -> {self.target_table.table_name} ({self.get_lineage_type_display()})"
