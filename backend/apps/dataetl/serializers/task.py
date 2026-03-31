from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from ..models import ETLTask


class ETLTaskSerializer(BaseModelSerializer):
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='task_name')
    taskCode = serializers.CharField(source='task_code')
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    etlType = serializers.CharField(source='etl_type')
    executorType = serializers.CharField(source='executor_type')
    executeStrategy = serializers.CharField(source='execute_strategy')
    sourceDatasourceId = serializers.IntegerField(source='source_datasource_id')
    sourceDatasourceName = serializers.CharField(
        source='source_datasource.name', read_only=True, required=False
    )
    targetDatasourceId = serializers.IntegerField(source='target_datasource_id')
    targetDatasourceName = serializers.CharField(
        source='target_datasource.name', read_only=True, required=False
    )
    sourceTableId = serializers.IntegerField(source='source_table_id', required=False, allow_null=True)
    sourceTableName = serializers.CharField(source='source_table_name', required=False, allow_blank=True, allow_null=True)
    sourceDatabaseName = serializers.CharField(source='source_database_name', required=False, allow_blank=True, allow_null=True)
    targetTable = serializers.CharField(source='target_table', required=False, allow_blank=True, allow_null=True)
    sqlConfig = serializers.CharField(source='sql_config', required=False, allow_blank=True, allow_null=True)
    executorParams = serializers.JSONField(source='executor_params', required=False, allow_null=True)

    class Meta:
        model = ETLTask
        fields = [
            'taskId', 'taskName', 'taskCode', 'description', 'etlType', 'executorType',
            'executeStrategy', 'sourceDatasourceId', 'sourceDatasourceName',
            'targetDatasourceId', 'targetDatasourceName', 'sourceTableId',
            'sourceTableName', 'sourceDatabaseName', 'targetTable', 'sqlConfig', 'executorParams',
        ]


class ETLTaskQuerySerializer(serializers.Serializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    taskCode = serializers.CharField(required=False, allow_blank=True)
    etlType = serializers.CharField(required=False, allow_blank=True)
    executorType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0', '1'])
    sourceDatasourceId = serializers.IntegerField(required=False)
    targetDatasourceId = serializers.IntegerField(required=False)
    createTimeStart = serializers.DateTimeField(required=False)
    createTimeEnd = serializers.DateTimeField(required=False)


class ETLTaskCreateSerializer(ETLTaskSerializer):
    taskName = serializers.CharField(source='task_name', required=True)
    taskCode = serializers.CharField(source='task_code', required=True)
    sourceDatasourceId = serializers.IntegerField(source='source_datasource_id', required=True)
    targetDatasourceId = serializers.IntegerField(source='target_datasource_id', required=True)
    sourceTableId = serializers.IntegerField(source='source_table_id', required=False, allow_null=True)

    def validate_task_code(self, value):
        if ETLTask.objects.filter(task_code=value, del_flag='0').exists():
            raise serializers.ValidationError('任务编码已存在')
        return value

    def create(self, validated_data):
        validated_data.pop('taskId', None)
        return super().create(validated_data)


class ETLTaskUpdateSerializer(ETLTaskSerializer):
    taskId = serializers.IntegerField(source='id', required=True)

    def validate_task_code(self, value):
        if ETLTask.objects.filter(
            task_code=value, del_flag='0'
        ).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError('任务编码已存在')
        return value


class ETLTaskSimpleSerializer(serializers.Serializer):
    taskId = serializers.IntegerField(source='id')
    taskName = serializers.CharField(source='task_name')
    taskCode = serializers.CharField(source='task_code')
