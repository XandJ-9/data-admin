from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from ..models import ETLTaskTemplate


class ETLTaskTemplateSerializer(BaseModelSerializer):
    templateId = serializers.IntegerField(source='id', read_only=True)
    templateName = serializers.CharField(source='template_name')
    templateCode = serializers.CharField(source='template_code')
    taskType = serializers.CharField(source='task_type')
    category = serializers.CharField()
    tags = serializers.JSONField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    isSystem = serializers.BooleanField(source='is_system', read_only=True)
    usageCount = serializers.IntegerField(source='usage_count', read_only=True)
    templateConfig = serializers.JSONField(source='template_config')

    class Meta:
        model = ETLTaskTemplate
        fields = [
            'templateId', 'templateName', 'templateCode', 'taskType', 'category',
            'tags', 'description', 'isSystem', 'usageCount', 'templateConfig',
        ]


class ETLTaskTemplateQuerySerializer(serializers.Serializer):
    templateName = serializers.CharField(required=False, allow_blank=True)
    templateCode = serializers.CharField(required=False, allow_blank=True)
    taskType = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    isSystem = serializers.BooleanField(required=False)


class ETLTaskTemplateCreateSerializer(ETLTaskTemplateSerializer):
    templateName = serializers.CharField(source='template_name', required=True)
    templateCode = serializers.CharField(source='template_code', required=True)

    def validate_template_code(self, value):
        if ETLTaskTemplate.objects.filter(template_code=value).exists():
            raise serializers.ValidationError('模板编码已存在')
        return value
