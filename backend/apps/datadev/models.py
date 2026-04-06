from django.core.exceptions import ValidationError
from django.db import models
from apps.system.models import BaseModel
from apps.datasource.models import DataSource


class DataDevDirectory(BaseModel):
    """
    数据目录

    用于维护数据开发模块中的目录树节点，首期内置 ODS/DWD/DWS/ADS，
    后续可继续扩展新的目录项。

    树形结构说明：
    - parent_id = 0 表示根节点
    - ancestors 按“0,父目录ID,祖先目录ID”格式维护祖级链路
    """

    ROOT_PARENT_ID = 0
    ROOT_ANCESTORS = '0'

    directory_id = models.AutoField(primary_key=True, verbose_name='目录ID')
    parent_id = models.IntegerField(default=ROOT_PARENT_ID, verbose_name='父目录ID')
    ancestors = models.CharField(max_length=255, default=ROOT_ANCESTORS, verbose_name='祖级列表')
    directory_name = models.CharField(max_length=100, verbose_name='目录名称')
    directory_code = models.CharField(max_length=32, unique=True, verbose_name='目录编码')
    order_num = models.IntegerField(default=0, verbose_name='显示顺序')
    status = models.CharField(
        max_length=1,
        choices=[('0', '正常'), ('1', '停用')],
        default='0',
        verbose_name='状态',
    )
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'datadev_directory'
        verbose_name = '数据目录'
        verbose_name_plural = '数据目录'
        ordering = ['order_num', 'directory_id']
        indexes = [
            models.Index(fields=['parent_id']),
            models.Index(fields=['directory_code']),
            models.Index(fields=['status']),
            models.Index(fields=['del_flag']),
        ]

    def clean(self):
        if self.parent_id == self.directory_id and self.directory_id is not None:
            raise ValidationError('数据目录不能将自身设置为父目录')

        if self.parent_id != self.ROOT_PARENT_ID:
            parent = DataDevDirectory.objects.filter(
                directory_id=self.parent_id,
                del_flag='0',
            ).first()
            if parent is None:
                raise ValidationError('父目录不存在，无法保存当前目录')

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.parent_id == self.ROOT_PARENT_ID:
            self.ancestors = self.ROOT_ANCESTORS
        else:
            parent = DataDevDirectory.objects.filter(
                directory_id=self.parent_id,
                del_flag='0',
            ).first()
            if parent is None:
                raise ValidationError('父目录不存在，无法保存当前目录')
            self.ancestors = f"{parent.ancestors},{parent.directory_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.directory_name} ({self.directory_code})"


class DataDevScript(BaseModel):
    """
    数据开发脚本

    脚本研发中心的核心资产模型，管理 SQL 和 Python 脚本的元信息与生命周期。
    """

    SCRIPT_TYPE_CHOICES = [
        ('sql', 'SQL'),
        ('python', 'Python'),
    ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    script_name = models.CharField(max_length=128, verbose_name='脚本名称')
    script_code = models.CharField(max_length=64, unique=True, verbose_name='脚本编码')
    script_type = models.CharField(
        max_length=20, choices=SCRIPT_TYPE_CHOICES, default='sql', verbose_name='脚本类型'
    )
    description = models.TextField(blank=True, null=True, verbose_name='脚本描述')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态'
    )
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dev_scripts',
        verbose_name='关联数据源',
        help_text='SQL 脚本执行时使用的数据源',
    )
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')
    remark = models.CharField(max_length=500, blank=True, null=True, verbose_name='备注')

    # 预留字段：后续 ADR-007 权限阶段启用
    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='归属人')
    project_id = models.CharField(max_length=64, blank=True, default='', verbose_name='项目ID')

    # 所属数据目录（未指定时自动取 order_num 最小的目录）
    directory = models.ForeignKey(
        DataDevDirectory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scripts',
        verbose_name='所属目录',
        help_text='脚本所属数据目录，未指定时使用默认目录（order_num 最小的目录）',
    )

    class Meta:
        db_table = 'datadev_script'
        verbose_name = '数据开发脚本'
        verbose_name_plural = '数据开发脚本'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['script_type']),
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.script_name} ({self.script_code})"


class DataDevScriptVersion(models.Model):
    """
    脚本版本

    记录脚本内容的版本快照，支持版本回溯。
    不继承 BaseModel —— 版本为追加写入的不可变记录，仅需 create 审计字段。
    """

    script = models.ForeignKey(
        DataDevScript,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='所属脚本',
    )
    version_number = models.PositiveIntegerField(verbose_name='版本号')
    content = models.TextField(verbose_name='脚本内容')
    content_hash = models.CharField(max_length=64, blank=True, default='', verbose_name='内容哈希')
    change_log = models.TextField(blank=True, default='', verbose_name='变更说明')
    is_current = models.BooleanField(default=False, verbose_name='当前版本')
    is_released = models.BooleanField(default=False, verbose_name='正式可用')

    create_by = models.CharField(max_length=64, blank=True, default='', verbose_name='创建者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'datadev_script_version'
        verbose_name = '脚本版本'
        verbose_name_plural = '脚本版本'
        ordering = ['-version_number']
        unique_together = [['script', 'version_number']]
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['is_released']),
        ]

    def __str__(self):
        return f"{self.script.script_name} v{self.version_number}"


class DataDevScriptExecution(models.Model):
    """
    脚本执行记录

    记录每次脚本执行的参数、状态与结果。
    不继承 BaseModel —— 执行记录为追加写入的事件日志，无需软删除。
    """

    STATUS_CHOICES = [
        ('pending', '等待执行'),
        ('running', '执行中'),
        ('success', '执行成功'),
        ('failed', '执行失败'),
        ('cancelled', '已取消'),
    ]

    script = models.ForeignKey(
        DataDevScript,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='所属脚本',
    )
    version = models.ForeignKey(
        DataDevScriptVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executions',
        verbose_name='执行版本',
    )
    execution_id = models.CharField(max_length=64, unique=True, verbose_name='执行ID')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='执行状态'
    )
    executor_type = models.CharField(max_length=20, blank=True, default='', verbose_name='执行器类型')
    executor_params = models.JSONField(blank=True, null=True, verbose_name='执行参数')

    start_time = models.DateTimeField(blank=True, null=True, verbose_name='开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name='结束时间')
    duration_seconds = models.IntegerField(blank=True, null=True, verbose_name='执行时长(秒)')

    result_summary = models.JSONField(blank=True, null=True, verbose_name='结果摘要')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')

    executed_by = models.CharField(max_length=64, blank=True, default='', verbose_name='执行者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'datadev_script_execution'
        verbose_name = '脚本执行记录'
        verbose_name_plural = '脚本执行记录'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['executed_by']),
            models.Index(fields=['create_time']),
        ]

    def __str__(self):
        return f"{self.script.script_name} - {self.execution_id} ({self.status})"
