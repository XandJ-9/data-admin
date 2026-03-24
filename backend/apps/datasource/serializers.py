from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from apps.common.encrypt import encrypt_password
from .models import DataSource


class DataSourceSerializer(BaseModelSerializer):
    """数据源序列化器（列表/详情）"""
    dataSourceId = serializers.IntegerField(source='id', read_only=True)
    dataSourceName = serializers.CharField(source='name')
    dbType = serializers.CharField(source='db_type')
    host = serializers.CharField()
    port = serializers.IntegerField()
    dbName = serializers.CharField(source='db_name')
    username = serializers.CharField()
    password = serializers.SerializerMethodField()
    params = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False, allow_blank=True)
    remark = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def get_password(self, obj) -> str:
        return encrypt_password(obj.password)

    class Meta:
        model = DataSource
        fields = [
            'dataSourceId', 'dataSourceName', 'dbType', 'host', 'port', 'dbName',
            'username', 'password', 'params', 'status', 'remark'
        ]


class DataSourceQuerySerializer(serializers.Serializer):
    """数据源查询序列化器"""
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    dbType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0', '1'])


class DataSourceCreateSerializer(DataSourceSerializer):
    """数据源创建序列化器"""
    password = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        validated_data.pop('dataSourceId', None)
        return super().create(validated_data)


class DataSourceUpdateSerializer(DataSourceSerializer):
    """数据源更新序列化器"""
    dataSourceId = serializers.IntegerField(source='id', required=True)
    password = serializers.CharField(required=False, allow_blank=True)
