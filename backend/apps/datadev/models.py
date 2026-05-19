from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
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
    """建模与加工中的加工作业定义。"""

    SCRIPT_TYPE_CHOICES = [
        ('sql', 'SQL'),
        ('python', 'Python'),
    ]
    SCRIPT_ROLE_CHOICES = [
        ('explore', '探索分析'),
        ('transform', '模型加工'),
        ('quality', '质量校验'),
        ('backfill', '数据回刷'),
        ('python_job', 'Python 作业'),
    ]
    ENGINE_TYPE_CHOICES = [
        ('spark', 'Spark SQL'),
        ('hive', 'Hive'),
        ('mvp', 'MVP预演'),
    ]
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    script_name = models.CharField(max_length=128, verbose_name='作业名称')
    script_code = models.CharField(max_length=64, unique=True, verbose_name='作业编码')
    script_type = models.CharField(
        max_length=20, choices=SCRIPT_TYPE_CHOICES, default='sql', verbose_name='作业类型'
    )
    script_role = models.CharField(
        max_length=20, choices=SCRIPT_ROLE_CHOICES, default='explore', verbose_name='作业用途'
    )
    description = models.TextField(blank=True, null=True, verbose_name='作业说明')
    engine_type = models.CharField(
        max_length=16, choices=ENGINE_TYPE_CHOICES, default='spark', verbose_name='执行引擎'
    )
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
    target_model = models.ForeignKey(
        'DataDevModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scripts',
        verbose_name='目标模型',
        help_text='生产型加工作业建议绑定目标模型，探索脚本可留空',
    )
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')
    remark = models.CharField(max_length=500, blank=True, null=True, verbose_name='备注')

    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='负责人')
    project_id = models.CharField(max_length=64, blank=True, default='', verbose_name='项目ID')

    class Meta:
        db_table = 'datadev_script'
        verbose_name = '加工作业'
        verbose_name_plural = '加工作业'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['script_type']),
            models.Index(fields=['script_role']),
            models.Index(fields=['engine_type']),
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.script_name} ({self.script_code})"


class DataDevScriptVersion(models.Model):
    """作业版本快照。"""

    script = models.ForeignKey(
        DataDevScript,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='所属作业',
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
        verbose_name = '作业版本'
        verbose_name_plural = '作业版本'
        ordering = ['-version_number']
        unique_together = [['script', 'version_number']]
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['is_released']),
        ]

    def __str__(self):
        return f"{self.script.script_name} v{self.version_number}"


class DataDevModel(BaseModel):
    """数据模型定义。"""

    LAYER_CHOICES = [
        ('ODS', 'ODS'),
        ('DWD', 'DWD'),
        ('DWS', 'DWS'),
        ('ADS', 'ADS'),
    ]
    ENGINE_CHOICES = [
        ('spark', 'Spark SQL'),
        ('hive', 'Hive'),
    ]
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('deployed', '已建表'),
    ]

    model_name = models.CharField(max_length=128, verbose_name='模型名称')
    model_code = models.CharField(max_length=64, unique=True, verbose_name='模型编码')
    layer = models.CharField(max_length=16, choices=LAYER_CHOICES, verbose_name='数据层级')
    table_name = models.CharField(max_length=255, verbose_name='目标表名')
    schema_name = models.CharField(max_length=128, blank=True, default='', verbose_name='Schema/库名')
    table_comment = models.CharField(max_length=1024, verbose_name='表注释')
    engine_type = models.CharField(max_length=16, choices=ENGINE_CHOICES, default='spark', verbose_name='执行引擎')
    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='负责人')
    description = models.TextField(blank=True, default='', verbose_name='模型说明')
    remark = models.TextField(blank=True, default='', verbose_name='备注')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')

    class Meta:
        db_table = 'datadev_model'
        verbose_name = '数据模型'
        verbose_name_plural = '数据模型'
        ordering = ['-update_time', '-create_time']
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['layer']),
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.model_name} ({self.table_name})"


class DataDevModelField(BaseModel):
    """数据模型字段定义。"""

    model = models.ForeignKey(DataDevModel, on_delete=models.CASCADE, related_name='model_fields', verbose_name='所属模型')
    ordinal_position = models.IntegerField(default=1, verbose_name='字段顺序')
    field_name = models.CharField(max_length=128, verbose_name='字段名称')
    field_type = models.CharField(max_length=64, verbose_name='字段类型')
    field_comment = models.CharField(max_length=512, blank=True, default='', verbose_name='字段注释')
    is_nullable = models.BooleanField(default=True, verbose_name='是否可空')

    class Meta:
        db_table = 'datadev_model_field'
        verbose_name = '数据模型字段'
        verbose_name_plural = '数据模型字段'
        ordering = ['ordinal_position', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['model', 'field_name'],
                condition=Q(del_flag='0'),
                name='datadev_model_field_unique_name',
            ),
        ]
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['model', 'ordinal_position']),
        ]

    def __str__(self):
        return f"{self.model.model_name}.{self.field_name}"
