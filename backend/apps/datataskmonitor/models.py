from django.db import models
from apps.system.models import BaseModel

class DataTask(BaseModel):
    TASK_TYPES = (
        ('collection', '数据采集'),
        ('sync', '数据同步'),
        ('calculation', '数据计算'),
        ('storage', '数据存储'),
    )
    SCHEDULE_TYPES = (
        ('cron', 'Cron表达式'),
        ('interval', '固定间隔'),
        ('once', '单次执行'),
    )
    STATUS_CHOICES = (
        ('running', '运行中'),
        ('paused', '暂停'),
        ('failed', '失败'),
        ('success', '成功'),
        ('idle', '空闲'),
    )
    ENABLE_CHOICES = (
        ('0', '启用'),
        ('1', '禁用'),
    )

    source_task = models.OneToOneField(
        'datastudio.DataStudioTask',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ops_task',
        verbose_name='来源任务',
    )
    task_name = models.CharField(max_length=128, verbose_name='任务名称')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, verbose_name='任务类型')
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='cron', verbose_name='调度类型')
    schedule_conf = models.CharField(max_length=256, verbose_name='调度配置', help_text='Cron表达式或间隔时间(秒)')
    enabled = models.CharField(max_length=1, choices=ENABLE_CHOICES, default='0', verbose_name='启用状态')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle', verbose_name='任务状态')
    last_run_time = models.DateTimeField(null=True, blank=True, verbose_name='上次运行时间')
    next_run_time = models.DateTimeField(null=True, blank=True, verbose_name='下次运行时间')
    description = models.TextField(blank=True, verbose_name='描述')

    class Meta:
        db_table = 'dt_task'
        verbose_name = '数据任务'
        verbose_name_plural = '数据任务'

    def __str__(self):
        return self.task_name

class TaskLog(BaseModel):
    STATUS_CHOICES = (
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
    )
    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, related_name='logs', verbose_name='关联任务')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='运行状态')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    message = models.TextField(blank=True, verbose_name='日志信息')

    class Meta:
        db_table = 'dt_task_log'
        verbose_name = '任务日志'
        verbose_name_plural = '任务日志'
        ordering = ['-create_time']

class AlertRule(BaseModel):
    RULE_TYPES = (
        ('failure', '任务失败'),
        ('timeout', '运行超时'),
    )
    CHANNELS = (
        ('email', '邮件'),
        ('sms', '短信'),
        ('wechat', '微信'),
    )

    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_rules', verbose_name='关联任务', help_text='为空则为全局规则')
    rule_name = models.CharField(max_length=128, verbose_name='规则名称')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, verbose_name='规则类型')
    threshold = models.IntegerField(default=0, verbose_name='阈值', help_text='超时时间(秒)或重试次数')
    notification_channels = models.CharField(max_length=128, verbose_name='通知渠道', help_text='逗号分隔')
    receivers = models.TextField(verbose_name='接收人', help_text='逗号分隔')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'dt_alert_rule'
        verbose_name = '报警规则'
        verbose_name_plural = '报警规则'

class AlertRecord(BaseModel):
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('handled', '已处理'),
        ('ignored', '已忽略'),
    )
    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, verbose_name='触发规则')
    task_name = models.CharField(max_length=128, verbose_name='相关任务')
    trigger_time = models.DateTimeField(auto_now_add=True, verbose_name='触发时间')
    content = models.TextField(verbose_name='报警内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    handle_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    handle_note = models.TextField(blank=True, verbose_name='处理备注')

    class Meta:
        db_table = 'dt_alert_record'
        verbose_name = '报警记录'
        verbose_name_plural = '报警记录'
        ordering = ['-trigger_time']
