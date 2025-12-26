from rest_framework import serializers
from .models import DataStudioTask

from apps.system.serializers import BaseModelSerializer



class DataStudioTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='name')
    taskType = serializers.CharField(source='type')

    class Meta:
        model = DataStudioTask
        fields = ['taskId', 'taskName', 'taskType', 'description', 'status']

class DataStudioTaskRetrieveSerializer(DataStudioTaskSerializer):
    class Meta:
        model = DataStudioTask
        fields = ['taskId', 'taskName', 'taskType', 'description', 'status', 'config']

class DataStudioTaskCreateSerializer(DataStudioTaskSerializer):
    class Meta:
        model = DataStudioTask
        fields = ['taskName', 'taskType', 'description', 'status', 'config']

class DataStudioTaskUpdateSerializer(DataStudioTaskSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = DataStudioTask
        fields = ['taskId', 'taskName', 'taskType', 'description', 'status', 'config']