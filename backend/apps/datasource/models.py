from django.db import models

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

