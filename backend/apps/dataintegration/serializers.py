from rest_framework import serializers

from apps.datatask.models import TaskInstance
from apps.datasource.models import DataSource, SourceTableSnapshot
from apps.system.serializers import BaseModelSerializer

from .models import DataIntegrationTask


class SourceTableOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    objectName = serializers.CharField(source='table_name', read_only=True)
    tableName = serializers.CharField(source='table_name', read_only=True)
    databaseName = serializers.CharField(source='database_name', read_only=True)
    tableComment = serializers.CharField(source='table_comment', read_only=True)


class DataIntegrationTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='task_name', read_only=True)
    taskCode = serializers.CharField(source='task_code', read_only=True)
    sourceDataSourceId = serializers.IntegerField(source='source_datasource_id', read_only=True)
    sourceDataSourceName = serializers.CharField(source='source_datasource.name', read_only=True)
    targetDataSourceId = serializers.IntegerField(source='target_datasource_id', read_only=True)
    targetDataSourceName = serializers.CharField(source='target_datasource.name', read_only=True)
    sourceTableId = serializers.IntegerField(source='source_table_snapshot_id', read_only=True, allow_null=True)
    sourceTableName = serializers.SerializerMethodField()
    sourceDatabaseName = serializers.SerializerMethodField()
    targetSchemaName = serializers.CharField(source='target_schema_name', read_only=True)
    targetTableName = serializers.CharField(source='target_table_name', read_only=True)
    loadType = serializers.CharField(source='load_type', read_only=True)
    writeMode = serializers.CharField(source='write_mode', read_only=True)
    executorType = serializers.CharField(source='executor_type', read_only=True)
    scheduleType = serializers.CharField(source='schedule_type', read_only=True)
    cronExpression = serializers.CharField(source='cron_expression', read_only=True)
    taskConfig = serializers.JSONField(source='task_config', read_only=True)

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
            'sourceTableId',
            'sourceTableName',
            'sourceDatabaseName',
            'targetSchemaName',
            'targetTableName',
            'loadType',
            'writeMode',
            'executorType',
            'scheduleType',
            'cronExpression',
            'owner',
            'taskConfig',
            'remark',
        ]

    def get_sourceTableName(self, obj):
        if obj.source_table_snapshot_id and obj.source_table_snapshot is not None:
            return obj.source_table_snapshot.table_name
        return obj.source_table_name

    def get_sourceDatabaseName(self, obj):
        if obj.source_table_snapshot_id and obj.source_table_snapshot is not None:
            return obj.source_table_snapshot.database_name
        return obj.source_database_name


class DataIntegrationTaskCreateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=128)
    taskCode = serializers.CharField(max_length=128)
    sourceDataSourceId = serializers.IntegerField()
    targetDataSourceId = serializers.IntegerField()
    sourceTableId = serializers.IntegerField(required=False, allow_null=True, default=None)
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

    def validate_sourceTableId(self, value):
        if value is None:
            return value
        if not SourceTableSnapshot.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源表不存在')
        return value

    def validate(self, attrs):
        if attrs['sourceDataSourceId'] == attrs['targetDataSourceId']:
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if attrs['scheduleType'] == 'cron' and not attrs.get('cronExpression'):
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        source_table_id = attrs.get('sourceTableId')
        if source_table_id is not None:
            source_table = SourceTableSnapshot.objects.filter(id=source_table_id, del_flag='0').first()
            if source_table is not None and source_table.data_source_id != attrs['sourceDataSourceId']:
                raise serializers.ValidationError({'sourceTableId': '源表不属于当前源数据源'})
        return attrs


class DataIntegrationTaskUpdateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=128, required=False)
    sourceDataSourceId = serializers.IntegerField(required=False)
    targetDataSourceId = serializers.IntegerField(required=False)
    sourceTableId = serializers.IntegerField(required=False, allow_null=True)
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

    def validate_sourceTableId(self, value):
        if value is None:
            return value
        if not SourceTableSnapshot.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源表不存在')
        return value

    def validate(self, attrs):
        instance = self.context['instance']
        source_ds_id = attrs.get('sourceDataSourceId', instance.source_datasource_id)
        target_ds_id = attrs.get('targetDataSourceId', instance.target_datasource_id)
        source_table_id = attrs.get('sourceTableId', instance.source_table_snapshot_id)
        schedule_type = attrs.get('scheduleType', instance.schedule_type)
        cron_expression = attrs.get('cronExpression', instance.cron_expression)
        if source_ds_id == target_ds_id:
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if schedule_type == 'cron' and not cron_expression:
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        if source_table_id is not None:
            source_table = SourceTableSnapshot.objects.filter(id=source_table_id, del_flag='0').first()
            if source_table is not None and source_table.data_source_id != source_ds_id:
                raise serializers.ValidationError({'sourceTableId': '源表不属于当前源数据源'})
        return attrs


class DataIntegrationTaskQuerySerializer(serializers.Serializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    executorType = serializers.CharField(required=False, allow_blank=True)
    sourceDataSourceId = serializers.IntegerField(required=False)
    targetDataSourceId = serializers.IntegerField(required=False)


class SourceTableQuerySerializer(serializers.Serializer):
    sourceDataSourceId = serializers.IntegerField()


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
