from django.db import transaction
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.common.pagination import StandardPagination
from apps.datasource.models import SourceTableSnapshot
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet

from .models import DataIntegrationExecutionLog, DataIntegrationTask
from .serializers import (
    DataIntegrationExecutionLogQuerySerializer,
    DataIntegrationExecutionLogSerializer,
    DataIntegrationTaskCreateSerializer,
    DataIntegrationTaskQuerySerializer,
    DataIntegrationTaskSerializer,
    DataIntegrationTaskUpdateSerializer,
    DataIntegrationTaskValidateSerializer,
    SourceTableOptionSerializer,
    SourceTableQuerySerializer,
)
from .services import execute_integration_task, validate_task_configuration


class DataIntegrationTaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataIntegrationTask.objects.select_related(
        'source_datasource',
        'target_datasource',
        'source_table_snapshot',
    ).all()
    serializer_class = DataIntegrationTaskSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        serializer = DataIntegrationTaskQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskName'):
            queryset = queryset.filter(task_name__icontains=validated_data['taskName'])
        if validated_data.get('status'):
            queryset = queryset.filter(status=validated_data['status'])
        if validated_data.get('executorType'):
            queryset = queryset.filter(executor_type=validated_data['executorType'])
        if validated_data.get('sourceDataSourceId'):
            queryset = queryset.filter(source_datasource_id=validated_data['sourceDataSourceId'])
        if validated_data.get('targetDataSourceId'):
            queryset = queryset.filter(target_datasource_id=validated_data['targetDataSourceId'])
        return queryset.order_by('-update_time', '-id')

    def _get_source_table(self, source_table_id):
        if not source_table_id:
            return None
        return SourceTableSnapshot.objects.filter(id=source_table_id, del_flag='0').first()

    def create(self, request, *args, **kwargs):
        serializer = DataIntegrationTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        username = getattr(request.user, 'username', '')
        source_table = self._get_source_table(validated_data.get('sourceTableId'))
        task = DataIntegrationTask.objects.create(
            task_name=validated_data['taskName'],
            task_code=validated_data['taskCode'],
            source_datasource_id=validated_data['sourceDataSourceId'],
            target_datasource_id=validated_data['targetDataSourceId'],
            source_table_snapshot=source_table,
            source_database_name=getattr(source_table, 'database_name', '') if source_table else '',
            source_table_name=getattr(source_table, 'table_name', '') if source_table else '',
            target_schema_name=validated_data.get('targetSchemaName', ''),
            target_table_name=validated_data['targetTableName'],
            load_type=validated_data['loadType'],
            write_mode=validated_data['writeMode'],
            executor_type=validated_data['executorType'],
            status='active',
            schedule_type=validated_data['scheduleType'],
            cron_expression=validated_data.get('cronExpression', ''),
            owner=validated_data.get('owner', ''),
            task_config=validated_data.get('taskConfig', {}),
            remark=validated_data.get('remark', ''),
            create_by=username,
            update_by=username,
        )
        task = self.get_queryset().get(pk=task.pk)
        return self.data(DataIntegrationTaskSerializer(task).data, msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataIntegrationTaskUpdateSerializer(data=request.data, context={'instance': instance})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        source_table = self._get_source_table(validated_data['sourceTableId']) if 'sourceTableId' in validated_data else instance.source_table_snapshot
        if 'taskName' in validated_data:
            instance.task_name = validated_data['taskName']
        if 'sourceDataSourceId' in validated_data:
            instance.source_datasource_id = validated_data['sourceDataSourceId']
        if 'targetDataSourceId' in validated_data:
            instance.target_datasource_id = validated_data['targetDataSourceId']
        if 'sourceTableId' in validated_data:
            instance.source_table_snapshot = source_table
            instance.source_database_name = getattr(source_table, 'database_name', '') if source_table else ''
            instance.source_table_name = getattr(source_table, 'table_name', '') if source_table else ''
        if 'targetSchemaName' in validated_data:
            instance.target_schema_name = validated_data['targetSchemaName']
        if 'targetTableName' in validated_data:
            instance.target_table_name = validated_data['targetTableName']
        if 'loadType' in validated_data:
            instance.load_type = validated_data['loadType']
        if 'writeMode' in validated_data:
            instance.write_mode = validated_data['writeMode']
        if 'executorType' in validated_data:
            instance.executor_type = validated_data['executorType']
        if 'status' in validated_data:
            instance.status = validated_data['status']
        if 'scheduleType' in validated_data:
            instance.schedule_type = validated_data['scheduleType']
        if 'cronExpression' in validated_data:
            instance.cron_expression = validated_data['cronExpression']
        if 'owner' in validated_data:
            instance.owner = validated_data['owner']
        if 'taskConfig' in validated_data:
            instance.task_config = validated_data['taskConfig']
        if 'remark' in validated_data:
            instance.remark = validated_data['remark']
        instance.update_by = getattr(request.user, 'username', '')
        instance.save()
        instance = self.get_queryset().get(pk=instance.pk)
        return self.data(DataIntegrationTaskSerializer(instance).data, msg='更新成功')

    @action(detail=False, methods=['get'], url_path='source-tables')
    def source_tables(self, request):
        serializer = SourceTableQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        queryset = SourceTableSnapshot.objects.filter(
            data_source_id=serializer.validated_data['sourceDataSourceId'],
            del_flag='0',
        ).order_by('database_name', 'table_name')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized = SourceTableOptionSerializer(page, many=True)
            return self.get_paginated_response(serialized.data)
        serialized = SourceTableOptionSerializer(queryset, many=True)
        return self.raw_response({'code': 200, 'msg': '操作成功', 'rows': serialized.data, 'total': len(serialized.data)})

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_task(self, request):
        serializer = DataIntegrationTaskValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        source_table = self._get_source_table(validated_data.get('sourceTableId'))
        task = DataIntegrationTask(
            task_name=validated_data['taskName'],
            task_code=validated_data['taskCode'],
            source_datasource_id=validated_data['sourceDataSourceId'],
            target_datasource_id=validated_data['targetDataSourceId'],
            source_table_snapshot=source_table,
            source_database_name=getattr(source_table, 'database_name', '') if source_table else '',
            source_table_name=getattr(source_table, 'table_name', '') if source_table else '',
            target_schema_name=validated_data.get('targetSchemaName', ''),
            target_table_name=validated_data['targetTableName'],
            load_type=validated_data['loadType'],
            write_mode=validated_data['writeMode'],
            executor_type=validated_data['executorType'],
            schedule_type=validated_data['scheduleType'],
            cron_expression=validated_data.get('cronExpression', ''),
            task_config=validated_data.get('taskConfig', {}),
            owner=validated_data.get('owner', ''),
            remark=validated_data.get('remark', ''),
        )
        task.source_datasource = task.source_datasource
        task.target_datasource = task.target_datasource
        is_valid, error_message = validate_task_configuration(task)
        if not is_valid:
            return self.error(msg=error_message)
        return self.ok(msg='校验通过')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        task = self.get_object()
        username = getattr(request.user, 'username', '')
        execution_log = execute_integration_task(task, username)
        if execution_log.status == 'failed':
            return self.data(DataIntegrationExecutionLogSerializer(execution_log).data, msg='执行失败')
        return self.data(DataIntegrationExecutionLogSerializer(execution_log).data, msg='执行成功')

    @action(detail=True, methods=['get'], url_path='executions')
    def executions(self, request, pk=None):
        task = self.get_object()
        queryset = DataIntegrationExecutionLog.objects.filter(task=task, del_flag='0').order_by('-create_time', '-id')
        page = self.paginate_queryset(queryset)
        serializer = DataIntegrationExecutionLogSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return self.raw_response({'code': 200, 'msg': '操作成功', 'rows': serializer.data, 'total': len(serializer.data)})


class IntegrationExecutionLogViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataIntegrationExecutionLog.objects.select_related('task').all()
    serializer_class = DataIntegrationExecutionLogSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        serializer = DataIntegrationExecutionLogQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskId'):
            queryset = queryset.filter(task_id=validated_data['taskId'])
        if validated_data.get('status'):
            queryset = queryset.filter(status=validated_data['status'])
        return queryset.order_by('-create_time', '-id')

    @action(detail=True, methods=['get'], url_path='detail')
    def detail(self, request, pk=None):
        instance = self.get_object()
        return self.data(DataIntegrationExecutionLogSerializer(instance).data)

