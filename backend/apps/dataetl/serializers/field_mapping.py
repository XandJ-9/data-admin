from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from ..models import ETLFieldMapping


class ETLFieldMappingSerializer(BaseModelSerializer):
    mappingId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(source='task.task_name', read_only=True, required=False)
    sourceFieldName = serializers.CharField(source='source_field_name')
    targetFieldName = serializers.CharField(source='target_field_name')
    transformRule = serializers.CharField(source='transform_rule', required=False, allow_blank=True, allow_null=True)
    cleanRule = serializers.CharField(source='clean_rule', required=False, allow_blank=True, allow_null=True)
    dataType = serializers.CharField(source='data_type', required=False, allow_blank=True, allow_null=True)
    isPrimaryKey = serializers.BooleanField(source='is_primary_key', required=False)
    sortOrder = serializers.IntegerField(source='sort_order', required=False)

    class Meta:
        model = ETLFieldMapping
        fields = [
            'mappingId', 'taskId', 'taskName', 'sourceFieldName', 'targetFieldName',
            'transformRule', 'cleanRule', 'dataType', 'isPrimaryKey', 'sortOrder',
        ]


class ETLFieldMappingQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    sourceFieldName = serializers.CharField(required=False, allow_blank=True)
    targetFieldName = serializers.CharField(required=False, allow_blank=True)


class ETLFieldMappingCreateSerializer(ETLFieldMappingSerializer):
    taskId = serializers.IntegerField(source='task_id', required=True)
    sourceFieldName = serializers.CharField(source='source_field_name', required=True)
    targetFieldName = serializers.CharField(source='target_field_name', required=True)


class ETLFieldMappingUpdateSerializer(ETLFieldMappingSerializer):
    mappingId = serializers.IntegerField(source='id', required=True)
