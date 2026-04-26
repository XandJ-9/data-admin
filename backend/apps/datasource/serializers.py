from rest_framework import serializers

from apps.datatask.models import TaskInstance
from apps.common.encrypt import encrypt_password
from apps.system.serializers import BaseModelSerializer

from .models import DataSource


class DataSourceSerializer(BaseModelSerializer):
    dataSourceId = serializers.IntegerField(source='id', read_only=True)
    dataSourceName = serializers.CharField(source='name')
    dbType = serializers.CharField(source='db_type')
    dbName = serializers.CharField(source='db_name')
    password = serializers.SerializerMethodField()
    connectivityStatus = serializers.CharField(source='connectivity_status', read_only=True)
    connectivityMessage = serializers.CharField(source='connectivity_message', read_only=True)
    connectivityTestedAt = serializers.DateTimeField(
        source='connectivity_tested_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S',
    )

    class Meta:
        model = DataSource
        fields = [
            'dataSourceId',
            'dataSourceName',
            'dbType',
            'host',
            'port',
            'dbName',
            'username',
            'password',
            'params',
            'status',
            'remark',
            'connectivityStatus',
            'connectivityMessage',
            'connectivityTestedAt',
        ]

    def get_password(self, obj):
        return '******' if obj.password else ''


class DataSourceQuerySerializer(serializers.Serializer):
    dataSourceName = serializers.CharField(required=False, allow_blank=True)
    dbType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0', '1'])


class DataSourceCreateSerializer(DataSourceSerializer):
    password = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        validated_data.pop('id', None)
        password = validated_data.get('password', '')
        if password:
            validated_data['password'] = encrypt_password(password)
        return super().create(validated_data)


class DataSourceUpdateSerializer(DataSourceSerializer):
    dataSourceId = serializers.IntegerField(source='id', required=True)
    password = serializers.CharField(required=False, allow_blank=True)


class DataSourceTestSerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField(required=False, allow_null=True)
    dbType = serializers.CharField(source='db_type')
    host = serializers.CharField(required=False, allow_blank=True, default='')
    port = serializers.IntegerField(required=False, default=0)
    dbName = serializers.CharField(source='db_name', required=False, allow_blank=True, default='')
    username = serializers.CharField(required=False, allow_blank=True, default='')
    password = serializers.CharField(required=False, allow_blank=True, default='')
    params = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')


class DiscoveryRequestSerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField(source='data_source_id')
    databaseName = serializers.CharField(source='database_name', required=False, allow_blank=True, default='')


class TableDiscoveryRequestSerializer(DiscoveryRequestSerializer):
    tableName = serializers.CharField(source='table_name', required=False, allow_blank=True, default='')


class TableCollectionRequestSerializer(DiscoveryRequestSerializer):
    tableName = serializers.CharField(source='table_name')
    tableType = serializers.CharField(source='table_type', required=False, allow_blank=True, default='TABLE')


class DatabaseCollectionRequestSerializer(DiscoveryRequestSerializer):
    databaseName = serializers.CharField(source='database_name')


class DataSourceCollectionRunSerializer(serializers.ModelSerializer):
    taskInstanceId = serializers.IntegerField(source='id', read_only=True)
    taskId = serializers.IntegerField(source='task_id', read_only=True)
    runId = serializers.CharField(source='instance_id', read_only=True)
    taskCode = serializers.CharField(source='task.task_code', read_only=True)
    taskName = serializers.CharField(source='task.task_name', read_only=True)
    dataSourceId = serializers.SerializerMethodField()
    dataSourceName = serializers.SerializerMethodField()
    collectionScope = serializers.SerializerMethodField()
    databaseName = serializers.SerializerMethodField()
    tableName = serializers.SerializerMethodField()
    totalTables = serializers.SerializerMethodField()
    successfulTables = serializers.SerializerMethodField()
    failedTables = serializers.SerializerMethodField()
    skippedTables = serializers.SerializerMethodField()
    currentTable = serializers.SerializerMethodField()
    startedAt = serializers.DateTimeField(source='started_at', read_only=True, format='%Y-%m-%d %H:%M:%S')
    finishedAt = serializers.DateTimeField(source='finished_at', read_only=True, format='%Y-%m-%d %H:%M:%S')
    errorMessage = serializers.CharField(source='error_message', read_only=True)
    resultSummary = serializers.JSONField(source='result_summary', read_only=True)
    createTime = serializers.DateTimeField(source='create_time', read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = TaskInstance
        fields = [
            'taskInstanceId',
            'taskId',
            'runId',
            'taskCode',
            'taskName',
            'status',
            'dataSourceId',
            'dataSourceName',
            'collectionScope',
            'databaseName',
            'tableName',
            'totalTables',
            'successfulTables',
            'failedTables',
            'skippedTables',
            'currentTable',
            'startedAt',
            'finishedAt',
            'errorMessage',
            'resultSummary',
            'createTime',
        ]

    def _result_summary(self, obj):
        return obj.result_summary or {}

    def _runtime_config(self, obj):
        return obj.runtime_config or {}

    def get_dataSourceId(self, obj):
        runtime_config = self._runtime_config(obj)
        return runtime_config.get('dataSourceId')

    def get_dataSourceName(self, obj):
        runtime_config = self._runtime_config(obj)
        return runtime_config.get('dataSourceName') or ''

    def get_collectionScope(self, obj):
        runtime_config = self._runtime_config(obj)
        return runtime_config.get('collectionScope') or ''

    def get_databaseName(self, obj):
        runtime_config = self._runtime_config(obj)
        return runtime_config.get('databaseName') or ''

    def get_tableName(self, obj):
        runtime_config = self._runtime_config(obj)
        return runtime_config.get('tableName') or ''

    def get_totalTables(self, obj):
        return int(self._result_summary(obj).get('totalTables') or 0)

    def get_successfulTables(self, obj):
        return int(self._result_summary(obj).get('successfulTables') or 0)

    def get_failedTables(self, obj):
        return int(self._result_summary(obj).get('failedTables') or 0)

    def get_skippedTables(self, obj):
        return int(self._result_summary(obj).get('skippedTables') or 0)

    def get_currentTable(self, obj):
        return str(self._result_summary(obj).get('currentTable') or '')
