from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from apps.dataservice.models import QueryLog


class DataServiceQuerySerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField()
    sql = serializers.CharField()
    params = serializers.DictField(child=serializers.CharField(), required=False, allow_empty=True)
    pageSize = serializers.IntegerField(required=False, min_value=1, default=50)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class DataServiceQueryLogSerializer(BaseModelSerializer):
    logId = serializers.IntegerField(source='id')
    dataSourceName = serializers.CharField(source='data_source.name')
    userName = serializers.CharField(source='username')
    sqlText = serializers.CharField(source='sql_text')
    status = serializers.CharField()
    durationMs = serializers.IntegerField(source='duration_ms')
    errorMsg = serializers.CharField(source='error_msg', required=False, allow_blank=True)

    class Meta:
        model = QueryLog
        fields = ['logId', 'dataSourceName', 'userName', 'sqlText', 'status', 'durationMs', 'errorMsg', 'createTime']