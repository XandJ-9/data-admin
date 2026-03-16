from django.utils import timezone
from rest_framework import serializers

from apps.system.serializers import BaseModelSerializer
from .models import DataTask, TaskLog, AlertRule, AlertRecord, TaskExecution, TaskExecutionLog
from .taskmanager.scheduler import calc_next_run_time

class DataTaskSerializer(BaseModelSerializer):
    sourceTaskId = serializers.IntegerField(source='source_task_id', read_only=True)
    sourceTaskType = serializers.CharField(source='source_task.type', read_only=True)
    sourceTaskStatus = serializers.CharField(source='source_task.status', read_only=True)

    taskName = serializers.CharField(source='task_name', read_only=True)
    taskType = serializers.CharField(source='task_type', read_only=True)
    scheduleType = serializers.CharField(source='schedule_type')
    scheduleConf = serializers.CharField(source='schedule_conf', required=False, allow_blank=True, allow_null=True)
    enabled = serializers.CharField()
    status = serializers.CharField(read_only=True)
    lastRunTime = serializers.DateTimeField(
        source='last_run_time',
        read_only=True,
        allow_null=True,
        format='%Y-%m-%d %H:%M:%S',
    )
    nextRunTime = serializers.DateTimeField(
        source='next_run_time',
        read_only=True,
        allow_null=True,
        format='%Y-%m-%d %H:%M:%S',
    )
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        schedule_type = attrs.get('schedule_type', getattr(self.instance, 'schedule_type', None))
        schedule_conf = attrs.get('schedule_conf', getattr(self.instance, 'schedule_conf', None))

        schedule_type = (schedule_type or '').strip()
        schedule_conf = (schedule_conf or '').strip()

        if schedule_type == 'interval':
            try:
                seconds = int(schedule_conf)
            except Exception:
                raise serializers.ValidationError({'schedule_conf': '固定间隔必须为整数秒'})
            if seconds <= 0:
                raise serializers.ValidationError({'schedule_conf': '固定间隔必须大于0'})
            attrs['schedule_conf'] = str(seconds)
        elif schedule_type == 'cron':
            if not schedule_conf:
                raise serializers.ValidationError({'schedule_conf': 'Cron表达式不能为空'})
        elif schedule_type == 'once':
            attrs['schedule_conf'] = schedule_conf
        else:
            raise serializers.ValidationError({'schedule_type': '不支持的调度类型'})

        attrs['schedule_type'] = schedule_type
        return attrs

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        base_time = timezone.now()
        instance.next_run_time = (
            None if instance.enabled == '1' else calc_next_run_time(instance.schedule_type, instance.schedule_conf, base_time=base_time)
        )
        instance.save(update_fields=['next_run_time', 'update_time'])
        return instance

    class Meta:
        model = DataTask
        fields = [
            'id',
            'sourceTaskId',
            'sourceTaskType',
            'sourceTaskStatus',
            'taskName',
            'taskType',
            'scheduleType',
            'scheduleConf',
            'enabled',
            'status',
            'lastRunTime',
            'nextRunTime',
            'description',
        ]
        read_only_fields = [
            'id',
            'sourceTaskId',
            'sourceTaskType',
            'sourceTaskStatus',
            'taskName',
            'taskType',
            'status',
            'lastRunTime',
            'nextRunTime',
        ]

class TaskLogSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='task_id', read_only=True)
    taskName = serializers.CharField(source='task.task_name', read_only=True)
    startTime = serializers.DateTimeField(source='start_time', format='%Y-%m-%d %H:%M:%S')
    endTime = serializers.DateTimeField(source='end_time', allow_null=True, required=False, format='%Y-%m-%d %H:%M:%S')
    message = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = TaskLog
        fields = ['id', 'taskId', 'taskName', 'status', 'startTime', 'endTime', 'message']

class AlertRuleSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='task_id', required=False, allow_null=True)
    taskName = serializers.CharField(source='task.task_name', read_only=True)
    ruleName = serializers.CharField(source='rule_name')
    ruleType = serializers.CharField(source='rule_type')
    notificationChannels = serializers.CharField(source='notification_channels', required=False, allow_blank=True, allow_null=True)
    isActive = serializers.BooleanField(source='is_active')

    class Meta:
        model = AlertRule
        fields = [
            'id',
            'taskId',
            'taskName',
            'ruleName',
            'ruleType',
            'threshold',
            'notificationChannels',
            'receivers',
            'isActive',
        ]

class AlertRecordSerializer(BaseModelSerializer):
    ruleId = serializers.IntegerField(source='rule_id', read_only=True)
    ruleName = serializers.CharField(source='rule.rule_name', read_only=True)
    taskName = serializers.CharField(source='task_name')
    triggerTime = serializers.DateTimeField(source='trigger_time', read_only=True, format='%Y-%m-%d %H:%M:%S')
    handleTime = serializers.DateTimeField(source='handle_time', read_only=True, allow_null=True, format='%Y-%m-%d %H:%M:%S')
    handleNote = serializers.CharField(source='handle_note', read_only=True, allow_blank=True, allow_null=True)

    class Meta:
        model = AlertRecord
        fields = [
            'id',
            'ruleId',
            'ruleName',
            'taskName',
            'triggerTime',
            'content',
            'status',
            'handleTime',
            'handleNote',
        ]


class TaskExecutionSerializer(BaseModelSerializer):
    """
    通用任务执行记录序列化器
    支持所有任务类型（ETL、元数据采集、质量检查等）
    """

    taskType = serializers.CharField(source='task_type', read_only=True)
    taskTypeDisplay = serializers.CharField(source='get_task_type_display', read_only=True)
    statusDisplay = serializers.CharField(source='get_status_display', read_only=True)

    startTime = serializers.DateTimeField(source='start_time', format='%Y-%m-%d %H:%M:%S')
    endTime = serializers.DateTimeField(source='end_time', allow_null=True, required=False, format='%Y-%m-%d %H:%M:%S')

    durationFormatted = serializers.SerializerMethodField()

    class Meta:
        model = TaskExecution
        fields = [
            'id', 'taskType', 'taskTypeDisplay', 'taskId',
            'startTime', 'endTime', 'durationSeconds', 'durationFormatted',
            'status', 'statusDisplay', 'progress',
            'rowsRead', 'rowsWritten', 'bytesProcessed',
            'errorMessage', 'errorStack',
            'peakMemoryMb', 'logFilePath', 'executorType',
            'createTime',
        ]

    def get_duration_formatted(self, obj):
        """格式化执行时长"""
        if not obj.duration_seconds:
            return '-'
        duration = obj.duration_seconds
        if duration < 60:
            return f"{duration}秒"
        elif duration < 3600:
            minutes = duration // 60
            seconds = duration % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            return f"{hours}小时{minutes}分"


class TaskExecutionListSerializer(BaseModelSerializer):
    """任务执行记录列表序列化器（简化版）"""

    taskType = serializers.CharField(source='task_type', read_only=True)
    statusDisplay = serializers.CharField(source='get_status_display', read_only=True)
    startTime = serializers.DateTimeField(source='start_time', format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = TaskExecution
        fields = [
            'id', 'taskType', 'taskId',
            'status', 'statusDisplay', 'progress',
            'rowsRead', 'rowsWritten',
            'durationSeconds', 'startTime',
            'errorMessage',
        ]


class TaskExecutionLogSerializer(BaseModelSerializer):
    """任务执行日志序列化器"""

    executionId = serializers.IntegerField(source='execution_id', read_only=True)
    logLevel = serializers.CharField(source='log_level')
    timestamp = serializers.DateTimeField(source='create_time', format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = TaskExecutionLog
        fields = [
            'id', 'executionId', 'logLevel', 'message', 'metadata', 'timestamp',
        ]
