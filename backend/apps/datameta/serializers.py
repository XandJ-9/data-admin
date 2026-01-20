from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import MetaTable, MetaColumn


class MetaTableSerializer(BaseModelSerializer):
    tableName = serializers.CharField(source='table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    dataSourceName = serializers.CharField(source='data_source.name', read_only=True, required=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(source='database', required=False, allow_blank=True)

    class Meta:
        model = MetaTable
        fields = ['id', 'dataSourceId', 'tableName', 'comment', 'databaseName', 'dataSourceName']


class MetaColumnSerializer(BaseModelSerializer):
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
        fields = ['id', 'tableId', 'dataSourceId', 'dataSourceName', 'tableName', 'databaseName',
                  'columnIndex', 'columnName', 'dataType', 'isNullable', 'defaultValue', 'isPrimary', 'columnComment']
