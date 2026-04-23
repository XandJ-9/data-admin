from rest_framework import serializers

from apps.common.encrypt import encrypt_password
from apps.system.serializers import BaseModelSerializer

from .models import DataSource


class DataSourceSerializer(BaseModelSerializer):
    dataSourceId = serializers.IntegerField(source='id', read_only=True)
    dataSourceName = serializers.CharField(source='name')
    dbType = serializers.CharField(source='db_type')
    dbName = serializers.CharField(source='db_name')
    password = serializers.SerializerMethodField()
    connectivityStatus = serializers.CharField(source='connectivity_status', read_only=True)
    connectivityMessage = serializers.CharField(source='connectivity_message', read_only=True)
    connectivityTestedAt = serializers.DateTimeField(
        source='connectivity_tested_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )

    class Meta:
        model = DataSource
        fields = [
            'dataSourceId',
            'dataSourceName',
            'dbType',
            'host',
            'port',
            'dbName',
            'username',
            'password',
            'params',
            'status',
            'remark',
            'connectivityStatus',
            'connectivityMessage',
            'connectivityTestedAt',
        ]

    def get_password(self, obj):
        return '******' if obj.password else ''


class DataSourceQuerySerializer(serializers.Serializer):
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    dbType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0', '1'])


class DataSourceCreateSerializer(DataSourceSerializer):
    password = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        validated_data.pop('id', None)
        password = validated_data.get('password', '')
        if password:
            validated_data['password'] = encrypt_password(password)
        return super().create(validated_data)


class DataSourceUpdateSerializer(DataSourceSerializer):
    dataSourceId = serializers.IntegerField(source='id', required=True)
    password = serializers.CharField(required=False, allow_blank=True)


class DataSourceTestSerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField(required=False, allow_null=True)
    dbType = serializers.CharField(source='db_type')
    host = serializers.CharField(required=False, allow_blank=True, default='')
    port = serializers.IntegerField(required=False, default=0)
    dbName = serializers.CharField(source='db_name', required=False, allow_blank=True, default='')
    username = serializers.CharField(required=False, allow_blank=True, default='')
    password = serializers.CharField(required=False, allow_blank=True, default='')
    params = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')


class DiscoveryRequestSerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField(source='data_source_id')
    databaseName = serializers.CharField(source='database_name', required=False, allow_blank=True, default='')


class TableDiscoveryRequestSerializer(DiscoveryRequestSerializer):
    tableName = serializers.CharField(source='table_name', required=False, allow_blank=True, default='')


class CollectionStatusQuerySerializer(serializers.Serializer):
    taskId = serializers.CharField(source='task_id')

