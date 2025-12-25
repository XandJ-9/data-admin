from django.db import models
from apps.system.models import BaseModel

class DataStudioTask(BaseModel):
    TASK_TYPE_CHOICES = (
        ('data_integration', '数据采集'),
        ('hive', 'Hive计算'),
        ('spark', 'Spark计算'),
        ('flink', 'Flink计算'),
        ('python', 'Python脚本'),
        ('shell', 'Shell脚本'),
    )

    name = models.CharField(max_length=255, verbose_name='任务名称')
    type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    description = models.CharField(max_length=500, blank=True, default='', verbose_name='任务描述')
    config = models.JSONField(default=dict, verbose_name='任务配置')
    status = models.CharField(max_length=1, choices=[('0', '正常'), ('1', '停用')], default='0', verbose_name='状态')

    class Meta:
        db_table = 'datastudio_task'
        verbose_name = '数据开发任务'
        verbose_name_plural = '数据开发任务'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.name}({self.type})"
