from rest_framework import serializers

from apps.system.serializers import BaseModelSerializer

from .models import Task, TaskDependency, TaskInstance


class TaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='task_name', read_only=True)
    taskCode = serializers.CharField(source='task_code', read_only=True)
    taskType = serializers.CharField(source='task_type', read_only=True)
    sourceModule = serializers.CharField(source='source_module', read_only=True)
    sourceRecordId = serializers.IntegerField(source='source_record_id', read_only=True, allow_null=True)
    scheduleType = serializers.CharField(source='schedule_type', read_only=True)
    cronExpression = serializers.CharField(source='cron_expression', read_only=True)
    taskConfig = serializers.JSONField(source='task_config', read_only=True)
    lastInstanceStatus = serializers.CharField(source='last_instance_status', read_only=True)
    lastInstanceAt = serializers.DateTimeField(
        source='last_instance_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )

    class Meta:
        model = Task
        fields = [
            'taskId',
            'taskName',
            'taskCode',
            'taskType',
            'status',
            'sourceModule',
            'sourceRecordId',
            'scheduleType',
            'cronExpression',
            'owner',
            'taskConfig',
            'lastInstanceStatus',
            'lastInstanceAt',
            'remark',
        ]


class TaskQuerySerializer(serializers.Serializer):
    taskType = serializers.ChoiceField(required=False, choices=['DATA_SYNC', 'SQL_COMPUTE'])
    status = serializers.ChoiceField(required=False, choices=['draft', 'active', 'paused', 'archived'])
    sourceModule = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.CharField(required=False, allow_blank=True)


class TaskDependencySerializer(BaseModelSerializer):
    dependencyId = serializers.IntegerField(source='id', read_only=True)
    upstreamTaskId = serializers.IntegerField(source='upstream_task_id', read_only=True)
    upstreamTaskCode = serializers.CharField(source='upstream_task.task_code', read_only=True)
    upstreamTaskName = serializers.CharField(source='upstream_task.task_name', read_only=True)
    downstreamTaskId = serializers.IntegerField(source='downstream_task_id', read_only=True)
    downstreamTaskCode = serializers.CharField(source='downstream_task.task_code', read_only=True)
    downstreamTaskName = serializers.CharField(source='downstream_task.task_name', read_only=True)
    triggerCondition = serializers.CharField(source='trigger_condition', read_only=True)
    lagSeconds = serializers.IntegerField(source='lag_seconds', read_only=True)

    class Meta:
        model = TaskDependency
        fields = [
            'dependencyId',
            'upstreamTaskId',
            'upstreamTaskCode',
            'upstreamTaskName',
            'downstreamTaskId',
            'downstreamTaskCode',
            'downstreamTaskName',
            'triggerCondition',
            'lagSeconds',
            'remark',
        ]


class TaskDependencyQuerySerializer(serializers.Serializer):
    upstreamTaskId = serializers.IntegerField(required=False)
    downstreamTaskId = serializers.IntegerField(required=False)


class TaskInstanceSerializer(serializers.ModelSerializer):
    taskInstanceId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id', read_only=True)
    taskCode = serializers.CharField(source='task.task_code', read_only=True)
    taskName = serializers.CharField(source='task.task_name', read_only=True)
    instanceId = serializers.CharField(source='instance_id', read_only=True)
    triggerMode = serializers.CharField(source='trigger_mode', read_only=True)
    scheduledAt = serializers.DateTimeField(
        source='scheduled_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )
    startedAt = serializers.DateTimeField(
        source='started_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )
    finishedAt = serializers.DateTimeField(
        source='finished_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )
    durationSeconds = serializers.FloatField(source='duration_seconds', read_only=True)
    runtimeConfig = serializers.JSONField(source='runtime_config', read_only=True)
    executorType = serializers.CharField(source='executor_type', read_only=True)
    resultSummary = serializers.JSONField(source='result_summary', read_only=True)
    errorMessage = serializers.CharField(source='error_message', read_only=True)
    triggeredBy = serializers.CharField(source='triggered_by', read_only=True)
    createTime = serializers.DateTimeField(
        source='create_time',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )

    class Meta:
        model = TaskInstance
        fields = [
            'taskInstanceId',
            'taskId',
            'taskCode',
            'taskName',
            'instanceId',
            'status',
            'triggerMode',
            'scheduledAt',
            'startedAt',
            'finishedAt',
            'durationSeconds',
            'runtimeConfig',
            'executorType',
            'resultSummary',
            'errorMessage',
            'triggeredBy',
            'createTime',
        ]


class TaskInstanceQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        required=False,
        choices=['pending', 'running', 'success', 'failed', 'cancelled'],
    )
    triggerMode = serializers.ChoiceField(
        required=False,
        choices=['manual', 'schedule', 'dependency'],
    )
    triggeredBy = serializers.CharField(required=False, allow_blank=True)
