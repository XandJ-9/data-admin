from django.db import models
from apps.system.models import BaseModel


class IntegrationTask(BaseModel):
    TASK_TYPE_CHOICES = (
        ('single', '单表'),
        ('multi', '分库分表'),
    )

    name = models.CharField(max_length=255, verbose_name='任务名称')
    type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    schedule = models.JSONField(default=dict, verbose_name='调度配置')
    detail = models.JSONField(default=dict, verbose_name='任务详情')
    status = models.CharField(max_length=1, choices=[('0', '正常'), ('1', '停用')], default='0', verbose_name='状态')
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'dataintegration_task'
        verbose_name = '数据集成任务'
        verbose_name_plural = '数据集成任务'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.name}({self.type})"

