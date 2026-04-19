from rest_framework import serializers

from apps.dataasset.models import DataAsset
from apps.datasource.models import DataSource
from apps.datatask.models import TaskInstance
from apps.datatask.serializers import TaskInstanceSerializer
from apps.system.serializers import BaseModelSerializer

from .models import DataIntegrationTask


class DataIntegrationTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='task_name', read_only=True)
    taskCode = serializers.CharField(source='task_code', read_only=True)
    sourceDataSourceId = serializers.IntegerField(source='source_datasource_id', read_only=True)
    sourceDataSourceName = serializers.CharField(source='source_datasource.name', read_only=True)
    targetDataSourceId = serializers.IntegerField(source='target_datasource_id', read_only=True)
    targetDataSourceName = serializers.CharField(source='target_datasource.name', read_only=True)
    sourceAssetId = serializers.IntegerField(source='source_asset_id', read_only=True, allow_null=True)
    sourceTableName = serializers.CharField(source='source_asset.object_name', read_only=True, default='')
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
            'sourceAssetId',
            'sourceTableName',
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


class DataIntegrationTaskCreateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=128)
    taskCode = serializers.CharField(max_length=128)
    sourceDataSourceId = serializers.IntegerField()
    targetDataSourceId = serializers.IntegerField()
    sourceAssetId = serializers.IntegerField(required=False, allow_null=True, default=None)
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
        if DataIntegrationTask.objects.filter(task_code=value).exists():
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

    def validate_sourceAssetId(self, value):
        if value is None:
            return value
        if not DataAsset.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源资产不存在')
        return value

    def validate(self, attrs):
        if attrs['sourceDataSourceId'] == attrs['targetDataSourceId']:
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if attrs['scheduleType'] == 'cron' and not attrs.get('cronExpression'):
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        source_asset_id = attrs.get('sourceAssetId')
        if source_asset_id is not None:
            source_asset = DataAsset.objects.filter(id=source_asset_id, del_flag='0').first()
            if source_asset is not None and source_asset.namespace.data_source_id != attrs['sourceDataSourceId']:
                raise serializers.ValidationError({'sourceAssetId': '源资产不属于当前源数据源'})
        return attrs


class DataIntegrationTaskUpdateSerializer(serializers.Serializer):
    taskName = serializers.CharField(max_length=128, required=False)
    sourceDataSourceId = serializers.IntegerField(required=False)
    targetDataSourceId = serializers.IntegerField(required=False)
    sourceAssetId = serializers.IntegerField(required=False, allow_null=True)
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

    def validate_sourceAssetId(self, value):
        if value is None:
            return value
        if not DataAsset.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源资产不存在')
        return value

    def validate(self, attrs):
        instance = self.context.get('instance')
        source_datasource_id = attrs.get(
            'sourceDataSourceId',
            instance.source_datasource_id if instance is not None else None,
        )
        target_datasource_id = attrs.get(
            'targetDataSourceId',
            instance.target_datasource_id if instance is not None else None,
        )
        schedule_type = attrs.get(
            'scheduleType',
            instance.schedule_type if instance is not None else 'manual',
        )
        cron_expression = attrs.get(
            'cronExpression',
            instance.cron_expression if instance is not None else '',
        )
        executor_type = attrs.get(
            'executorType',
            instance.executor_type if instance is not None else 'mock',
        )
        source_asset_id = attrs.get(
            'sourceAssetId',
            instance.source_asset_id if instance is not None else None,
        )
        if (
            source_datasource_id is not None
            and target_datasource_id is not None
            and source_datasource_id == target_datasource_id
        ):
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if schedule_type == 'cron' and not cron_expression:
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        if source_asset_id is not None and source_datasource_id is not None:
            source_asset = DataAsset.objects.filter(id=source_asset_id, del_flag='0').first()
            if source_asset is not None and source_asset.namespace.data_source_id != source_datasource_id:
                raise serializers.ValidationError({'sourceAssetId': '源资产不属于当前源数据源'})
        return attrs


class DataIntegrationTaskQuerySerializer(serializers.Serializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['draft', 'active', 'paused', 'archived'])
    executorType = serializers.ChoiceField(required=False, choices=['mock', 'datax'])
    sourceDataSourceId = serializers.IntegerField(required=False)
    targetDataSourceId = serializers.IntegerField(required=False)


class DataIntegrationTaskValidateSerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    taskName = serializers.CharField(max_length=128)
    taskCode = serializers.CharField(max_length=128)
    sourceDataSourceId = serializers.IntegerField()
    targetDataSourceId = serializers.IntegerField()
    sourceAssetId = serializers.IntegerField(required=False, allow_null=True, default=None)
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

    def validate_taskId(self, value):
        if not DataIntegrationTask.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('任务不存在')
        return value

    def validate_taskCode(self, value):
        task_id = self.initial_data.get('taskId')
        queryset = DataIntegrationTask.objects.filter(task_code=value)
        if task_id not in (None, ''):
            queryset = queryset.exclude(id=task_id)
        if queryset.exists():
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

    def validate_sourceAssetId(self, value):
        if value is None:
            return value
        if not DataAsset.objects.filter(id=value, del_flag='0').exists():
            raise serializers.ValidationError('源资产不存在')
        return value

    def validate(self, attrs):
        if attrs['sourceDataSourceId'] == attrs['targetDataSourceId']:
            raise serializers.ValidationError({'targetDataSourceId': '源数据源和目标数据源不能相同'})
        if attrs['scheduleType'] == 'cron' and not attrs.get('cronExpression'):
            raise serializers.ValidationError({'cronExpression': '定时调度模式必须配置 Cron 表达式'})
        source_asset_id = attrs.get('sourceAssetId')
        if source_asset_id is not None:
            source_asset = DataAsset.objects.filter(id=source_asset_id, del_flag='0').first()
            if source_asset is not None and source_asset.namespace.data_source_id != attrs['sourceDataSourceId']:
                raise serializers.ValidationError({'sourceAssetId': '源资产不属于当前源数据源'})
        return attrs


class DataIntegrationExecutionLogSerializer(TaskInstanceSerializer):
    integrationTaskId = serializers.IntegerField(source='task.source_record_id', read_only=True)

    class Meta(TaskInstanceSerializer.Meta):
        fields = ['integrationTaskId'] + TaskInstanceSerializer.Meta.fields


class DataIntegrationExecutionLogQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        required=False,
        choices=['pending', 'running', 'success', 'failed', 'cancelled'],
    )


class DataIntegrationExecutionDetailSerializer(TaskInstanceSerializer):
    integrationTaskId = serializers.IntegerField(source='task.source_record_id', read_only=True)

    class Meta(TaskInstanceSerializer.Meta):
        fields = ['integrationTaskId'] + TaskInstanceSerializer.Meta.fields
