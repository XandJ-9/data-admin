from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import MetaTable, MetaColumn


class MetaTableSerializer(BaseModelSerializer):
    tableName = serializers.CharField(source='table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')

    class Meta:
        model = MetaTable
        fields = ['id', 'dataSourceId', 'tableName']


class MetaColumnSerializer(BaseModelSerializer):
    tableName = serializers.CharField(source='table_name')
    dataSourceId = serializers.IntegerField(source='data_source_id')
    name = serializers.CharField()
    type = serializers.CharField()
    notnull = serializers.BooleanField()
    default = serializers.CharField()
    primary = serializers.BooleanField()

    class Meta:
        model = MetaColumn
        fields = ['id', 'dataSourceId', 'tableName', 'name', 'type', 'notnull', 'default', 'primary']
