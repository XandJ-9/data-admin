from rest_framework import serializers

from apps.datatask.models import TaskInstance
from apps.datatask.models import Task
from apps.datasource.models import DataSource
from apps.system.serializers import BaseModelSerializer

from .models import DataIntegrationTask
from .task_source import PUBLISHED_TO_TASK_OPS_KEY


class DataIntegrationTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='task_name', read_only=True)
    taskCode = serializers.CharField(source='task_code', read_only=True)
    sourceDataSourceId = serializers.IntegerField(source='source_datasource_id', read_only=True, allow_null=True)
    sourceDataSourceName = serializers.SerializerMethodField()
    targetDataSourceId = serializers.IntegerField(source='target_datasource_id', read_only=True, allow_null=True)
    targetDataSourceName = serializers.SerializerMethodField()
    sourceTableName = serializers.CharField(source='source_table_name', read_only=True)
    sourceDatabaseName = serializers.CharField(source='source_database_name', read_only=True)
    targetSchemaName = serializers.CharField(source='target_schema_name', read_only=True)
    targetTableName = serializers.CharField(source='target_table_name', read_only=True)
    loadType = serializers.CharField(source='load_type', read_only=True)
    writeMode = serializers.CharField(source='write_mode', read_only=True)
    executorType = serializers.CharField(source='executor_type', read_only=True)
    scheduleType = serializers.CharField(source='schedule_type', read_only=True)
    cronExpression = serializers.CharField(source='cron_expression', read_only=True)
    taskConfig = serializers.JSONField(source='task_config', read_only=True)
    publishedToTaskOps = serializers.SerializerMethodField()
    platformTaskId = serializers.SerializerMethodField()

    class Meta:
        model = DataIntegrationTask
        fields = [
            'taskId',
            'taskName',
            'taskCode',
            'status',
            'sourceDataSourceId',
            'sourceDataSourceName',
            'targetDataSourceId',
            'targetDataSourceName',
            'sourceTableName',
            'sourceDatabaseName',
            'targetSchemaName',
            'targetTableName',
            'loadType',
            'writeMode',
            'executorType',
            'scheduleType',
            'cronExpression',
            'publishedToTaskOps',
            'platformTaskId',
            'owner',
            'taskConfig',
            'remark',
        ]

    def get_sourceDataSourceName(self, obj):
        if obj.source_datasource is None:
            return ''
        return obj.source_datasource.name

    def get_targetDataSourceName(self, obj):
        if obj.target_datasource is None:
            return ''
        return obj.target_datasource.name

    def _get_platform_task(self, obj):
        cache = getattr(self, '_platform_task_cache', None)
        if cache is None:
            cache = {}
            self._platform_task_cache = cache
        if obj.id not in cache:
            cache[obj.id] = Task.objects.filter(
                source_module='dataintegration.task',
                source_record_id=obj.id,
                del_flag='0',
            ).only('id', 'task_config').first()
        return cache[obj.id]

    def get_publishedToTaskOps(self, obj):
        platform_task = self._get_platform_task(obj)
        if platform_task is None:
            return False
        return bool((platform_task.task_config or {}).get(PUBLISHED_TO_TASK_OPS_KEY))

    def get_platformTaskId(self, obj):
        platform_task = self._get_platform_task(obj)
        if platform_task is None:
            return None
        return platform_task.id

class DataIntegrationTaskCreateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=128)
    taskCode = serializers.CharField(max_length=128)
    sourceDataSourceId = serializers.IntegerField()
    targetDataSourceId = serializers.IntegerField()
    sourceDatabaseName = serializers.CharField(required=False, allow_blank=True, default='')
    sourceTableName = serializers.CharField(max_length=256)
    targetSchemaName = serializers.CharField(required=False, allow_blank=True, default='')
    targetTableName = serializers.CharField(max_length=128)
    loadType = serializers.ChoiceField(choices=['full', 'incremental'], default='full')
    writeMode = serializers.ChoiceField(choices=['overwrite', 'append', 'upsert'], default='overwrite')
    executorType = serializers.ChoiceField(choices=['mock', 'datax'], default='mock')
    scheduleType = serializers.ChoiceField(choices=['manual', 'cron'], default='manual')
    cronExpression = serializers.CharField(required=False, allow_blank=True, default='')
    owner = serializers.CharField(required=False, allow_blank=True, default='')
    taskConfig = serializers.JSONField(required=False, default=dict)
    remark = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_taskCode(self, value):
        if DataIntegrationTask.objects.filter(task_code=value, del_flag='0').exists():
            raise serializers.ValidationError('任务编码已存在')
        return value

    def validate_sourceDataSourceId(self, value):
        if not DataSource.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源数据源不存在')
        return value

    def validate_targetDataSourceId(self, value):
        if not DataSource.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('目标数据源不存在')
        return value

    def validate(self, attrs):
        if attrs['sourceDataSourceId'] == attrs['targetDataSourceId']:
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if attrs['scheduleType'] == 'cron' and not attrs.get('cronExpression'):
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        if not str(attrs.get('sourceTableName') or '').strip():
            raise serializers.ValidationError({'sourceTableName': '请输入源表名'})
        return attrs


class DataIntegrationTaskUpdateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=128, required=False)
    sourceDataSourceId = serializers.IntegerField(required=False)
    targetDataSourceId = serializers.IntegerField(required=False)
    sourceDatabaseName = serializers.CharField(required=False, allow_blank=True)
    sourceTableName = serializers.CharField(max_length=256, required=False)
    targetSchemaName = serializers.CharField(required=False, allow_blank=True)
    targetTableName = serializers.CharField(max_length=128, required=False)
    loadType = serializers.ChoiceField(choices=['full', 'incremental'], required=False)
    writeMode = serializers.ChoiceField(choices=['overwrite', 'append', 'upsert'], required=False)
    executorType = serializers.ChoiceField(choices=['mock', 'datax'], required=False)
    status = serializers.ChoiceField(choices=['draft', 'active', 'paused', 'archived'], required=False)
    scheduleType = serializers.ChoiceField(choices=['manual', 'cron'], required=False)
    cronExpression = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.CharField(required=False, allow_blank=True)
    taskConfig = serializers.JSONField(required=False)
    remark = serializers.CharField(required=False, allow_blank=True)

    def validate_sourceDataSourceId(self, value):
        if not DataSource.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源数据源不存在')
        return value

    def validate_targetDataSourceId(self, value):
        if not DataSource.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('目标数据源不存在')
        return value

    def validate(self, attrs):
        instance = self.context['instance']
        source_ds_id = attrs.get('sourceDataSourceId', instance.source_datasource_id)
        target_ds_id = attrs.get('targetDataSourceId', instance.target_datasource_id)
        source_table_name = attrs.get('sourceTableName', instance.source_table_name)
        schedule_type = attrs.get('scheduleType', instance.schedule_type)
        cron_expression = attrs.get('cronExpression', instance.cron_expression)
        if source_ds_id and target_ds_id and source_ds_id == target_ds_id:
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if schedule_type == 'cron' and not cron_expression:
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        if not str(source_table_name or '').strip():
            raise serializers.ValidationError({'sourceTableName': '请输入源表名'})
        return attrs


class DataIntegrationTaskQuerySerializer(serializers.Serializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    executorType = serializers.CharField(required=False, allow_blank=True)
    sourceDataSourceId = serializers.IntegerField(required=False)
    targetDataSourceId = serializers.IntegerField(required=False)


class DataIntegrationTaskValidateSerializer(DataIntegrationTaskCreateSerializer):
    taskId = serializers.IntegerField(required=False, allow_null=True)

    def validate_taskCode(self, value):
        task_id = self.initial_data.get('taskId')
        queryset = DataIntegrationTask.objects.filter(task_code=value, del_flag='0')
        if task_id:
            queryset = queryset.exclude(id=task_id)
        if queryset.exists():
            raise serializers.ValidationError('任务编码已存在')
        return value


class DataIntegrationExecutionSerializer(serializers.ModelSerializer):
    taskInstanceId = serializers.IntegerField(source='id', read_only=True)
    instanceId = serializers.CharField(source='instance_id', read_only=True)
    triggerMode = serializers.CharField(source='trigger_mode', read_only=True)
    triggeredBy = serializers.CharField(source='triggered_by', read_only=True)
    executorType = serializers.CharField(source='executor_type', read_only=True)
    startedAt = serializers.DateTimeField(source='started_at', read_only=True, format='%Y-%m-%d %H:%M:%S')
    finishedAt = serializers.DateTimeField(source='finished_at', read_only=True, format='%Y-%m-%d %H:%M:%S')
    durationSeconds = serializers.IntegerField(source='duration_seconds', read_only=True)
    errorMessage = serializers.CharField(source='error_message', read_only=True)
    runtimeConfig = serializers.JSONField(source='runtime_config', read_only=True)
    resultSummary = serializers.JSONField(source='result_summary', read_only=True)
    rawOutput = serializers.SerializerMethodField()
    createTime = serializers.DateTimeField(source='create_time', read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = TaskInstance
        fields = [
            'taskInstanceId',
            'instanceId',
            'status',
            'triggerMode',
            'triggeredBy',
            'executorType',
            'startedAt',
            'finishedAt',
            'durationSeconds',
            'errorMessage',
            'runtimeConfig',
            'resultSummary',
            'rawOutput',
            'createTime',
        ]

    def get_rawOutput(self, obj):
        summary = obj.result_summary or {}
        return (
            summary.get('rawOutput')
            or summary.get('raw_output')
            or summary.get('log_file')
            or obj.error_message
            or ''
        )


class DataIntegrationExecutionLogQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
