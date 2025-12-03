from django.db import models
from apps.system.models import BaseModel

from apps.datasource.models import DataSource



class QueryLog(BaseModel):
    data_source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='数据源')
    sql_text = models.TextField(verbose_name='SQL语句')
    username = models.CharField(max_length=64, verbose_name='用户名')
    status = models.CharField(max_length=10, choices=[('success', '成功'), ('fail', '失败')], default='success', verbose_name='执行状态')
    duration_ms = models.IntegerField(default=0, verbose_name='耗时(ms)')
    error_msg = models.CharField(max_length=500, blank=True, default='', verbose_name='错误信息')

    class Meta:
        db_table = 'datasource_query_log'
        verbose_name = '数据查询日志'
        verbose_name_plural = '数据查询日志'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['status']),
            models.Index(fields=['data_source']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.username} - {self.status} - {self.duration_ms}ms"