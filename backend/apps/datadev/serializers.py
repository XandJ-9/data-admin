import hashlib

from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import DataDevScript, DataDevScriptVersion, DataDevScriptExecution, DataDevDirectory


# ── Script ──────────────────────────────────────

class ScriptListSerializer(BaseModelSerializer):
    """脚本列表序列化器"""
    scriptId = serializers.IntegerField(source='id', read_only=True)
    scriptName = serializers.CharField(source='script_name')
    scriptCode = serializers.CharField(source='script_code')
    scriptType = serializers.CharField(source='script_type')
    datasourceId = serializers.PrimaryKeyRelatedField(
        source='datasource', read_only=True
    )
    datasourceName = serializers.CharField(
        source='datasource.name', read_only=True, default=''
    )
    directoryId = serializers.IntegerField(
        source='directory_id', read_only=True, allow_null=True
    )
    directoryName = serializers.CharField(
        source='directory.directory_name', read_only=True, default=''
    )

    class Meta:
        model = DataDevScript
        fields = [
            'scriptId', 'scriptName', 'scriptCode', 'scriptType',
            'description', 'status', 'datasourceId', 'datasourceName',
            'directoryId', 'directoryName',
            'tags', 'owner', 'remark',
        ]


class ScriptCreateSerializer(serializers.Serializer):
    """脚本创建序列化器"""
    scriptName = serializers.CharField(max_length=128)
    scriptCode = serializers.CharField(max_length=64)
    scriptType = serializers.ChoiceField(choices=['sql', 'python'], default='sql')
    description = serializers.CharField(required=False, allow_blank=True, default='')
    directoryId = serializers.IntegerField(required=False, allow_null=True, default=None)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    remark = serializers.CharField(required=False, allow_blank=True, default='')
    content = serializers.CharField(required=False, allow_blank=True, default='')


class ScriptUpdateSerializer(serializers.Serializer):
    """脚本更新序列化器"""
    scriptName = serializers.CharField(max_length=128, required=False)
    scriptType = serializers.ChoiceField(choices=['sql', 'python'], required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['draft', 'published', 'archived'], required=False)
    directoryId = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    remark = serializers.CharField(required=False, allow_blank=True)


class ScriptQuerySerializer(serializers.Serializer):
    """脚本查询序列化器"""
    scriptName = serializers.CharField(required=False, allow_blank=True)
    scriptType = serializers.ChoiceField(required=False, choices=['sql', 'python'])
    status = serializers.ChoiceField(required=False, choices=['draft', 'published', 'archived'])
    directoryId = serializers.IntegerField(required=False, allow_null=True)


# ── ScriptVersion ───────────────────────────────

class ScriptVersionSerializer(serializers.ModelSerializer):
    """脚本版本序列化器"""
    versionId = serializers.IntegerField(source='id', read_only=True)
    scriptId = serializers.IntegerField(source='script_id', read_only=True)
    versionNumber = serializers.IntegerField(source='version_number', read_only=True)
    contentHash = serializers.CharField(source='content_hash', read_only=True)
    changeLog = serializers.CharField(source='change_log', read_only=True)
    isCurrent = serializers.BooleanField(source='is_current', read_only=True)
    isReleased = serializers.BooleanField(source='is_released', read_only=True)
    createBy = serializers.CharField(source='create_by', read_only=True)
    createTime = serializers.DateTimeField(
        source='create_time', read_only=True, format='%Y-%m-%d %H:%M:%S'
    )

    class Meta:
        model = DataDevScriptVersion
        fields = [
            'versionId', 'scriptId', 'versionNumber', 'content',
            'contentHash', 'changeLog', 'isCurrent', 'isReleased', 'createBy', 'createTime',
        ]


class ScriptVersionCreateSerializer(serializers.Serializer):
    """创建新版本"""
    content = serializers.CharField()
    changeLog = serializers.CharField(required=False, allow_blank=True, default='')
    isReleased = serializers.BooleanField(required=False, default=False)


# ── ScriptExecution ─────────────────────────────

class ScriptExecutionSerializer(serializers.ModelSerializer):
    """脚本执行记录序列化器"""
    executionId = serializers.CharField(source='execution_id', read_only=True)
    scriptId = serializers.IntegerField(source='script_id', read_only=True)
    scriptName = serializers.CharField(source='script.script_name', read_only=True, default='')
    versionNumber = serializers.IntegerField(
        source='version.version_number', read_only=True, default=None
    )
    executorType = serializers.CharField(source='executor_type', read_only=True)
    executorParams = serializers.JSONField(source='executor_params', read_only=True)
    startTime = serializers.DateTimeField(
        source='start_time', read_only=True, format='%Y-%m-%d %H:%M:%S'
    )
    endTime = serializers.DateTimeField(
        source='end_time', read_only=True, format='%Y-%m-%d %H:%M:%S'
    )
    durationSeconds = serializers.IntegerField(source='duration_seconds', read_only=True)
    resultSummary = serializers.JSONField(source='result_summary', read_only=True)
    errorMessage = serializers.CharField(source='error_message', read_only=True)
    executedBy = serializers.CharField(source='executed_by', read_only=True)
    createTime = serializers.DateTimeField(
        source='create_time', read_only=True, format='%Y-%m-%d %H:%M:%S'
    )

    class Meta:
        model = DataDevScriptExecution
        fields = [
            'executionId', 'scriptId', 'scriptName', 'status',
            'versionNumber', 'executorType', 'executorParams',
            'startTime', 'endTime', 'durationSeconds',
            'resultSummary', 'errorMessage', 'executedBy', 'createTime',
        ]


class ScriptExecutionQuerySerializer(serializers.Serializer):
    """执行记录查询序列化器"""
    status = serializers.ChoiceField(
        required=False,
        choices=['pending', 'running', 'success', 'failed', 'cancelled'],
    )
    executedBy = serializers.CharField(required=False, allow_blank=True)


# ── DataDevDirectory ──────────────────────────────────────

class DataDevDirectorySerializer(BaseModelSerializer):
    """数据目录序列化器（列表/详情）"""
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
        # __init_subclass__ 自动追加: status, remark, createBy, updateBy, createTime, updateTime


class DataDevDirectoryCreateSerializer(serializers.Serializer):
    """数据目录创建序列化器"""
    parentId = serializers.IntegerField(default=0)
    directoryName = serializers.CharField(max_length=100)
    directoryCode = serializers.CharField(max_length=32)
    orderNum = serializers.IntegerField(default=0)
    status = serializers.ChoiceField(choices=['0', '1'], default='0')
    remark = serializers.CharField(required=False, allow_blank=True, default='')


class DataDevDirectoryUpdateSerializer(serializers.Serializer):
    """数据目录更新序列化器"""
    parentId = serializers.IntegerField(required=False)
    directoryName = serializers.CharField(max_length=100, required=False)
    directoryCode = serializers.CharField(max_length=32, required=False)
    orderNum = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=['0', '1'], required=False)
    remark = serializers.CharField(required=False, allow_blank=True)
