from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer, PaginationQuerySerializer
from .models import IntegrationTask


class IntegrationTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='name')
    taskType = serializers.CharField(source='type')
    schedule = serializers.JSONField()
    detail = serializers.JSONField()

    class Meta:
        model = IntegrationTask
        fields = ['taskId', 'taskName', 'taskType', 'schedule', 'detail']


class IntegrationTaskQuerySerializer(PaginationQuerySerializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    taskType = serializers.ChoiceField(required=False, choices=['single', 'multi'])
    status = serializers.ChoiceField(required=False, choices=['0', '1'])


class IntegrationTaskCreateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=255)
    taskType = serializers.ChoiceField(choices=['single', 'multi'])
    schedule = serializers.JSONField()
    detail = serializers.JSONField()
    status = serializers.ChoiceField(required=False, choices=['0', '1'], default='0')
    remark = serializers.CharField(required=False, allow_blank=True, default='')


class IntegrationTaskUpdateSerializer(IntegrationTaskCreateSerializer):
    taskId = serializers.IntegerField()

