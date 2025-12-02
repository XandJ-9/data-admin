from django.db import models
from apps.system.models import BaseModel
from apps.datasource.models import DataSource


class MetaTable(BaseModel):
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=256)

    class Meta:
        db_table = 'datameta_table'
        unique_together = (('data_source', 'table_name'),)


class MetaColumn(BaseModel):
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=256)
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256, blank=True, default='')
    notnull = models.BooleanField(default=False)
    default = models.CharField(max_length=512, blank=True, default='')
    primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'datameta_column'
        unique_together = (('data_source', 'table_name', 'name'),)
