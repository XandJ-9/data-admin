from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer, CamelCaseModelSerializer
from .models import MetaTable, MetaColumn, MetaCollectionTask, TableLineage


# ==================== MetaTable Serializers ==

class MetaTableSerializer(BaseModelSerializer):
    """元数据表序列化器"""
    tableName = serializers.CharField(source='table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    dataSourceName = serializers.CharField(source='data_source.name', read_only=True, required=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(source='database', required=False, allow_blank=True)

    class Meta:
        model = MetaTable
        fields = ['id', 'dataSourceId', 'tableName', 'comment', 'databaseName', 'dataSourceName']


class MetaTableQuerySerializer(serializers.Serializer):
    """元数据表查询序列化器"""
    dataSourceId = serializers.IntegerField(required=False)
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    tableName = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
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

    class Meta:
        model = MetaColumn
        fields = [
            'id', 'tableId', 'dataSourceId', 'dataSourceName', 'tableName', 'databaseName',
            'columnIndex', 'columnName', 'dataType', 'isNullable', 'defaultValue',
            'isPrimary', 'columnComment'
        ]


class MetaColumnQuerySerializer(serializers.Serializer):
    """元数据字段查询序列化器"""
    dataSourceId = serializers.IntegerField(required=False)
    tableId = serializers.IntegerField(required=False)
    tableName = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)
    columnName = serializers.CharField(required=False, allow_blank=True)
    columnComment = serializers.CharField(required=False, allow_blank=True)
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
    errorMessage = serializers.CharField(source='error_message', required=False, allow_blank=True)
    startedAt = serializers.DateTimeField(source='started_at', required=False, allow_null=True)
    completedAt = serializers.DateTimeField(source='completed_at', required=False, allow_null=True)
    threadId = serializers.CharField(source='thread_id', required=False, allow_blank=True)

    class Meta:
        model = MetaCollectionTask
        fields = [
            'taskId', 'taskUuid', 'dataSourceId', 'dataSourceName', 'status', 'progress',
            'currentTable', 'totalTables', 'collectedTables', 'failedTables', 'databaseName',
            'errorMessage', 'startedAt', 'completedAt', 'threadId'
        ]


class MetaCollectionTaskCreateSerializer(serializers.Serializer):
    """元数据采集任务创建序列化器"""
    dataSourceId = serializers.IntegerField(required=True)
    databaseName = serializers.CharField(required=False, allow_blank=True)


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
