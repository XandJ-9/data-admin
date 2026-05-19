from django.db import transaction
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.pagination import StandardPagination
from apps.datatask.models import TaskInstance
from apps.datatask.services import TaskService
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet

from .models import DataIntegrationTask
from .serializers import (
    DataIntegrationExecutionLogQuerySerializer,
    DataIntegrationExecutionSerializer,
    DataIntegrationTaskCreateSerializer,
    DataIntegrationTaskQuerySerializer,
    DataIntegrationTaskSerializer,
    DataIntegrationTaskUpdateSerializer,
    DataIntegrationTaskValidateSerializer,
)
from .task_source import (
    RUNTIME_TASK_CONFIG_OVERRIDE_KEY,
    ensure_runtime_task,
    get_platform_task,
    is_task_published,
    sync_source_task,
    validate_task_configuration,
)


class DataIntegrationTaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    permission_map = {
        'list': 'dataintegration:task:query',
        'model_list': 'dataintegration:task:query',
        'retrieve': 'dataintegration:task:view',
        'executions': 'dataintegration:task:view',
        'create': 'dataintegration:task:add',
        'update': 'dataintegration:task:edit',
        'destroy': 'dataintegration:task:remove',
        'validate_task': 'dataintegration:task:add',
        'publish_task': 'dataintegration:task:execute',
        'execute_task': 'dataintegration:task:execute',
    }
    queryset = DataIntegrationTask.objects.select_related(
        'source_datasource',
        'target_datasource',
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

    def create(self, request, *args, **kwargs):
        serializer = DataIntegrationTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            task = DataIntegrationTask.objects.create(
                task_name=validated_data['taskName'],
                task_code=validated_data['taskCode'],
                source_datasource_id=validated_data['sourceDataSourceId'],
                target_datasource_id=validated_data['targetDataSourceId'],
                source_database_name=validated_data.get('sourceDatabaseName', ''),
                source_table_name=validated_data['sourceTableName'].strip(),
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            instance.del_flag = '1'
            instance.update_by = username
            instance.save(update_fields=['del_flag', 'update_by', 'update_time'])
            TaskService.soft_delete_source_task(
                source_module='dataintegration.task',
                source_record_id=instance.id,
                username=username,
            )
        return self.ok(msg='删除成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataIntegrationTaskUpdateSerializer(data=request.data, context={'instance': instance})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            if 'taskName' in validated_data:
                instance.task_name = validated_data['taskName']
            if 'sourceDataSourceId' in validated_data:
                instance.source_datasource_id = validated_data['sourceDataSourceId']
            if 'targetDataSourceId' in validated_data:
                instance.target_datasource_id = validated_data['targetDataSourceId']
            if 'sourceDatabaseName' in validated_data:
                instance.source_database_name = validated_data['sourceDatabaseName']
            if 'sourceTableName' in validated_data:
                instance.source_table_name = validated_data['sourceTableName'].strip()
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
            instance.update_by = username
            instance.save()
        instance = self.get_queryset().get(pk=instance.pk)
        return self.data(DataIntegrationTaskSerializer(instance).data, msg='更新成功')

    @action(detail=True, methods=['post'], url_path='publish')
    def publish_task(self, request, pk=None):
        integration_task = self.get_object()
        username = getattr(request.user, 'username', '')
        is_valid, error_message = validate_task_configuration(integration_task)
        if not is_valid:
            return self.error(msg=error_message)
        sync_source_task(integration_task, username=username, published_to_task_ops=True)
        integration_task = self.get_queryset().get(pk=integration_task.pk)
        return self.data(DataIntegrationTaskSerializer(integration_task).data, msg='发布成功')

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_task(self, request):
        serializer = DataIntegrationTaskValidateSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))
            message = first_error[0] if isinstance(first_error, list) and first_error else first_error
            return Response({'code': 400, 'msg': str(message)}, status=400)
        validated_data = serializer.validated_data
        task = DataIntegrationTask(
            task_name=validated_data['taskName'],
            task_code=validated_data['taskCode'],
            source_datasource_id=validated_data['sourceDataSourceId'],
            target_datasource_id=validated_data['targetDataSourceId'],
            source_database_name=validated_data.get('sourceDatabaseName', ''),
            source_table_name=validated_data['sourceTableName'].strip(),
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
            return Response({'code': 400, 'msg': error_message}, status=400)
        return self.ok(msg='校验通过')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        integration_task = self.get_object()
        username = getattr(request.user, 'username', '')
        platform_task = ensure_runtime_task(integration_task, username=username)
        result = TaskService.execute_task(
            platform_task,
            username=username,
            runtime_config={
                RUNTIME_TASK_CONFIG_OVERRIDE_KEY: {
                    'sourceDataSourceId': integration_task.source_datasource_id,
                    'targetDataSourceId': integration_task.target_datasource_id,
                    'sourceDatabaseName': integration_task.source_database_name,
                    'sourceTableName': integration_task.source_table_name,
                    'targetSchemaName': integration_task.target_schema_name,
                    'targetTableName': integration_task.target_table_name,
                    'loadType': integration_task.load_type,
                    'writeMode': integration_task.write_mode,
                    'executorType': integration_task.executor_type,
                    'scheduleType': integration_task.schedule_type,
                    'cronExpression': integration_task.cron_expression,
                    'taskConfig': integration_task.task_config,
                }
            },
        )
        task_instance = TaskInstance.objects.filter(instance_id=(result.get('data') or {}).get('executionId')).first()
        payload = DataIntegrationExecutionSerializer(task_instance).data if task_instance is not None else result.get('data')
        if payload is None and not result['ok']:
            return self.error(msg=result['msg'])
        return self.data(payload, msg=result['msg'])

    @action(detail=True, methods=['get'], url_path='executions')
    def executions(self, request, pk=None):
        integration_task = self.get_object()
        queryset = TaskInstance.objects.select_related('task').filter(
            task__source_module='dataintegration.task',
            task__source_record_id=integration_task.id,
        ).order_by('-create_time', '-id')
        page = self.paginate_queryset(queryset)
        serializer = DataIntegrationExecutionSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return self.raw_response({'code': 200, 'msg': '操作成功', 'rows': serializer.data, 'total': len(serializer.data)})


class IntegrationExecutionLogViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    permission_map = {
        'list': 'dataintegration:task:view',
        'model_list': 'dataintegration:task:view',
        'retrieve': 'dataintegration:task:view',
        'execution_detail': 'dataintegration:task:view',
    }
    queryset = TaskInstance.objects.select_related('task').filter(task__source_module='dataintegration.task')
    serializer_class = DataIntegrationExecutionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        serializer = DataIntegrationExecutionLogQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskId'):
            queryset = queryset.filter(task__source_record_id=validated_data['taskId'])
        if validated_data.get('status'):
            queryset = queryset.filter(status=validated_data['status'])
        return queryset.order_by('-create_time', '-id')

    @action(detail=True, methods=['get'], url_path='detail')
    def execution_detail(self, request, pk=None):
        instance = TaskInstance.objects.select_related('task').filter(
            pk=pk,
            task__source_module='dataintegration.task',
        ).first()
        if instance is None:
            return self.not_found('执行记录不存在')
        return self.raw_response({
            'code': 200,
            'msg': '操作成功',
            'data': DataIntegrationExecutionSerializer(instance).data,
        })
