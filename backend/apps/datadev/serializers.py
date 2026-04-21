import hashlib

from rest_framework import serializers

from apps.datatask.models import Task
from apps.system.serializers import BaseModelSerializer
from .models import (
    DataDevDirectory,
    DataDevModel,
    DataDevModelField,
    DataDevScript,
    DataDevScriptExecution,
    DataDevScriptVersion,
)


class ScriptListSerializer(BaseModelSerializer):
    """加工作业列表序列化器。"""

    scriptId = serializers.IntegerField(source='id', read_only=True)
    scriptName = serializers.CharField(source='script_name')
    scriptCode = serializers.CharField(source='script_code')
    scriptType = serializers.CharField(source='script_type')
    scriptRole = serializers.CharField(source='script_role')
    engineType = serializers.CharField(source='engine_type')
    datasourceId = serializers.PrimaryKeyRelatedField(source='datasource', read_only=True)
    datasourceName = serializers.CharField(source='datasource.name', read_only=True, default='')
    targetModelId = serializers.IntegerField(source='target_model_id', read_only=True, allow_null=True)
    targetModelName = serializers.CharField(source='target_model.model_name', read_only=True, default='')
    targetLayer = serializers.CharField(source='target_model.layer', read_only=True, default='')
    taskId = serializers.SerializerMethodField()
    taskStatus = serializers.SerializerMethodField()

    class Meta:
        model = DataDevScript
        fields = [
            'scriptId', 'scriptName', 'scriptCode', 'scriptType', 'scriptRole', 'engineType',
            'description', 'status', 'datasourceId', 'datasourceName',
            'targetModelId', 'targetModelName', 'targetLayer', 'taskId', 'taskStatus',
            'tags', 'owner', 'remark',
        ]

    @staticmethod
    def _get_bound_task(obj):
        return Task.objects.filter(
            source_module='datadev.script',
            source_record_id=obj.id,
            del_flag='0',
        ).first()

    def get_taskId(self, obj):
        task = self._get_bound_task(obj)
        return task.id if task else None

    def get_taskStatus(self, obj):
        task = self._get_bound_task(obj)
        return task.status if task else ''


class ScriptCreateSerializer(serializers.Serializer):
    """加工作业创建序列化器。"""

    scriptName = serializers.CharField(max_length=128)
    scriptCode = serializers.CharField(max_length=64)
    scriptType = serializers.ChoiceField(choices=['sql', 'python'], default='sql')
    scriptRole = serializers.ChoiceField(
        choices=[choice[0] for choice in DataDevScript.SCRIPT_ROLE_CHOICES],
        required=False,
    )
    engineType = serializers.ChoiceField(choices=['spark', 'hive', 'mvp'], required=False, default='spark')
    description = serializers.CharField(required=False, allow_blank=True, default='')
    targetModelId = serializers.IntegerField(required=False, allow_null=True, default=None)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    remark = serializers.CharField(required=False, allow_blank=True, default='')
    content = serializers.CharField(required=False, allow_blank=True, default='')


class ScriptUpdateSerializer(serializers.Serializer):
    """加工作业更新序列化器。"""

    scriptName = serializers.CharField(max_length=128, required=False)
    scriptType = serializers.ChoiceField(choices=['sql', 'python'], required=False)
    scriptRole = serializers.ChoiceField(
        choices=[choice[0] for choice in DataDevScript.SCRIPT_ROLE_CHOICES],
        required=False,
    )
    engineType = serializers.ChoiceField(choices=['spark', 'hive', 'mvp'], required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['draft', 'published', 'archived'], required=False)
    targetModelId = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    remark = serializers.CharField(required=False, allow_blank=True)


class ScriptQuerySerializer(serializers.Serializer):
    """加工作业查询序列化器。"""

    scriptName = serializers.CharField(required=False, allow_blank=True)
    scriptType = serializers.ChoiceField(required=False, choices=['sql', 'python'])
    scriptRole = serializers.ChoiceField(
        required=False,
        choices=[choice[0] for choice in DataDevScript.SCRIPT_ROLE_CHOICES],
    )
    status = serializers.ChoiceField(required=False, choices=['draft', 'published', 'archived'])
    targetModelId = serializers.IntegerField(required=False, allow_null=True)


class ScriptVersionSerializer(serializers.ModelSerializer):
    """作业版本序列化器。"""

    versionId = serializers.IntegerField(source='id', read_only=True)
    scriptId = serializers.IntegerField(source='script_id', read_only=True)
    versionNumber = serializers.IntegerField(source='version_number', read_only=True)
    contentHash = serializers.CharField(source='content_hash', read_only=True)
    changeLog = serializers.CharField(source='change_log', read_only=True)
    isCurrent = serializers.BooleanField(source='is_current', read_only=True)
    isReleased = serializers.BooleanField(source='is_released', read_only=True)
    createBy = serializers.CharField(source='create_by', read_only=True)
    createTime = serializers.DateTimeField(source='create_time', read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = DataDevScriptVersion
        fields = [
            'versionId', 'scriptId', 'versionNumber', 'content',
            'contentHash', 'changeLog', 'isCurrent', 'isReleased', 'createBy', 'createTime',
        ]


class ScriptVersionCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    changeLog = serializers.CharField(required=False, allow_blank=True, default='')
    isReleased = serializers.BooleanField(required=False, default=False)


class ScriptExecutionSerializer(serializers.ModelSerializer):
    taskId = serializers.IntegerField(source='task_instance.task_id', read_only=True, allow_null=True)
    taskInstanceId = serializers.IntegerField(source='task_instance_id', read_only=True, allow_null=True)
    executionId = serializers.CharField(source='execution_id', read_only=True)
    scriptId = serializers.IntegerField(source='script_id', read_only=True)
    scriptName = serializers.CharField(source='script.script_name', read_only=True, default='')
    versionNumber = serializers.IntegerField(source='version.version_number', read_only=True, default=None)
    executorType = serializers.CharField(source='executor_type', read_only=True)
    executorParams = serializers.JSONField(source='executor_params', read_only=True)
    startTime = serializers.DateTimeField(source='start_time', read_only=True, format='%Y-%m-%d %H:%M:%S')
    endTime = serializers.DateTimeField(source='end_time', read_only=True, format='%Y-%m-%d %H:%M:%S')
    durationSeconds = serializers.IntegerField(source='duration_seconds', read_only=True)
    resultSummary = serializers.JSONField(source='result_summary', read_only=True)
    errorMessage = serializers.CharField(source='error_message', read_only=True)
    executedBy = serializers.CharField(source='executed_by', read_only=True)
    createTime = serializers.DateTimeField(source='create_time', read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = DataDevScriptExecution
        fields = [
            'taskId', 'taskInstanceId',
            'executionId', 'scriptId', 'scriptName', 'status',
            'versionNumber', 'executorType', 'executorParams',
            'startTime', 'endTime', 'durationSeconds',
            'resultSummary', 'errorMessage', 'executedBy', 'createTime',
        ]


class ScriptExecutionQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        required=False,
        choices=['pending', 'running', 'success', 'failed', 'cancelled'],
    )
    executedBy = serializers.CharField(required=False, allow_blank=True)


class DataDevDirectorySerializer(BaseModelSerializer):
    directoryId = serializers.IntegerField(source='directory_id', read_only=True)
    parentId = serializers.IntegerField(source='parent_id', read_only=True)
    directoryName = serializers.CharField(source='directory_name', read_only=True)
    directoryCode = serializers.CharField(source='directory_code', read_only=True)
    orderNum = serializers.IntegerField(source='order_num', read_only=True)

    class Meta:
        model = DataDevDirectory
        fields = [
            'directoryId', 'parentId', 'ancestors',
            'directoryName', 'directoryCode', 'orderNum',
        ]


class DataDevDirectoryCreateSerializer(serializers.Serializer):
    parentId = serializers.IntegerField(default=0)
    directoryName = serializers.CharField(max_length=100)
    directoryCode = serializers.CharField(max_length=32)
    orderNum = serializers.IntegerField(default=0)
    status = serializers.ChoiceField(choices=['0', '1'], default='0')
    remark = serializers.CharField(required=False, allow_blank=True, default='')


class DataDevDirectoryUpdateSerializer(serializers.Serializer):
    parentId = serializers.IntegerField(required=False)
    directoryName = serializers.CharField(max_length=100, required=False)
    directoryCode = serializers.CharField(max_length=32, required=False)
    orderNum = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=['0', '1'], required=False)
    remark = serializers.CharField(required=False, allow_blank=True)


class DataModelFieldPayloadSerializer(serializers.Serializer):
    fieldId = serializers.IntegerField(required=False)
    fieldName = serializers.CharField(max_length=128)
    fieldType = serializers.CharField(max_length=64)
    fieldComment = serializers.CharField(max_length=512)
    isNullable = serializers.BooleanField(required=False, default=True)
    ordinalPosition = serializers.IntegerField(required=False, default=1)


class DataModelFieldSerializer(BaseModelSerializer):
    fieldId = serializers.IntegerField(source='id', read_only=True)
    fieldName = serializers.CharField(source='field_name')
    fieldType = serializers.CharField(source='field_type')
    fieldComment = serializers.CharField(source='field_comment')
    isNullable = serializers.BooleanField(source='is_nullable')
    ordinalPosition = serializers.IntegerField(source='ordinal_position')

    class Meta:
        model = DataDevModelField
        fields = ['fieldId', 'fieldName', 'fieldType', 'fieldComment', 'isNullable', 'ordinalPosition']


class DataModelListSerializer(BaseModelSerializer):
    modelId = serializers.IntegerField(source='id', read_only=True)
    modelName = serializers.CharField(source='model_name')
    modelCode = serializers.CharField(source='model_code')
    layer = serializers.CharField()
    tableName = serializers.CharField(source='table_name')
    schemaName = serializers.CharField(source='schema_name')
    tableComment = serializers.CharField(source='table_comment')
    engineType = serializers.CharField(source='engine_type')
    owner = serializers.CharField()
    description = serializers.CharField()
    fieldCount = serializers.SerializerMethodField()

    class Meta:
        model = DataDevModel
        fields = [
            'modelId', 'modelName', 'modelCode', 'layer', 'tableName', 'schemaName',
            'tableComment', 'engineType', 'owner', 'description', 'status', 'fieldCount',
            'remark', 'createBy', 'updateBy', 'createTime', 'updateTime',
        ]

    def get_fieldCount(self, obj):
        prefetched = getattr(obj, 'active_field_count', None)
        if prefetched is not None:
            return prefetched
        return obj.model_fields.filter(del_flag='0').count()


class DataModelDetailSerializer(DataModelListSerializer):
    fields = DataModelFieldSerializer(source='model_fields', many=True, read_only=True)

    class Meta(DataModelListSerializer.Meta):
        fields = DataModelListSerializer.Meta.fields + ['fields']


class DataModelCreateUpdateSerializer(serializers.Serializer):
    modelName = serializers.CharField(max_length=128)
    modelCode = serializers.CharField(max_length=64)
    layer = serializers.ChoiceField(choices=['ODS', 'DWD', 'DWS', 'ADS'])
    tableName = serializers.CharField(max_length=255)
    schemaName = serializers.CharField(required=False, allow_blank=True, default='')
    tableComment = serializers.CharField(max_length=1024)
    engineType = serializers.ChoiceField(choices=['spark', 'hive'], default='spark')
    owner = serializers.CharField(max_length=64)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    remark = serializers.CharField(required=False, allow_blank=True, default='')
    fields = DataModelFieldPayloadSerializer(many=True, allow_empty=False)


class DataModelQuerySerializer(serializers.Serializer):
    modelName = serializers.CharField(required=False, allow_blank=True)
    layer = serializers.ChoiceField(required=False, choices=['ODS', 'DWD', 'DWS', 'ADS'])
    status = serializers.ChoiceField(required=False, choices=['draft', 'deployed'])
