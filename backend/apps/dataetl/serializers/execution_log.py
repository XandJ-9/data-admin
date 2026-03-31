from rest_framework import serializers
from ..models import ETLExecutionLog


class ETLExecutionLogSerializer(serializers.ModelSerializer):
    logId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(source='task.task_name', read_only=True, required=False)
    taskCode = serializers.CharField(source='task.task_code', read_only=True, required=False)
    executionId = serializers.CharField(source='execution_id')
    status = serializers.CharField()
    triggerType = serializers.CharField(source='trigger_type')
    startTime = serializers.DateTimeField(source='start_time', required=False, allow_null=True)
    endTime = serializers.DateTimeField(source='end_time', required=False, allow_null=True)
    durationSeconds = serializers.IntegerField(source='duration_seconds', required=False, allow_null=True)
    totalRows = serializers.IntegerField(source='total_rows', required=False, allow_null=True)
    successRows = serializers.IntegerField(source='success_rows', required=False, allow_null=True)
    failedRows = serializers.IntegerField(source='failed_rows', required=False, allow_null=True)
    errorMessage = serializers.CharField(source='error_message', required=False, allow_blank=True, allow_null=True)
    logFile = serializers.CharField(source='log_file', required=False, allow_blank=True, allow_null=True)
    executedBy = serializers.CharField(source='executed_by', required=False, allow_blank=True, allow_null=True)
    executorParams = serializers.JSONField(source='executor_params', required=False, allow_null=True)
    createTime = serializers.DateTimeField(source='create_time', read_only=True)

    class Meta:
        model = ETLExecutionLog
        fields = [
            'logId', 'taskId', 'taskName', 'taskCode', 'executionId', 'status', 'triggerType',
            'startTime', 'endTime', 'durationSeconds', 'totalRows', 'successRows',
            'failedRows', 'errorMessage', 'logFile', 'executedBy', 'executorParams', 'createTime',
        ]


class ETLExecutionLogQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    executionId = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    triggerType = serializers.CharField(required=False, allow_blank=True)
    executedBy = serializers.CharField(required=False, allow_blank=True)
    createTimeStart = serializers.DateTimeField(required=False)
    createTimeEnd = serializers.DateTimeField(required=False)


class ETLExecutionLogCreateSerializer(ETLExecutionLogSerializer):
    taskId = serializers.IntegerField(source='task_id', required=True)
    executionId = serializers.CharField(source='execution_id', required=True)
