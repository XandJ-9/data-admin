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
    connectivityStatus = serializers.CharField(source='connectivity_status', read_only=True)
    connectivityMessage = serializers.CharField(source='connectivity_message', read_only=True)
    connectivityTestedAt = serializers.DateTimeField(
        source='connectivity_tested_at', read_only=True, format='%Y-%m-%d %H:%M:%S'
    )

    def get_password(self, obj) -> str:
        # 不返回真实密码，仅返回掩码标识
        return '******' if obj.password else ''

    class Meta:
        model = DataSource
        fields = [
            'dataSourceId', 'dataSourceName', 'dbType', 'host', 'port', 'dbName',
            'username', 'password', 'params', 'status', 'remark',
            'connectivityStatus', 'connectivityMessage', 'connectivityTestedAt'
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
        pwd = validated_data.get('password', '')
        if pwd:
            validated_data['password'] = encrypt_password(pwd)
        return super().create(validated_data)


class DataSourceTestSerializer(serializers.Serializer):
    """数据源连通性测试序列化器（不落库，只校验连接参数）"""
    dataSourceId = serializers.IntegerField(required=False, allow_null=True)
    dbType = serializers.CharField(source='db_type')
    host = serializers.CharField(required=False, allow_blank=True, default='')
    port = serializers.IntegerField(required=False, default=0)
    dbName = serializers.CharField(source='db_name', required=False, allow_blank=True, default='')
    username = serializers.CharField(required=False, allow_blank=True, default='')
    password = serializers.CharField(required=False, allow_blank=True, default='')
    params = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class DataSourceUpdateSerializer(DataSourceSerializer):
    """数据源更新序列化器"""
    dataSourceId = serializers.IntegerField(source='id', required=True)
    password = serializers.CharField(required=False, allow_blank=True)
