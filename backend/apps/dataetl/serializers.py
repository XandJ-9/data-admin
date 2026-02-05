"""
ETL Serializers

This module defines serializers for ETL task management.
"""

from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import ETLTask, ETLTaskVersion, ETLFieldMapping, ETLExecutionLog


# ==================== ETLTask Serializers ====================

class ETLTaskSerializer(BaseModelSerializer):
    """ETL任务序列化器（列表/详情）"""
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='task_name')
    taskCode = serializers.CharField(source='task_code')
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    etlType = serializers.CharField(source='etl_type')
    executorType = serializers.CharField(source='executor_type')
    executeStrategy = serializers.CharField(source='execute_strategy')
    sourceDatasourceId = serializers.IntegerField(source='source_datasource_id')
    sourceDatasourceName = serializers.CharField(
        source='source_datasource.name',
        read_only=True,
        required=False
    )
    targetDatasourceId = serializers.IntegerField(source='target_datasource_id')
    targetDatasourceName = serializers.CharField(
        source='target_datasource.name',
        read_only=True,
        required=False
    )
    sourceTableId = serializers.IntegerField(source='source_table_id', required=False, allow_null=True)
    sourceTableName = serializers.CharField(
        source='source_table.table_name',
        read_only=True,
        required=False
    )
    targetTable = serializers.CharField(source='target_table', required=False, allow_blank=True, allow_null=True)
    sqlConfig = serializers.CharField(source='sql_config', required=False, allow_blank=True, allow_null=True)
    executorParams = serializers.JSONField(source='executor_params', required=False)

    class Meta:
        model = ETLTask
        fields = [
            'taskId', 'taskName', 'taskCode', 'description', 'etlType', 'executorType',
            'executeStrategy', 'sourceDatasourceId', 'sourceDatasourceName',
            'targetDatasourceId', 'targetDatasourceName', 'sourceTableId',
            'sourceTableName', 'targetTable', 'sqlConfig', 'executorParams'
        ]


class ETLTaskQuerySerializer(serializers.Serializer):
    """ETL任务查询序列化器"""
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
    """ETL任务创建序列化器"""
    taskName = serializers.CharField(source='task_name', required=True)
    taskCode = serializers.CharField(source='task_code', required=True)
    sourceDatasourceId = serializers.IntegerField(source='source_datasource_id', required=True)
    targetDatasourceId = serializers.IntegerField(source='target_datasource_id', required=True)
    sourceTableId = serializers.IntegerField(source='source_table_id', required=False, allow_null=True)

    def validate_task_code(self, value):
        """验证任务编码唯一性"""
        if ETLTask.objects.filter(task_code=value, del_flag='0').exists():
            raise serializers.ValidationError('任务编码已存在')
        return value

    def create(self, validated_data):
        # 创建任务时，移除嵌套字段
        validated_data.pop('taskId', None)
        return super().create(validated_data)


class ETLTaskUpdateSerializer(ETLTaskSerializer):
    """ETL任务更新序列化器"""
    taskId = serializers.IntegerField(source='id', required=True)

    def validate_task_code(self, value):
        """验证任务编码唯一性（排除自身）"""
        instance = self.instance
        if ETLTask.objects.filter(
            task_code=value,
            del_flag='0'
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError('任务编码已存在')
        return value


# ==================== ETLTaskVersion Serializers ====================

class ETLTaskVersionSerializer(serializers.ModelSerializer):
    """ETL任务版本序列化器"""
    versionId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(
        source='task.task_name',
        read_only=True,
        required=False
    )
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
            'changeLog', 'isCurrent', 'createBy', 'createTime'
        ]


class ETLTaskVersionCreateSerializer(ETLTaskVersionSerializer):
    """ETL任务版本创建序列化器"""
    taskId = serializers.IntegerField(source='task_id', required=True)


# ==================== ETLFieldMapping Serializers ====================

class ETLFieldMappingSerializer(BaseModelSerializer):
    """ETL字段映射序列化器"""
    mappingId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(
        source='task.task_name',
        read_only=True,
        required=False
    )
    sourceFieldName = serializers.CharField(source='source_field_name')
    targetFieldName = serializers.CharField(source='target_field_name')
    transformRule = serializers.CharField(
        source='transform_rule',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    cleanRule = serializers.CharField(
        source='clean_rule',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    dataType = serializers.CharField(
        source='data_type',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    isPrimaryKey = serializers.BooleanField(source='is_primary_key', required=False)
    sortOrder = serializers.IntegerField(source='sort_order', required=False)

    class Meta:
        model = ETLFieldMapping
        fields = [
            'mappingId', 'taskId', 'taskName', 'sourceFieldName', 'targetFieldName',
            'transformRule', 'cleanRule', 'dataType', 'isPrimaryKey', 'sortOrder'
        ]


class ETLFieldMappingQuerySerializer(serializers.Serializer):
    """ETL字段映射查询序列化器"""
    taskId = serializers.IntegerField(required=False)
    sourceFieldName = serializers.CharField(required=False, allow_blank=True)
    targetFieldName = serializers.CharField(required=False, allow_blank=True)


class ETLFieldMappingCreateSerializer(ETLFieldMappingSerializer):
    """ETL字段映射创建序列化器"""
    taskId = serializers.IntegerField(source='task_id', required=True)
    sourceFieldName = serializers.CharField(source='source_field_name', required=True)
    targetFieldName = serializers.CharField(source='target_field_name', required=True)


class ETLFieldMappingUpdateSerializer(ETLFieldMappingSerializer):
    """ETL字段映射更新序列化器"""
    mappingId = serializers.IntegerField(source='id', required=True)


# ==================== ETLExecutionLog Serializers ====================

class ETLExecutionLogSerializer(serializers.ModelSerializer):
    """ETL执行日志序列化器"""
    logId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(
        source='task.task_name',
        read_only=True,
        required=False
    )
    executionId = serializers.CharField(source='execution_id')
    status = serializers.CharField()
    triggerType = serializers.CharField(source='trigger_type')
    startTime = serializers.DateTimeField(
        source='start_time',
        required=False,
        allow_null=True
    )
    endTime = serializers.DateTimeField(
        source='end_time',
        required=False,
        allow_null=True
    )
    durationSeconds = serializers.IntegerField(
        source='duration_seconds',
        required=False,
        allow_null=True
    )
    totalRows = serializers.IntegerField(
        source='total_rows',
        required=False,
        allow_null=True
    )
    successRows = serializers.IntegerField(
        source='success_rows',
        required=False,
        allow_null=True
    )
    failedRows = serializers.IntegerField(
        source='failed_rows',
        required=False,
        allow_null=True
    )
    errorMessage = serializers.CharField(
        source='error_message',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    logFile = serializers.CharField(
        source='log_file',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    executedBy = serializers.CharField(
        source='executed_by',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    executorParams = serializers.JSONField(
        source='executor_params',
        required=False,
        allow_null=True
    )
    createTime = serializers.DateTimeField(source='create_time', read_only=True)

    class Meta:
        model = ETLExecutionLog
        fields = [
            'logId', 'taskId', 'taskName', 'executionId', 'status', 'triggerType',
            'startTime', 'endTime', 'durationSeconds', 'totalRows', 'successRows',
            'failedRows', 'errorMessage', 'logFile', 'executedBy', 'executorParams',
            'createTime'
        ]


class ETLExecutionLogQuerySerializer(serializers.Serializer):
    """ETL执行日志查询序列化器"""
    taskId = serializers.IntegerField(required=False)
    executionId = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    triggerType = serializers.CharField(required=False, allow_blank=True)
    executedBy = serializers.CharField(required=False, allow_blank=True)
    createTimeStart = serializers.DateTimeField(required=False)
    createTimeEnd = serializers.DateTimeField(required=False)


class ETLExecutionLogCreateSerializer(ETLExecutionLogSerializer):
    """ETL执行日志创建序列化器"""
    taskId = serializers.IntegerField(source='task_id', required=True)
    executionId = serializers.CharField(source='execution_id', required=True)


# ==================== Simple Serializers for Dropdowns ====================

class ETLTaskSimpleSerializer(serializers.Serializer):
    """ETL任务简单序列化器（用于下拉框）"""
    taskId = serializers.IntegerField(source='id')
    taskName = serializers.CharField(source='task_name')
    taskCode = serializers.CharField(source='task_code')
