from rest_framework import serializers

from apps.system.serializers import CamelCaseModelSerializer
from .models import OperLog


class OperLogSerializer(CamelCaseModelSerializer):
    operId = serializers.IntegerField(source='oper_id', read_only=True)
    title = serializers.CharField()
    businessType = serializers.IntegerField(source='business_type')
    method = serializers.CharField()
    requestMethod = serializers.CharField(source='request_method')
    operatorType = serializers.IntegerField(source='operator_type', required=False)
    operName = serializers.CharField(source='oper_name')
    deptName = serializers.CharField(source='dept_name', required=False)
    operUrl = serializers.CharField(source='oper_url')
    operIp = serializers.CharField(source='oper_ip')
    operLocation = serializers.CharField(source='oper_location', required=False)
    operParam = serializers.CharField(source='oper_param')
    jsonResult = serializers.CharField(source='json_result')
    status = serializers.IntegerField()
    errorMsg = serializers.CharField(source='error_msg', required=False)
    operTime = serializers.DateTimeField(source='oper_time', format='%Y-%m-%d %H:%M:%S')
    costTime = serializers.IntegerField(source='cost_time')

    class Meta:
        model = OperLog
        fields = [
            'operId', 'title', 'businessType', 'method', 'requestMethod', 'operatorType',
            'operName', 'deptName', 'operUrl', 'operIp', 'operLocation', 'operParam',
            'jsonResult', 'status', 'errorMsg', 'operTime', 'costTime'
        ]