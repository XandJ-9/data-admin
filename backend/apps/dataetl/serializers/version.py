from rest_framework import serializers
from ..models import ETLTaskVersion


class ETLTaskVersionSerializer(serializers.ModelSerializer):
    versionId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(source='task.task_name', read_only=True, required=False)
    versionNumber = serializers.IntegerField(source='version_number')
    configSnapshot = serializers.JSONField(source='config_snapshot')
    changeLog = serializers.CharField(source='change_log')
    isCurrent = serializers.BooleanField(source='is_current')
    createBy = serializers.CharField(source='create_by', required=False, allow_blank=True)
    createTime = serializers.DateTimeField(source='create_time', read_only=True)

    class Meta:
        model = ETLTaskVersion
        fields = [
            'versionId', 'taskId', 'taskName', 'versionNumber', 'configSnapshot',
            'changeLog', 'isCurrent', 'createBy', 'createTime',
        ]


class ETLTaskVersionCreateSerializer(ETLTaskVersionSerializer):
    taskId = serializers.IntegerField(source='task_id', required=True)
