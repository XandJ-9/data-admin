from django.db import models
from django.db.models import Q

from apps.system.models import BaseModel


class DataSource(BaseModel):
    """Phase 1：连接与发现阶段的数据源定义。"""

    name = models.CharField(max_length=64, verbose_name='数据源名称')
    db_type = models.CharField(max_length=20, verbose_name='数据库类型')
    host = models.CharField(max_length=128, blank=True, default='', verbose_name='主机')
    port = models.IntegerField(default=0, verbose_name='端口')
    db_name = models.CharField(max_length=256, blank=True, default='', verbose_name='数据库名')
    username = models.CharField(max_length=128, blank=True, default='', verbose_name='用户名')
    password = models.CharField(max_length=256, blank=True, default='', verbose_name='密码')
    params = models.TextField(blank=True, default='', verbose_name='连接参数(JSON 或 KV)')
    status = models.CharField(
        max_length=1,
        choices=[('0', '正常'), ('1', '停用')],
        default='0',
        verbose_name='状态',
    )
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')
    connectivity_status = models.CharField(
        max_length=16,
        choices=[('unknown', '未测试'), ('success', '连通'), ('failed', '异常')],
        default='unknown',
        verbose_name='最近连通性状态',
    )
    connectivity_message = models.CharField(max_length=255, blank=True, default='', verbose_name='最近连通性说明')
    connectivity_tested_at = models.DateTimeField(blank=True, null=True, verbose_name='最近连通性测试时间')

    class Meta:
        db_table = 'dataasset_datasource'
        verbose_name = '数据源'
        verbose_name_plural = '数据源'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['db_type']),
            models.Index(fields=['status']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f'{self.name}({self.db_type})'


class SourceTableSnapshot(BaseModel):
    """源端采集后的原始表快照。"""

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='table_snapshots', verbose_name='数据源')
    database_name = models.CharField(max_length=256, blank=True, default='', verbose_name='数据库名')
    table_name = models.CharField(max_length=256, verbose_name='表名')
    table_type = models.CharField(max_length=64, blank=True, default='TABLE', verbose_name='表类型')
    table_comment = models.CharField(max_length=500, blank=True, default='', verbose_name='表注释')
    source_create_time = models.CharField(max_length=64, blank=True, default='', verbose_name='源创建时间')
    source_update_time = models.CharField(max_length=64, blank=True, default='', verbose_name='源更新时间')
    raw_payload = models.JSONField(default=dict, blank=True, verbose_name='原始载荷')

    class Meta:
        db_table = 'datasource_source_table'
        verbose_name = '源表快照'
        verbose_name_plural = '源表快照'
        indexes = [
            models.Index(fields=['data_source', 'database_name']),
            models.Index(fields=['data_source', 'table_name']),
            models.Index(fields=['del_flag']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['data_source', 'database_name', 'table_name', 'del_flag'],
                name='uniq_datasource_source_table_active',
            )
        ]

    def __str__(self):
        return f'{self.database_name}.{self.table_name}' if self.database_name else self.table_name


class SourceColumnSnapshot(BaseModel):
    """源端采集后的原始字段快照。"""

    table_snapshot = models.ForeignKey(
        SourceTableSnapshot,
        on_delete=models.CASCADE,
        related_name='column_snapshots',
        verbose_name='表快照',
    )
    column_name = models.CharField(max_length=256, verbose_name='字段名')
    ordinal_position = models.IntegerField(default=0, verbose_name='序号')
    data_type = models.CharField(max_length=128, blank=True, default='', verbose_name='数据类型')
    column_type = models.CharField(max_length=255, blank=True, default='', verbose_name='完整类型')
    is_nullable = models.CharField(max_length=8, blank=True, default='YES', verbose_name='是否可空')
    column_default = models.CharField(max_length=255, blank=True, default='', verbose_name='默认值')
    column_key = models.CharField(max_length=32, blank=True, default='', verbose_name='键类型')
    column_comment = models.CharField(max_length=500, blank=True, default='', verbose_name='字段注释')
    raw_payload = models.JSONField(default=dict, blank=True, verbose_name='原始载荷')

    class Meta:
        db_table = 'datasource_source_column'
        verbose_name = '源字段快照'
        verbose_name_plural = '源字段快照'
        indexes = [
            models.Index(fields=['table_snapshot', 'ordinal_position']),
            models.Index(fields=['table_snapshot', 'column_name']),
            models.Index(fields=['del_flag']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['table_snapshot', 'column_name', 'del_flag'],
                name='uniq_datasource_source_column_active',
            )
        ]

    def __str__(self):
        return f'{self.table_snapshot}.{self.column_name}'


class SourceMetadataCollectionTask(BaseModel):
    """源数据采集任务，仅负责 Phase 1 原始元数据采集。"""

    SCOPE_CHOICES = (
        ('full', '整源采集'),
        ('database', '整库采集'),
        ('table', '单表采集'),
    )
    STATUS_CHOICES = (
        ('pending', '待执行'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )
    RUN_MODE_CHOICES = (
        ('sync', '同步'),
        ('async', '异步'),
    )

    task_id = models.CharField(max_length=64, unique=True, verbose_name='任务ID')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='collection_tasks', verbose_name='数据源')
    collection_scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default='full', verbose_name='采集范围')
    run_mode = models.CharField(max_length=16, choices=RUN_MODE_CHOICES, default='sync', verbose_name='执行模式')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    database_name = models.CharField(max_length=256, blank=True, default='', verbose_name='数据库名')
    table_name = models.CharField(max_length=256, blank=True, default='', verbose_name='表名')
    total_tables = models.IntegerField(default=0, verbose_name='总表数')
    collected_tables = models.IntegerField(default=0, verbose_name='已采集表数')
    current_table = models.CharField(max_length=256, blank=True, default='', verbose_name='当前表')
    error_message = models.CharField(max_length=500, blank=True, default='', verbose_name='错误信息')
    cancel_requested = models.BooleanField(default=False, verbose_name='是否请求取消')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='开始时间')
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name='完成时间')
    result_summary = models.JSONField(default=dict, blank=True, verbose_name='结果摘要')

    class Meta:
        db_table = 'datasource_collection_task'
        verbose_name = '源数据采集任务'
        verbose_name_plural = '源数据采集任务'
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['data_source', 'status']),
            models.Index(fields=['del_flag']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['data_source'],
                condition=Q(del_flag='0') & Q(status__in=['pending', 'running']),
                name='uniq_datasource_active_collection_task',
            )
        ]

    def __str__(self):
        return self.task_id
