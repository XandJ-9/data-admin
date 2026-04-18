from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q

from apps.dataasset.models import DataAsset
from apps.datasource.models import DataSource
from apps.executors.base import ExecutorFactory
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet
from apps.common.pagination import StandardPagination
from apps.datatask.models import Task, TaskDependency, TaskInstance
from apps.datatask.services import TaskService

from .models import DataIntegrationTask
from .serializers import (
    DataIntegrationExecutionDetailSerializer,
    DataIntegrationExecutionLogQuerySerializer,
    DataIntegrationExecutionLogSerializer,
    DataIntegrationTaskCreateSerializer,
    DataIntegrationTaskQuerySerializer,
    DataIntegrationTaskSerializer,
    DataIntegrationTaskUpdateSerializer,
    DataIntegrationTaskValidateSerializer,
)


class DataIntegrationTaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataIntegrationTask.objects.select_related(
        'source_datasource',
        'target_datasource',
        'source_asset',
    ).all()
    serializer_class = DataIntegrationTaskSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = DataIntegrationTaskQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskName'):
            qs = qs.filter(task_name__icontains=validated_data['taskName'])
        if validated_data.get('status'):
            qs = qs.filter(status=validated_data['status'])
        if validated_data.get('executorType'):
            qs = qs.filter(executor_type=validated_data['executorType'])
        if validated_data.get('sourceDataSourceId'):
            qs = qs.filter(source_datasource_id=validated_data['sourceDataSourceId'])
        if validated_data.get('targetDataSourceId'):
            qs = qs.filter(target_datasource_id=validated_data['targetDataSourceId'])
        return qs.order_by('-update_time', '-id')

    def create(self, request, *args, **kwargs):
        serializer = DataIntegrationTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        username = getattr(request.user, 'username', '')

        source_asset = self._get_source_asset(validated_data.get('sourceAssetId'))
        with transaction.atomic():
            task = DataIntegrationTask.objects.create(
                task_name=validated_data['taskName'],
                task_code=validated_data['taskCode'],
                source_datasource_id=validated_data['sourceDataSourceId'],
                target_datasource_id=validated_data['targetDataSourceId'],
                source_asset=source_asset,
                target_schema_name=validated_data.get('targetSchemaName', ''),
                target_table_name=validated_data['targetTableName'],
                load_type=validated_data['loadType'],
                write_mode=validated_data['writeMode'],
                executor_type=validated_data['executorType'],
                schedule_type=validated_data['scheduleType'],
                cron_expression=validated_data.get('cronExpression', ''),
                owner=validated_data.get('owner', ''),
                task_config=validated_data.get('taskConfig', {}),
                remark=validated_data.get('remark', ''),
                create_by=username,
                update_by=username,
            )
            self._sync_platform_task(task, username=username)
        return self.data(
            DataIntegrationTaskSerializer(task).data,
            msg='创建成功',
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataIntegrationTaskUpdateSerializer(data=request.data, context={'instance': instance})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        with transaction.atomic():
            if 'taskName' in validated_data:
                instance.task_name = validated_data['taskName']
            if 'sourceDataSourceId' in validated_data:
                instance.source_datasource_id = validated_data['sourceDataSourceId']
            if 'targetDataSourceId' in validated_data:
                instance.target_datasource_id = validated_data['targetDataSourceId']
            if 'sourceAssetId' in validated_data:
                instance.source_asset = self._get_source_asset(validated_data.get('sourceAssetId'))
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
            self._sync_platform_task(instance, username=instance.update_by)
        return self.data(
            DataIntegrationTaskSerializer(instance).data,
            msg='更新成功',
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        username = getattr(request.user, 'username', '')
        affected_downstream_ids = []
        with transaction.atomic():
            instance.del_flag = '1'
            instance.update_by = username
            instance.save(update_fields=['del_flag', 'update_by'])

            platform_task = Task.objects.filter(
                source_module='dataintegration.task',
                source_record_id=instance.id,
                del_flag='0',
            ).first()
            if platform_task is not None:
                related_dependencies = TaskDependency.objects.filter(
                    del_flag='0',
                ).filter(
                    Q(upstream_task=platform_task) | Q(downstream_task=platform_task)
                )
                for dependency in related_dependencies:
                    if dependency.upstream_task_id == platform_task.id:
                        affected_downstream_ids.append(dependency.downstream_task_id)
                    dependency.del_flag = '1'
                    dependency.update_by = username
                    dependency.save(update_fields=['del_flag', 'update_by'])
                platform_task.del_flag = '1'
                platform_task.update_by = username
                platform_task.save(update_fields=['del_flag', 'update_by'])

            for downstream_task_id in set(affected_downstream_ids):
                TaskService.sync_dependency_schedule_type(downstream_task_id)
        return self.ok(msg='删除成功')

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_task(self, request):
        serializer = DataIntegrationTaskValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        errors = []
        if validated_data['sourceDataSourceId'] == validated_data['targetDataSourceId']:
            errors.append('源数据源和目标数据源不能相同')
        if validated_data['scheduleType'] == 'cron' and not validated_data.get('cronExpression'):
            errors.append('定时调度模式必须配置 Cron 表达式')
        if validated_data['executorType'] == 'datax':
            errors.append('当前阶段 DataX 执行链路尚未接入，请先使用 mock 执行器完成配置联调')
        if errors:
            return self.error(msg='；'.join(errors))
        return self.ok(msg='校验通过')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        integration_task = self.get_object()
        username = getattr(request.user, 'username', '')
        result = TaskService.execute_integration_task(integration_task, username=username)
        if result['ok']:
            return self.data(result['data'], msg=result['msg'])
        return Response({'code': 400, 'msg': result['msg'], 'data': result['data']})

    @action(detail=True, methods=['get'], url_path='executions')
    def executions(self, request, pk=None):
        integration_task = self.get_object()
        queryset = TaskInstance.objects.select_related('task').filter(
            task__source_module='dataintegration.task',
            task__source_record_id=integration_task.id,
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DataIntegrationExecutionLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = DataIntegrationExecutionLogSerializer(queryset, many=True)
        return self.data(serializer.data)

    def _get_source_asset(self, source_asset_id):
        if source_asset_id in (None, ''):
            return None
        source_asset = DataAsset.objects.filter(id=source_asset_id, del_flag='0').first()
        if source_asset is None:
            raise DRFValidationError({'sourceAssetId': '源资产不存在'})
        return source_asset

    def _sync_platform_task(self, integration_task, username=''):
        return TaskService.sync_integration_source_task(integration_task, username=username)



class IntegrationExecutionLogViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = TaskInstance.objects.select_related('task').filter(task__source_module='dataintegration.task')
    serializer_class = DataIntegrationExecutionLogSerializer
    pagination_class = StandardPagination
    http_method_names = ['get']

    def get_queryset(self):
        queryset = super().get_queryset().filter(task__source_module='dataintegration.task')
        serializer = DataIntegrationExecutionLogQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskId'):
            queryset = queryset.filter(task__source_record_id=validated_data['taskId'])
        if validated_data.get('status'):
            queryset = queryset.filter(status=validated_data['status'])
        return queryset.order_by('-create_time')

    @action(detail=True, methods=['get'], url_path='detail')
    def execution_detail(self, request, pk=None):
        instance = self.get_object()
        serializer = DataIntegrationExecutionDetailSerializer(instance)
        return self.data(serializer.data)
