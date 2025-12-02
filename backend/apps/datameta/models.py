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
