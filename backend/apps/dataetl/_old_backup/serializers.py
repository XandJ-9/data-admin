from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer, PaginationQuerySerializer
from .models import IntegrationTask, IntegrationTaskVersion, TaskExecutionLog, DataLineage


class IntegrationTaskSerializer(BaseModelSerializer):
    """ETL任务序列化器"""
    taskId = serializers.IntegerField(source='id', read_only=True)
    taskName = serializers.CharField(source='name')
    taskType = serializers.CharField(source='type')

    # 新增字段
    targetLayer = serializers.CharField(source='target_layer')
    executorType = serializers.CharField(source='executor_type')

    # 数据源配置
    sourceDatasourceId = serializers.IntegerField(source='source_datasource.id', read_only=True)
    sourceDatasourceName = serializers.CharField(source='source_datasource.name', read_only=True)
    sourceTable = serializers.CharField(source='source_table')
    sourceFilter = serializers.CharField(source='source_filter')

    # 【5000+租户优化】多库采集配置
    isMultiDbTask = serializers.BooleanField(source='is_multi_db_task')
    sourceDatabases = serializers.JSONField(source='source_databases')
    tenantIdField = serializers.CharField(source='tenant_id_field')

    # 目标配置
    targetDatasourceId = serializers.IntegerField(source='target_datasource.id', read_only=True)
    targetDatasourceName = serializers.CharField(source='target_datasource.name', read_only=True)
    targetTable = serializers.CharField(source='target_table')
    targetPartition = serializers.JSONField(source='target_partition')

    # 增量策略
    incrementalStrategy = serializers.CharField(source='incremental_strategy')
    incrementalField = serializers.CharField(source='incremental_field')

    # 字段映射
    fieldMapping = serializers.JSONField(source='field_mapping')

    # 执行配置
    batchSize = serializers.IntegerField(source='batch_size')
    concurrency = serializers.IntegerField(source='concurrency')

    # 预处理SQL
    preSql = serializers.CharField(source='pre_sql', required=False, allow_blank=True)
    postSql = serializers.CharField(source='post_sql', required=False, allow_blank=True)

    # DataX配置 (JSON字段,用于存储各种配置)
    dataxConfig = serializers.JSONField(source='datax_config', required=False)

    # 【场景3优化】SQL脚本和变量配置 (从dataxConfig中提取,便于前端使用)
    sqlScript = serializers.CharField(source='datax_config.sql_script', required=False, allow_blank=True)
    variables = serializers.JSONField(source='datax_config.variables', required=False)

    # 原有字段
    schedule = serializers.JSONField(required=False)
    detail = serializers.JSONField(required=False)
    status = serializers.CharField(required=False)
    remark = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = IntegrationTask
        fields = [
            'taskId', 'taskName', 'taskType',
            'targetLayer', 'executorType',
            'sourceDatasourceId', 'sourceDatasourceName', 'sourceTable', 'sourceFilter',
            'isMultiDbTask', 'sourceDatabases', 'tenantIdField',
            'targetDatasourceId', 'targetDatasourceName', 'targetTable', 'targetPartition',
            'incrementalStrategy', 'incrementalField',
            'fieldMapping',
            'batchSize', 'concurrency',
            'preSql', 'postSql',
            'dataxConfig', 'sqlScript', 'variables',
            'schedule', 'detail', 'status', 'remark'
        ]


class IntegrationTaskQuerySerializer(PaginationQuerySerializer):
    taskName = serializers.CharField(required=False, allow_blank=True)
    taskType = serializers.ChoiceField(required=False, choices=['dbToDb', 'dbToHive', 'hiveToDb'])
    status = serializers.ChoiceField(required=False, choices=['0', '1'])
    targetLayer = serializers.CharField(required=False)
    executorType = serializers.CharField(required=False)


class IntegrationTaskCreateSerializer(IntegrationTaskSerializer):
    """创建任务序列化器"""
    sourceDatasourceId = serializers.IntegerField(write_only=True, required=False)
    targetDatasourceId = serializers.IntegerField(write_only=True, required=False)


class IntegrationTaskUpdateSerializer(IntegrationTaskCreateSerializer):
    """更新任务序列化器"""
    taskId = serializers.IntegerField()


# ==================== 新增序列化器 ====================

class TaskExecutionLogSerializer(BaseModelSerializer):
    """任务执行日志序列化器"""
    executionId = serializers.CharField(source='execution_id', read_only=True)
    taskId = serializers.IntegerField(source='task.id', read_only=True)
    taskName = serializers.CharField(source='task.name', read_only=True)
    statusDisplay = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TaskExecutionLog
        fields = [
            'id', 'executionId', 'taskId', 'taskName',
            'status', 'statusDisplay',
            'startTime', 'endTime', 'durationSeconds',
            'rowsRead', 'rowsWritten', 'rowsError', 'bytesTransferred',
            'logPath', 'errorMessage',
            'triggeredBy', 'createTime'
        ]


class TaskExecutionLogQuerySerializer(PaginationQuerySerializer):
    """执行日志查询序列化器"""
    taskId = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)


class DataLineageSerializer(BaseModelSerializer):
    """数据血缘序列化器"""
    taskId = serializers.IntegerField(source='source_task.id', read_only=True)
    taskName = serializers.CharField(source='source_task.name', read_only=True)

    class Meta:
        model = DataLineage
        fields = [
            'id', 'taskId', 'taskName',
            'lineageType', 'sourceDatasource', 'sourceTable', 'sourceField',
            'targetDatasource', 'targetTable', 'targetField',
            'transformRule', 'createTime'
        ]


class DataLineageQuerySerializer(PaginationQuerySerializer):
    """血缘查询序列化器"""
    table = serializers.CharField(required=False)
    direction = serializers.ChoiceField(required=False, choices=['upstream', 'downstream'])


class IntegrationTaskVersionSerializer(BaseModelSerializer):
    """任务版本管理序列化器"""
    taskId = serializers.IntegerField(source='task.id', read_only=True)
    taskName = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = IntegrationTaskVersion
        fields = [
            'id', 'taskId', 'taskName',
            'version', 'configSnapshot', 'changeLog',
            'isActive', 'createTime'
        ]

