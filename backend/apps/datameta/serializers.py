from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import MetaTable, MetaColumn


class MetaTableSerializer(BaseModelSerializer):
    tableName = serializers.CharField(source='table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    comment = serializers.CharField(required=False, allow_blank=True)
    databaseName = serializers.CharField(source='database', required=False, allow_blank=True)

    class Meta:
        model = MetaTable
        fields = ['id', 'dataSourceId', 'tableName', 'comment', 'databaseName']


class MetaColumnSerializer(BaseModelSerializer):
    tableName = serializers.CharField(source='table.table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    columnIndex = serializers.IntegerField(source='order')
    name = serializers.CharField()
    type = serializers.CharField()
    notnull = serializers.BooleanField()
    default = serializers.CharField()
    primary = serializers.BooleanField()
    comment = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = MetaColumn
        fields = ['id', 'dataSourceId', 'tableName', 'columnIndex', 'name', 'type', 'notnull', 'default', 'primary', 'comment']
