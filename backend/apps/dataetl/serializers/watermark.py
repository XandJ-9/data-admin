from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from ..models import ETLWatermark


class ETLWatermarkSerializer(BaseModelSerializer):
    watermarkId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(source='task.task_name', read_only=True, required=False)
    taskCode = serializers.CharField(source='task.task_code', read_only=True, required=False)
    incrementField = serializers.CharField(source='increment_field')
    incrementType = serializers.CharField(source='increment_type')
    watermarkValue = serializers.CharField(source='watermark_value')
    executionId = serializers.CharField(source='execution_id', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ETLWatermark
        fields = [
            'watermarkId', 'taskId', 'taskName', 'taskCode',
            'incrementField', 'incrementType', 'watermarkValue', 'executionId',
        ]


class ETLWatermarkQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)


class DataXConfigValidateSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    warnings = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    config = serializers.JSONField(required=False, allow_null=True)


class DataXConfigGenerateSerializer(serializers.Serializer):
    config = serializers.JSONField()
    executionDate = serializers.CharField(required=False, allow_blank=True)
    warnings = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
