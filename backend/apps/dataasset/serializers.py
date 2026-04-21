from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer, CamelCaseModelSerializer
from .models import (
    AssetNamespace,
    DataAsset,
    DataAssetColumn,
    MetaTable,
    MetaColumn,
    MetaCollectionTask,
    TableLineage,
)


class AssetNamespaceSerializer(BaseModelSerializer):
    """资产命名空间序列化器"""

    dataSourceId = serializers.IntegerField(source='data_source_id')
    dataSourceName = serializers.CharField(source='data_source.name', read_only=True, required=False)
    catalogName = serializers.CharField(source='catalog_name', required=False, allow_blank=True)
    schemaName = serializers.CharField(source='schema_name', required=False, allow_blank=True)
    namespaceKey = serializers.CharField(source='namespace_key', read_only=True)
    displayName = serializers.CharField(source='display_name', required=False, allow_blank=True)

    class Meta:
        model = AssetNamespace
        fields = [
            'id', 'dataSourceId', 'dataSourceName', 'environment',
            'catalogName', 'schemaName', 'namespaceKey', 'displayName'
        ]


class AssetNamespaceQuerySerializer(serializers.Serializer):
    """资产命名空间查询序列化器"""

    dataSourceId = serializers.IntegerField(required=False)
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    environment = serializers.CharField(required=False, allow_blank=True)
    catalogName = serializers.CharField(required=False, allow_blank=True)
    schemaName = serializers.CharField(required=False, allow_blank=True)
    keyword = serializers.CharField(required=False, allow_blank=True)


class DataAssetSerializer(BaseModelSerializer):
    """数据资产序列化器"""

    namespaceId = serializers.IntegerField(source='namespace_id')
    dataSourceId = serializers.IntegerField(source='namespace.data_source_id', read_only=True)
    dataSourceName = serializers.CharField(source='namespace.data_source.name', read_only=True, required=False)
    assetType = serializers.CharField(source='asset_type')
    assetCategory = serializers.CharField(source='asset_category', required=False, allow_blank=True)
    objectName = serializers.CharField(source='object_name')
    qualifiedName = serializers.CharField(source='qualified_name', read_only=True)
    displayName = serializers.CharField(source='display_name', required=False, allow_blank=True)
    catalogName = serializers.CharField(source='namespace.catalog_name', read_only=True, required=False)
    schemaName = serializers.CharField(source='namespace.schema_name', read_only=True, required=False)
    databaseName = serializers.SerializerMethodField()
    warehouseLayer = serializers.CharField(source='warehouse_layer', required=False, allow_blank=True)
    businessDomain = serializers.CharField(source='business_domain', required=False, allow_blank=True)
    subjectArea = serializers.CharField(source='subject_area', required=False, allow_blank=True)
    owner = serializers.CharField(required=False, allow_blank=True)
    steward = serializers.CharField(required=False, allow_blank=True)
    lifecycleStatus = serializers.CharField(source='lifecycle_status', required=False, allow_blank=True)
    securityLevel = serializers.CharField(source='security_level', required=False, allow_blank=True)
    grain = serializers.CharField(required=False, allow_blank=True)
    isActive = serializers.BooleanField(source='is_active', required=False)
    lastCollectedAt = serializers.DateTimeField(source='last_collected_at', required=False, allow_null=True)
    legacyMetaTableId = serializers.IntegerField(source='legacy_meta_table_id', read_only=True, allow_null=True)

    class Meta:
        model = DataAsset
        fields = [
            'id', 'namespaceId', 'dataSourceId', 'assetType', 'assetCategory', 'objectName',
            'dataSourceName', 'catalogName', 'schemaName', 'databaseName',
            'qualifiedName', 'displayName', 'comment', 'warehouseLayer', 'businessDomain',
            'subjectArea', 'owner', 'steward', 'lifecycleStatus', 'securityLevel', 'grain',
            'isActive', 'lastCollectedAt', 'legacyMetaTableId'
        ]

    def get_databaseName(self, obj):
        return '.'.join([part for part in [obj.namespace.catalog_name, obj.namespace.schema_name] if part])


class DataAssetQuerySerializer(serializers.Serializer):
    """数据资产查询序列化器"""

    dataSourceId = serializers.IntegerField(required=False)
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    namespaceId = serializers.IntegerField(required=False)
    assetType = serializers.CharField(required=False, allow_blank=True)
    assetCategory = serializers.CharField(required=False, allow_blank=True)
    objectName = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
    catalogName = serializers.CharField(required=False, allow_blank=True)
    schemaName = serializers.CharField(required=False, allow_blank=True)
    warehouseLayer = serializers.CharField(required=False, allow_blank=True)
    businessDomain = serializers.CharField(required=False, allow_blank=True)
    subjectArea = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.CharField(required=False, allow_blank=True)
    lifecycleStatus = serializers.CharField(required=False, allow_blank=True)
    securityLevel = serializers.CharField(required=False, allow_blank=True)
    keyword = serializers.CharField(required=False, allow_blank=True)


class DataAssetColumnSerializer(BaseModelSerializer):
    """数据资产字段序列化器"""

    assetId = serializers.IntegerField(source='asset_id')
    columnIndex = serializers.IntegerField(source='ordinal_position')
    columnName = serializers.CharField(source='column_name')
    tableName = serializers.CharField(source='asset.object_name', read_only=True)
    databaseName = serializers.SerializerMethodField()
    dataSourceId = serializers.IntegerField(source='asset.namespace.data_source_id', read_only=True)
    dataSourceName = serializers.CharField(source='asset.namespace.data_source.name', read_only=True, required=False)
    dataType = serializers.CharField(source='data_type')
    isNullable = serializers.BooleanField(source='is_nullable')
    defaultValue = serializers.CharField(source='default_value')
    isPrimary = serializers.BooleanField(source='is_primary_key')
    columnComment = serializers.CharField(source='comment', required=False, allow_blank=True)
    businessTerm = serializers.CharField(source='business_term', required=False, allow_blank=True)
    warehouseRole = serializers.CharField(source='warehouse_role', required=False, allow_blank=True)
    securityLevel = serializers.CharField(source='security_level', required=False, allow_blank=True)
    standardCode = serializers.CharField(source='standard_code', required=False, allow_blank=True)
    metricUnit = serializers.CharField(source='metric_unit', required=False, allow_blank=True)
    legacyMetaColumnId = serializers.IntegerField(source='legacy_meta_column_id', read_only=True, allow_null=True)

    class Meta:
        model = DataAssetColumn
        fields = [
            'id', 'assetId', 'dataSourceId', 'dataSourceName', 'tableName', 'databaseName',
            'columnIndex', 'columnName', 'dataType', 'isNullable', 'defaultValue',
            'isPrimary', 'columnComment', 'businessTerm', 'warehouseRole', 'securityLevel',
            'standardCode', 'metricUnit', 'legacyMetaColumnId'
        ]

    def get_databaseName(self, obj):
        return '.'.join([part for part in [obj.asset.namespace.catalog_name, obj.asset.namespace.schema_name] if part])


class DataAssetColumnQuerySerializer(serializers.Serializer):
    """数据资产字段查询序列化器"""

    dataSourceId = serializers.IntegerField(required=False)
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    assetId = serializers.IntegerField(required=False)
    tableId = serializers.IntegerField(required=False)
    tableName = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
    columnName = serializers.CharField(required=False, allow_blank=True)
    columnComment = serializers.CharField(required=False, allow_blank=True)
    businessTerm = serializers.CharField(required=False, allow_blank=True)
    warehouseRole = serializers.CharField(required=False, allow_blank=True)
    securityLevel = serializers.CharField(required=False, allow_blank=True)
    standardCode = serializers.CharField(required=False, allow_blank=True)


class DataAssetDetailSerializer(DataAssetSerializer):
    """数据资产详情序列化器"""

    columns = DataAssetColumnSerializer(source='asset_columns', many=True, read_only=True)

    class Meta(DataAssetSerializer.Meta):
        fields = DataAssetSerializer.Meta.fields + ['columns']


class CanonicalMetaTableSerializer(BaseModelSerializer):
    """兼容旧元数据表响应的规范资产序列化器"""

    id = serializers.SerializerMethodField()
    createBy = serializers.CharField(source='legacy_create_by', read_only=True, required=False, allow_blank=True, allow_null=True)
    updateBy = serializers.CharField(source='legacy_update_by', read_only=True, required=False, allow_blank=True, allow_null=True)
    createTime = serializers.DateTimeField(source='legacy_create_time', read_only=True, format='%Y-%m-%d %H:%M:%S')
    updateTime = serializers.DateTimeField(source='legacy_update_time', read_only=True, format='%Y-%m-%d %H:%M:%S')
    tableName = serializers.CharField(source='object_name')
    dataSourceId = serializers.IntegerField(source='namespace.data_source_id', read_only=True)
    dataSourceName = serializers.CharField(source='namespace.data_source.name', read_only=True, required=False)
    databaseName = serializers.SerializerMethodField()
    assetType = serializers.CharField(source='asset_type', read_only=True)
    assetCategory = serializers.CharField(source='asset_category', read_only=True)
    namespaceId = serializers.IntegerField(source='namespace_id', read_only=True)
    catalogName = serializers.CharField(source='namespace.catalog_name', read_only=True, required=False)
    schemaName = serializers.CharField(source='namespace.schema_name', read_only=True, required=False)
    qualifiedName = serializers.CharField(source='qualified_name', read_only=True)
    warehouseLayer = serializers.CharField(source='warehouse_layer', read_only=True)
    businessDomain = serializers.CharField(source='business_domain', read_only=True)
    subjectArea = serializers.CharField(source='subject_area', read_only=True)
    owner = serializers.CharField(read_only=True)
    steward = serializers.CharField(read_only=True)
    lifecycleStatus = serializers.CharField(source='lifecycle_status', read_only=True)
    securityLevel = serializers.CharField(source='security_level', read_only=True)
    grain = serializers.CharField(read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    lastCollectedAt = serializers.DateTimeField(source='last_collected_at', required=False, allow_null=True)

    class Meta:
        model = DataAsset
        fields = [
            'id', 'namespaceId', 'dataSourceId', 'dataSourceName', 'tableName', 'databaseName',
            'catalogName', 'schemaName', 'assetType', 'assetCategory', 'qualifiedName', 'comment',
            'warehouseLayer', 'businessDomain', 'subjectArea', 'owner', 'steward',
            'lifecycleStatus', 'securityLevel', 'grain', 'isActive', 'lastCollectedAt',
            'createBy', 'updateBy', 'createTime', 'updateTime'
        ]

    def get_id(self, obj):
        return obj.legacy_meta_table_id or obj.id

    def get_databaseName(self, obj):
        return '.'.join([part for part in [obj.namespace.catalog_name, obj.namespace.schema_name] if part])


class CanonicalMetaColumnSerializer(BaseModelSerializer):
    """兼容旧元数据字段响应的规范字段序列化器"""

    id = serializers.SerializerMethodField()
    tableId = serializers.SerializerMethodField()
    createBy = serializers.CharField(source='legacy_create_by', read_only=True, required=False, allow_blank=True, allow_null=True)
    updateBy = serializers.CharField(source='legacy_update_by', read_only=True, required=False, allow_blank=True, allow_null=True)
    tableName = serializers.CharField(source='asset.object_name', read_only=True)
    dataSourceId = serializers.IntegerField(source='asset.namespace.data_source_id', read_only=True)
    dataSourceName = serializers.CharField(source='asset.namespace.data_source.name', read_only=True, required=False)
    databaseName = serializers.SerializerMethodField()
    columnIndex = serializers.IntegerField(source='ordinal_position')
    columnName = serializers.CharField(source='column_name')
    dataType = serializers.CharField(source='data_type')
    isNullable = serializers.BooleanField(source='is_nullable')
    defaultValue = serializers.CharField(source='default_value')
    isPrimary = serializers.BooleanField(source='is_primary_key')
    columnComment = serializers.CharField(source='comment', required=False, allow_blank=True)
    businessTerm = serializers.CharField(source='business_term', read_only=True)
    warehouseRole = serializers.CharField(source='warehouse_role', read_only=True)
    securityLevel = serializers.CharField(source='security_level', read_only=True)
    standardCode = serializers.CharField(source='standard_code', read_only=True)
    metricUnit = serializers.CharField(source='metric_unit', read_only=True)

    class Meta:
        model = DataAssetColumn
        fields = [
            'id', 'tableId', 'dataSourceId', 'dataSourceName', 'tableName', 'databaseName',
            'columnIndex', 'columnName', 'dataType', 'isNullable', 'defaultValue',
            'isPrimary', 'columnComment', 'businessTerm', 'warehouseRole', 'securityLevel',
            'standardCode', 'metricUnit', 'createBy', 'updateBy'
        ]

    def get_id(self, obj):
        return obj.legacy_meta_column_id or obj.id

    def get_tableId(self, obj):
        return obj.asset.legacy_meta_table_id or obj.asset_id

    def get_databaseName(self, obj):
        return '.'.join([part for part in [obj.asset.namespace.catalog_name, obj.asset.namespace.schema_name] if part])


# ==================== MetaTable Serializers ==

class MetaTableSerializer(BaseModelSerializer):
    """元数据表序列化器"""
    tableName = serializers.CharField(source='table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    dataSourceName = serializers.CharField(source='data_source.name', read_only=True, required=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(source='database', required=False, allow_blank=True)
    assetCategory = serializers.CharField(source='asset_category', required=False, allow_blank=True)
    warehouseLayer = serializers.CharField(source='warehouse_layer', required=False, allow_blank=True)
    businessDomain = serializers.CharField(source='business_domain', required=False, allow_blank=True)
    subjectArea = serializers.CharField(source='subject_area', required=False, allow_blank=True)
    owner = serializers.CharField(required=False, allow_blank=True)
    steward = serializers.CharField(required=False, allow_blank=True)
    lifecycleStatus = serializers.CharField(source='lifecycle_status', required=False, allow_blank=True)
    securityLevel = serializers.CharField(source='security_level', required=False, allow_blank=True)
    grain = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = MetaTable
        fields = [
            'id', 'dataSourceId', 'tableName', 'comment', 'databaseName', 'dataSourceName',
            'assetCategory', 'warehouseLayer', 'businessDomain', 'subjectArea', 'owner',
            'steward', 'lifecycleStatus', 'securityLevel', 'grain'
        ]


class MetaTableQuerySerializer(serializers.Serializer):
    """元数据表查询序列化器"""
    dataSourceId = serializers.IntegerField(required=False)
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    tableName = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
    assetCategory = serializers.CharField(required=False, allow_blank=True)
    warehouseLayer = serializers.CharField(required=False, allow_blank=True)
    businessDomain = serializers.CharField(required=False, allow_blank=True)
    subjectArea = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.CharField(required=False, allow_blank=True)
    lifecycleStatus = serializers.CharField(required=False, allow_blank=True)
    securityLevel = serializers.CharField(required=False, allow_blank=True)
    createTimeStart = serializers.DateTimeField(required=False)
    createTimeEnd = serializers.DateTimeField(required=False)
    updateTimeStart = serializers.DateTimeField(required=False)
    updateTimeEnd = serializers.DateTimeField(required=False)


# ==================== MetaColumn Serializers ====================

class MetaColumnSerializer(BaseModelSerializer):
    """元数据字段序列化器"""
    tableName = serializers.CharField(source='table.table_name')
    tableId = serializers.IntegerField(source='table.id')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    dataSourceName = serializers.CharField(source='data_source.name', read_only=True, required=False)
    databaseName = serializers.CharField(source='table.database', read_only=True, required=False)
    columnIndex = serializers.IntegerField(source='order')
    columnName = serializers.CharField(source='name')
    dataType = serializers.CharField(source='type')
    isNullable = serializers.BooleanField(source='notnull')
    defaultValue = serializers.CharField(source='default')
    isPrimary = serializers.BooleanField(source='primary')
    columnComment = serializers.CharField(source='comment', required=False, allow_blank=True)
    businessTerm = serializers.CharField(source='business_term', required=False, allow_blank=True)
    warehouseRole = serializers.CharField(source='warehouse_role', required=False, allow_blank=True)
    securityLevel = serializers.CharField(source='security_level', required=False, allow_blank=True)
    standardCode = serializers.CharField(source='standard_code', required=False, allow_blank=True)
    metricUnit = serializers.CharField(source='metric_unit', required=False, allow_blank=True)

    class Meta:
        model = MetaColumn
        fields = [
            'id', 'tableId', 'dataSourceId', 'dataSourceName', 'tableName', 'databaseName',
            'columnIndex', 'columnName', 'dataType', 'isNullable', 'defaultValue',
            'isPrimary', 'columnComment', 'businessTerm', 'warehouseRole', 'securityLevel',
            'standardCode', 'metricUnit'
        ]


class MetaColumnQuerySerializer(serializers.Serializer):
    """元数据字段查询序列化器"""
    dataSourceId = serializers.IntegerField(required=False)
    tableId = serializers.IntegerField(required=False)
    tableName = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
    columnName = serializers.CharField(required=False, allow_blank=True)
    columnComment = serializers.CharField(required=False, allow_blank=True)
    businessTerm = serializers.CharField(required=False, allow_blank=True)
    warehouseRole = serializers.CharField(required=False, allow_blank=True)
    securityLevel = serializers.CharField(required=False, allow_blank=True)
    standardCode = serializers.CharField(required=False, allow_blank=True)
    dataSourceName = serializers.CharField(required=False, allow_blank=True)


# ==================== MetaCollectionTask Serializers ====================

class MetaCollectionTaskSerializer(CamelCaseModelSerializer):
    """元数据采集任务序列化器"""
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskUuid = serializers.CharField(source='task_id')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    dataSourceName = serializers.CharField(source='data_source.name', read_only=True, required=False)
    status = serializers.CharField(required=False)
    progress = serializers.IntegerField(required=False)
    currentTable = serializers.CharField(source='current_table', required=False, allow_blank=True)
    totalTables = serializers.IntegerField(source='total_tables', required=False)
    collectedTables = serializers.IntegerField(source='collected_tables', required=False)
    failedTables = serializers.IntegerField(source='failed_tables', required=False)
    databaseName = serializers.CharField(source='database_name', required=False, allow_blank=True)
    scopeLevel = serializers.CharField(source='scope_level', required=False, allow_blank=True)
    scopeCatalogName = serializers.CharField(source='scope_catalog_name', required=False, allow_blank=True)
    scopeSchemaName = serializers.CharField(source='scope_schema_name', required=False, allow_blank=True)
    scopeAssetName = serializers.CharField(source='scope_asset_name', required=False, allow_blank=True)
    runMode = serializers.CharField(source='run_mode', required=False, allow_blank=True)
    errorMessage = serializers.CharField(source='error_message', required=False, allow_blank=True)
    startedAt = serializers.DateTimeField(source='started_at', required=False, allow_null=True)
    completedAt = serializers.DateTimeField(source='completed_at', required=False, allow_null=True)
    threadId = serializers.CharField(source='thread_id', required=False, allow_blank=True)

    class Meta:
        model = MetaCollectionTask
        fields = [
            'taskId', 'taskUuid', 'dataSourceId', 'dataSourceName', 'status', 'progress',
            'currentTable', 'totalTables', 'collectedTables', 'failedTables', 'databaseName',
            'scopeLevel', 'scopeCatalogName', 'scopeSchemaName', 'scopeAssetName', 'runMode',
            'errorMessage', 'startedAt', 'completedAt', 'threadId'
        ]


class MetaCollectionTaskCreateSerializer(serializers.Serializer):
    """元数据采集任务创建序列化器"""
    dataSourceId = serializers.IntegerField(required=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
    scopeLevel = serializers.CharField(required=False, allow_blank=True)
    scopeCatalogName = serializers.CharField(required=False, allow_blank=True)
    scopeSchemaName = serializers.CharField(required=False, allow_blank=True)
    scopeAssetName = serializers.CharField(required=False, allow_blank=True)
    runMode = serializers.CharField(required=False, allow_blank=True)


# ==================== TableLineage Serializers ====================

class TableLineageSerializer(BaseModelSerializer):
    """表血缘序列化器"""
    sourceTableId = serializers.IntegerField(source='source_table.id', read_only=True)
    sourceTableName = serializers.CharField(source='source_table.table_name', read_only=True)
    targetTableId = serializers.IntegerField(source='target_table.id', read_only=True)
    targetTableName = serializers.CharField(source='target_table.table_name', read_only=True)
    lineageType = serializers.CharField(source='lineage_type')
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = TableLineage
        fields = [
            'id', 'sourceTableId', 'sourceTableName', 'targetTableId', 'targetTableName',
            'lineageType', 'description'
        ]


class TableLineageCreateSerializer(serializers.Serializer):
    """表血缘创建序列化器"""
    sourceTableId = serializers.IntegerField(required=True)
    targetTableId = serializers.IntegerField(required=True)
    lineageType = serializers.ChoiceField(
        choices=['upstream', 'downstream'],
        default='upstream',
        required=False
    )
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['sourceTableId'] == data['targetTableId']:
            raise serializers.ValidationError("源表和目标表不能相同")
        return data


class TableLineageUpdateSerializer(TableLineageCreateSerializer):
    """表血缘更新序列化器"""
    id = serializers.IntegerField(required=True)


class TableLineageQuerySerializer(serializers.Serializer):
    """表血缘查询序列化器"""
    sourceTableId = serializers.IntegerField(required=False)
    targetTableId = serializers.IntegerField(required=False)
    sourceTableName = serializers.CharField(required=False, allow_blank=True)
    targetTableName = serializers.CharField(required=False, allow_blank=True)
    lineageType = serializers.ChoiceField(
        choices=['upstream', 'downstream'],
        required=False
    )


class TableLineageGraphSerializer(serializers.Serializer):
    """表血缘图查询序列化器"""
    tableId = serializers.IntegerField(required=False)
    tableName = serializers.CharField(required=False, allow_blank=True)
    depth = serializers.IntegerField(required=False, default=2)
