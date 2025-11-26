from rest_framework import serializers
from system.serializers import BaseModelSerializer
from .models import DataSource


class DataSourceSerializer(BaseModelSerializer):
    dataSourceId = serializers.IntegerField(source='id', read_only=True)
    dataSourceName = serializers.CharField(source='name')
    dbType = serializers.CharField(source='db_type')
    host = serializers.CharField()
    port = serializers.IntegerField()
    dbName = serializers.CharField(source='db_name')
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    params = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = DataSource
        fields = [
            'dataSourceId', 'dataSourceName', 'dbType', 'host', 'port', 'dbName',
            'username', 'password', 'params'
        ]


class DataSourceQuerySerializer(serializers.Serializer):
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    dbType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0', '1'])


class DataSourceUpdateSerializer(DataSourceSerializer):
    dataSourceId = serializers.IntegerField(source='id')