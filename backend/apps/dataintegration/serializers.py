from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer, PaginationQuerySerializer
from .models import IntegrationTask


class IntegrationTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='name')
    taskType = serializers.CharField(source='type')
    schedule = serializers.JSONField()
    detail = serializers.JSONField()
    status = serializers.CharField(required=False)
    remark = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = IntegrationTask
        fields = ['taskId', 'taskName', 'taskType', 'schedule', 'detail', 'status', 'remark']


class IntegrationTaskQuerySerializer(PaginationQuerySerializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    taskType = serializers.ChoiceField(required=False, choices=['dbToDb', 'dbToHive', 'hiveToDb'])
    status = serializers.ChoiceField(required=False, choices=['0', '1'])


class IntegrationTaskCreateSerializer(IntegrationTaskSerializer):
    pass


class IntegrationTaskUpdateSerializer(IntegrationTaskCreateSerializer):
    taskId = serializers.IntegerField()

