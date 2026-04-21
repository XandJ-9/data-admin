from django.db import models
from apps.system.models import BaseModel
from apps.datasource.models import DataSource


def normalize_asset_part(value):
    return str(value or '').strip()


def build_namespace_key(data_source_id, environment, catalog_name, schema_name):
    return ':'.join([
        str(data_source_id or ''),
        normalize_asset_part(environment).lower(),
        normalize_asset_part(catalog_name).lower(),
        normalize_asset_part(schema_name).lower(),
    ])


def build_asset_qualified_name(data_source_id, environment, catalog_name, schema_name, asset_type, object_name):
    return ':'.join([
        str(data_source_id or ''),
        normalize_asset_part(environment).lower(),
        normalize_asset_part(catalog_name),
        normalize_asset_part(schema_name),
        normalize_asset_part(asset_type).lower(),
        normalize_asset_part(object_name),
    ])


def split_catalog_schema(db_type, database_name):
    database_name = normalize_asset_part(database_name)
    if normalize_asset_part(db_type).lower() in {'presto', 'trino'} and '.' in database_name:
        catalog_name, schema_name = database_name.split('.', 1)
        return normalize_asset_part(catalog_name), normalize_asset_part(schema_name)
    return database_name, ''


def resolve_collection_scope(db_type, database_name=''):
    catalog_name, schema_name = split_catalog_schema(db_type, database_name)
    scope_level = 'datasource'
    if schema_name:
        scope_level = 'schema'
    elif catalog_name:
        scope_level = 'catalog'
    return scope_level, catalog_name, schema_name


class AssetCategory(models.TextChoices):
    SOURCE = 'source', '源端元数据'
    BUSINESS = 'business', '业务元数据'
    WAREHOUSE = 'warehouse', '数仓元数据'
    SERVICE = 'service', '服务资产'
    OTHER = 'other', '其他资产'


class WarehouseLayer(models.TextChoices):
    NONE = '', '未设置'
    SOURCE = 'SOURCE', '源端'
    ODS = 'ODS', '贴源层'
    DWD = 'DWD', '明细层'
    DWS = 'DWS', '汇总层'
    ADS = 'ADS', '应用层'
    DIM = 'DIM', '维度层'


class LifecycleStatus(models.TextChoices):
    DRAFT = 'draft', '草稿'
    ACTIVE = 'active', '在线'
    OFFLINE = 'offline', '下线'
    ARCHIVED = 'archived', '归档'


class SecurityLevel(models.TextChoices):
    PUBLIC = 'public', '公开'
    INTERNAL = 'internal', '内部'
    SENSITIVE = 'sensitive', '敏感'
    RESTRICTED = 'restricted', '严格受限'


class WarehouseRole(models.TextChoices):
    NONE = '', '未设置'
    DIMENSION = 'dimension', '维度字段'
    MEASURE = 'measure', '指标字段'
    PARTITION_KEY = 'partition_key', '分区字段'
    BUSINESS_KEY = 'business_key', '业务主键'
    ATTRIBUTE = 'attribute', '属性字段'


class AssetNamespace(BaseModel):
    """资产命名空间（环境 / catalog / schema）"""

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='asset_namespaces')
    environment = models.CharField(max_length=32, default='default', verbose_name='环境')
    catalog_name = models.CharField(max_length=255, blank=True, default='', verbose_name='catalog')
    schema_name = models.CharField(max_length=255, blank=True, default='', verbose_name='schema')
    namespace_key = models.CharField(max_length=768, db_index=True, verbose_name='命名空间键')
    display_name = models.CharField(max_length=512, blank=True, default='', verbose_name='显示名称')

    class Meta:
        db_table = 'dataasset_asset_namespace'
        verbose_name = '资产命名空间'
        verbose_name_plural = '资产命名空间'
        constraints = [
            models.UniqueConstraint(
                fields=['data_source', 'environment', 'catalog_name', 'schema_name', 'del_flag'],
                name='dataasset_namespace_unique_scope'
            ),
        ]
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['data_source', 'environment']),
            models.Index(fields=['data_source', 'catalog_name', 'schema_name']),
        ]

    def save(self, *args, **kwargs):
        self.environment = normalize_asset_part(self.environment) or 'default'
        self.catalog_name = normalize_asset_part(self.catalog_name)
        self.schema_name = normalize_asset_part(self.schema_name)
        self.namespace_key = build_namespace_key(
            self.data_source_id, self.environment, self.catalog_name, self.schema_name
        )
        self.display_name = self.display_name or '.'.join(
            [part for part in [self.catalog_name, self.schema_name] if part]
        ) or self.environment
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.data_source.name}:{self.display_name}"


class DataAsset(BaseModel):
    """规范资产主表"""

    class AssetType(models.TextChoices):
        TABLE = 'table', '数据表'
        VIEW = 'view', '视图'
        MATERIALIZED_VIEW = 'materialized_view', '物化视图'
        EXTERNAL_TABLE = 'external_table', '外部表'

    namespace = models.ForeignKey(AssetNamespace, on_delete=models.CASCADE, related_name='assets')
    asset_type = models.CharField(
        max_length=32, choices=AssetType.choices, default=AssetType.TABLE, verbose_name='资产类型'
    )
    asset_category = models.CharField(
        max_length=32, choices=AssetCategory.choices, default=AssetCategory.SOURCE, verbose_name='资产分类'
    )
    object_name = models.CharField(max_length=255, verbose_name='对象名称')
    qualified_name = models.CharField(max_length=1024, db_index=True, verbose_name='限定名称')
    display_name = models.CharField(max_length=255, blank=True, default='', verbose_name='显示名称')
    comment = models.CharField(max_length=1024, blank=True, default='', verbose_name='描述')
    warehouse_layer = models.CharField(
        max_length=16, choices=WarehouseLayer.choices, blank=True, default=WarehouseLayer.NONE, verbose_name='数仓分层'
    )
    business_domain = models.CharField(max_length=128, blank=True, default='', verbose_name='业务域')
    subject_area = models.CharField(max_length=128, blank=True, default='', verbose_name='主题域')
    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='资产负责人')
    steward = models.CharField(max_length=64, blank=True, default='', verbose_name='数据管家')
    lifecycle_status = models.CharField(
        max_length=16, choices=LifecycleStatus.choices, default=LifecycleStatus.DRAFT, verbose_name='生命周期状态'
    )
    security_level = models.CharField(
        max_length=16, choices=SecurityLevel.choices, default=SecurityLevel.INTERNAL, verbose_name='安全等级'
    )
    grain = models.CharField(max_length=255, blank=True, default='', verbose_name='数据粒度')
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    last_collected_at = models.DateTimeField(null=True, blank=True, verbose_name='最近采集时间')
    legacy_meta_table_id = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name='旧元数据表ID')
    extra = models.TextField(blank=True, default='', verbose_name='扩展信息')

    class Meta:
        db_table = 'dataasset_data_asset'
        verbose_name = '数据资产'
        verbose_name_plural = '数据资产'
        constraints = [
            models.UniqueConstraint(
                fields=['namespace', 'asset_type', 'object_name', 'del_flag'],
                name='dataasset_asset_unique_object'
            ),
        ]
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['namespace', 'object_name']),
            models.Index(fields=['asset_type']),
            models.Index(fields=['asset_category']),
            models.Index(fields=['warehouse_layer']),
            models.Index(fields=['owner']),
        ]

    @property
    def data_source_id(self):
        return self.namespace.data_source_id

    def save(self, *args, **kwargs):
        self.object_name = normalize_asset_part(self.object_name)
        self.display_name = self.display_name or self.object_name
        self.qualified_name = build_asset_qualified_name(
            self.namespace.data_source_id,
            self.namespace.environment,
            self.namespace.catalog_name,
            self.namespace.schema_name,
            self.asset_type,
            self.object_name,
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.qualified_name


class DataAssetColumn(BaseModel):
    """规范资产字段"""

    asset = models.ForeignKey(DataAsset, on_delete=models.CASCADE, related_name='asset_columns')
    ordinal_position = models.IntegerField(default=0, verbose_name='字段顺序')
    column_name = models.CharField(max_length=255, verbose_name='字段名')
    data_type = models.CharField(max_length=255, blank=True, default='', verbose_name='字段类型')
    is_nullable = models.BooleanField(default=True, verbose_name='是否可空')
    default_value = models.CharField(max_length=512, blank=True, default='', verbose_name='默认值')
    is_primary_key = models.BooleanField(default=False, verbose_name='是否主键')
    comment = models.CharField(max_length=1024, blank=True, default='', verbose_name='字段描述')
    business_term = models.CharField(max_length=255, blank=True, default='', verbose_name='业务术语')
    warehouse_role = models.CharField(
        max_length=32, choices=WarehouseRole.choices, blank=True, default=WarehouseRole.NONE, verbose_name='数仓字段角色'
    )
    security_level = models.CharField(
        max_length=16, choices=SecurityLevel.choices, default=SecurityLevel.INTERNAL, verbose_name='安全等级'
    )
    standard_code = models.CharField(max_length=128, blank=True, default='', verbose_name='标准编码')
    metric_unit = models.CharField(max_length=64, blank=True, default='', verbose_name='指标单位')
    legacy_meta_column_id = models.BigIntegerField(
        null=True, blank=True, db_index=True, verbose_name='旧元数据字段ID'
    )
    extra = models.TextField(blank=True, default='', verbose_name='扩展信息')

    class Meta:
        db_table = 'dataasset_data_asset_column'
        verbose_name = '数据资产字段'
        verbose_name_plural = '数据资产字段'
        constraints = [
            models.UniqueConstraint(
                fields=['asset', 'column_name', 'del_flag'],
                name='dataasset_asset_column_unique_name'
            ),
        ]
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['asset', 'ordinal_position']),
            models.Index(fields=['asset', 'column_name']),
            models.Index(fields=['security_level']),
        ]

    def save(self, *args, **kwargs):
        self.column_name = normalize_asset_part(self.column_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset.object_name}.{self.column_name}"


class MetaTable(BaseModel):
    """元数据表"""
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='meta_tables')
    table_name = models.CharField(max_length=256, verbose_name='表名')
    comment = models.CharField(max_length=1024, blank=True, default='', verbose_name='表注释')
    database = models.CharField(max_length=256, blank=True, default='', verbose_name='数据库名')
    asset_category = models.CharField(
        max_length=32, choices=AssetCategory.choices, default=AssetCategory.SOURCE, verbose_name='资产分类'
    )
    warehouse_layer = models.CharField(
        max_length=16, choices=WarehouseLayer.choices, blank=True, default=WarehouseLayer.NONE, verbose_name='数仓分层'
    )
    business_domain = models.CharField(max_length=128, blank=True, default='', verbose_name='业务域')
    subject_area = models.CharField(max_length=128, blank=True, default='', verbose_name='主题域')
    owner = models.CharField(max_length=64, blank=True, default='', verbose_name='资产负责人')
    steward = models.CharField(max_length=64, blank=True, default='', verbose_name='数据管家')
    lifecycle_status = models.CharField(
        max_length=16, choices=LifecycleStatus.choices, default=LifecycleStatus.DRAFT, verbose_name='生命周期状态'
    )
    security_level = models.CharField(
        max_length=16, choices=SecurityLevel.choices, default=SecurityLevel.INTERNAL, verbose_name='安全等级'
    )
    grain = models.CharField(max_length=255, blank=True, default='', verbose_name='数据粒度')

    class Meta:
        db_table = 'dataasset_meta_table'
        verbose_name = '元数据表'
        verbose_name_plural = '元数据表'
        unique_together = (('data_source', 'table_name', 'database'),)
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['data_source', 'table_name']),
            models.Index(fields=['asset_category']),
            models.Index(fields=['warehouse_layer']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.data_source.name}.{self.table_name}"


class MetaColumn(BaseModel):
    """元数据字段"""
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='meta_columns')
    table = models.ForeignKey(MetaTable, on_delete=models.CASCADE, related_name='columns')
    order = models.IntegerField(default=0, verbose_name='字段顺序')
    name = models.CharField(max_length=256, verbose_name='字段名')
    type = models.CharField(max_length=256, blank=True, default='', verbose_name='字段类型')
    notnull = models.BooleanField(default=False, verbose_name='是否可空')
    default = models.CharField(max_length=512, blank=True, default='', verbose_name='默认值')
    primary = models.BooleanField(default=False, verbose_name='是否主键')
    comment = models.CharField(max_length=1024, blank=True, default='', verbose_name='字段注释')
    business_term = models.CharField(max_length=255, blank=True, default='', verbose_name='业务术语')
    warehouse_role = models.CharField(
        max_length=32, choices=WarehouseRole.choices, blank=True, default=WarehouseRole.NONE, verbose_name='数仓字段角色'
    )
    security_level = models.CharField(
        max_length=16, choices=SecurityLevel.choices, default=SecurityLevel.INTERNAL, verbose_name='安全等级'
    )
    standard_code = models.CharField(max_length=128, blank=True, default='', verbose_name='标准编码')
    metric_unit = models.CharField(max_length=64, blank=True, default='', verbose_name='指标单位')

    class Meta:
        db_table = 'dataasset_meta_column'
        verbose_name = '元数据字段'
        verbose_name_plural = '元数据字段'
        unique_together = (('data_source', 'table', 'name'),)
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['table', 'order']),
            models.Index(fields=['security_level']),
        ]

    def __str__(self):
        return f"{self.table.table_name}.{self.name}"


class MetaCollectionTask(BaseModel):
    """元数据采集任务追踪"""
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '采集中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )

    # 任务标识
    task_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='任务ID')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='collection_tasks')

    # 状态追踪
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True, verbose_name='状态')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    current_table = models.CharField(max_length=256, blank=True, verbose_name='当前处理表')

    # 采集统计
    total_tables = models.IntegerField(default=0, verbose_name='总表数')
    collected_tables = models.IntegerField(default=0, verbose_name='已采集表数')
    failed_tables = models.IntegerField(default=0, verbose_name='失败表数')

    # 配置
    database_name = models.CharField(max_length=256, blank=True, verbose_name='数据库名')
    scope_level = models.CharField(max_length=32, blank=True, default='datasource', verbose_name='采集范围层级')
    scope_catalog_name = models.CharField(max_length=256, blank=True, default='', verbose_name='范围catalog')
    scope_schema_name = models.CharField(max_length=256, blank=True, default='', verbose_name='范围schema')
    scope_asset_name = models.CharField(max_length=256, blank=True, default='', verbose_name='范围资产名')
    run_mode = models.CharField(max_length=32, blank=True, default='full', verbose_name='运行模式')

    # 结果
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    # 线程标识
    thread_id = models.CharField(max_length=64, blank=True, verbose_name='线程ID')

    class Meta:
        db_table = 'dataasset_collection_task'
        verbose_name = '元数据采集任务'
        verbose_name_plural = '元数据采集任务'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['data_source', 'create_time']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['data_source'],
                condition=models.Q(status__in=['pending', 'running']),
                name='dataasset_single_active_collection_task',
            ),
        ]
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task_id} - {self.get_status_display()}"


class TableLineage(BaseModel):
    """表血缘关系"""
    LINEAGE_TYPE_CHOICES = (
        ('upstream', '上游'),
        ('downstream', '下游'),
    )

    source_table = models.ForeignKey(
        MetaTable,
        on_delete=models.CASCADE,
        related_name='downstream_lineages',
        verbose_name='源表'
    )
    target_table = models.ForeignKey(
        MetaTable,
        on_delete=models.CASCADE,
        related_name='upstream_lineages',
        verbose_name='目标表'
    )
    lineage_type = models.CharField(
        max_length=20,
        choices=LINEAGE_TYPE_CHOICES,
        default='upstream',
        verbose_name='血缘类型'
    )
    description = models.CharField(max_length=1024, blank=True, default='', verbose_name='描述')

    class Meta:
        db_table = 'dataasset_table_lineage'
        verbose_name = '表血缘关系'
        verbose_name_plural = '表血缘关系'
        indexes = [
            models.Index(fields=['del_flag']),
            models.Index(fields=['source_table', 'target_table']),
            models.Index(fields=['lineage_type']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(source_table=models.F('target_table')),
                name='source_target_not_same'
            )
        ]

    def __str__(self):
        return f"{self.source_table.table_name} -> {self.target_table.table_name} ({self.get_lineage_type_display()})"
