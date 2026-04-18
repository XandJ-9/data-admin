from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q

from apps.common.pagination import StandardPagination
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet

from .models import Task, TaskDependency, TaskInstance
from .serializers import (
    TaskDependencyCreateSerializer,
    TaskDependencyQuerySerializer,
    TaskDependencySerializer,
    TaskDependencyUpdateSerializer,
    TaskInstanceQuerySerializer,
    TaskInstanceSerializer,
    TaskQuerySerializer,
    TaskUpdateSerializer,
    TaskSerializer,
)
from .services import TaskService


class TaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = StandardPagination
    http_method_names = ['get', 'put', 'post']

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = TaskQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskName'):
            keyword = validated_data['taskName']
            qs = qs.filter(Q(task_name__icontains=keyword) | Q(task_code__icontains=keyword))
        if validated_data.get('taskType'):
            qs = qs.filter(task_type=validated_data['taskType'])
        if validated_data.get('status'):
            qs = qs.filter(status=validated_data['status'])
        if validated_data.get('sourceModule'):
            qs = qs.filter(source_module=validated_data['sourceModule'])
        if validated_data.get('owner'):
            qs = qs.filter(owner=validated_data['owner'])
        return qs.order_by('-update_time', '-id')

    @action(detail=True, methods=['get'], url_path='instances')
    def instances(self, request, pk=None):
        task = self.get_object()
        queryset = task.instances.select_related('task').all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskInstanceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskInstanceSerializer(queryset, many=True)
        return self.data(serializer.data)

    def update(self, request, *args, **kwargs):
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            task = Task.objects.select_for_update().filter(pk=kwargs.get('pk'), del_flag='0').first()
            if task is None:
                return self.not_found(msg='任务不存在')
            serializer = TaskUpdateSerializer(data=request.data, context={'instance': task})
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            changed_fields = set()
            task_config = dict(task.task_config or {})

            if 'status' in validated_data and task.status != validated_data['status']:
                task.status = validated_data['status']
                changed_fields.add('status')
            if 'owner' in validated_data and task.owner != validated_data['owner']:
                task.owner = validated_data['owner']
                changed_fields.add('owner')
            if 'remark' in validated_data and task.remark != validated_data['remark']:
                task.remark = validated_data['remark']
                changed_fields.add('remark')
            if 'scheduleType' in validated_data:
                next_schedule_type = validated_data['scheduleType']
                next_cron_expression = (
                    validated_data.get('cronExpression', task.cron_expression)
                    if next_schedule_type == 'cron'
                    else ''
                )
                if task.schedule_type != next_schedule_type:
                    task.schedule_type = next_schedule_type
                    changed_fields.add('schedule_type')
                if task.cron_expression != next_cron_expression:
                    task.cron_expression = next_cron_expression
                    changed_fields.add('cron_expression')
                task_config[TaskService.SOURCE_SCHEDULE_TYPE_KEY] = next_schedule_type
                task_config[TaskService.SOURCE_CRON_EXPRESSION_KEY] = next_cron_expression
            elif 'cronExpression' in validated_data and task.schedule_type == 'cron':
                next_cron_expression = validated_data['cronExpression']
                if task.cron_expression != next_cron_expression:
                    task.cron_expression = next_cron_expression
                    changed_fields.add('cron_expression')
                task_config[TaskService.SOURCE_CRON_EXPRESSION_KEY] = next_cron_expression

            if changed_fields and task.task_config != task_config:
                task.task_config = task_config
                changed_fields.add('task_config')

            if changed_fields:
                task.update_by = username
                task.save(update_fields=list(changed_fields) + ['update_by', 'update_time'])
                TaskService.sync_task_source_snapshot(
                    task,
                    changed_fields=changed_fields,
                    username=username,
                )
        return self.data(TaskSerializer(task).data, msg='更新成功')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        task = self.get_object()
        result = TaskService.execute_task(
            task,
            username=getattr(request.user, 'username', ''),
        )
        if result['ok']:
            return self.data(result['data'], msg=result['msg'])
        return self.error(msg=result['msg']) if result['data'] is None else Response(
            {'code': 400, 'msg': result['msg'], 'data': result['data']}
        )


class TaskDependencyViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = TaskDependency.objects.select_related('upstream_task', 'downstream_task').all()
    serializer_class = TaskDependencySerializer
    pagination_class = None
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = TaskDependencyQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('upstreamTaskId'):
            qs = qs.filter(upstream_task_id=validated_data['upstreamTaskId'])
        if validated_data.get('downstreamTaskId'):
            qs = qs.filter(downstream_task_id=validated_data['downstreamTaskId'])
        return qs.order_by('upstream_task_id', 'downstream_task_id')

    def create(self, request, *args, **kwargs):
        username = getattr(request.user, 'username', '')
        initial_serializer = TaskDependencyCreateSerializer(data=request.data)
        initial_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            task_ids = sorted({
                initial_serializer.validated_data['upstreamTaskId'],
                initial_serializer.validated_data['downstreamTaskId'],
            })
            list(Task.objects.select_for_update().filter(id__in=task_ids).order_by('id'))
            serializer = TaskDependencyCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            dependency = TaskDependency.objects.create(
                upstream_task_id=validated_data['upstreamTaskId'],
                downstream_task_id=validated_data['downstreamTaskId'],
                trigger_condition=validated_data['triggerCondition'],
                lag_seconds=validated_data['lagSeconds'],
                remark=validated_data.get('remark', ''),
                create_by=username,
                update_by=username,
            )
            TaskService.sync_dependency_schedule_type(validated_data['downstreamTaskId'])
        return self.data(
            TaskDependencySerializer(dependency).data,
            msg='创建成功',
        )

    def update(self, request, *args, **kwargs):
        dependency = self.get_object()
        initial_serializer = TaskDependencyUpdateSerializer(
            data=request.data,
            context={'instance': dependency},
        )
        initial_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            task_ids = sorted({
                dependency.upstream_task_id,
                dependency.downstream_task_id,
                initial_serializer.validated_data['upstreamTaskId'],
                initial_serializer.validated_data['downstreamTaskId'],
            })
            list(Task.objects.select_for_update().filter(id__in=task_ids).order_by('id'))
            serializer = TaskDependencyUpdateSerializer(
                data=request.data,
                context={'instance': dependency},
            )
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            original_downstream_task_id = dependency.downstream_task_id
            dependency.upstream_task_id = validated_data['upstreamTaskId']
            dependency.downstream_task_id = validated_data['downstreamTaskId']
            dependency.trigger_condition = validated_data['triggerCondition']
            dependency.lag_seconds = validated_data['lagSeconds']
            dependency.remark = validated_data.get('remark', '')
            dependency.update_by = getattr(request.user, 'username', '')
            dependency.save()
            TaskService.sync_dependency_schedule_type(original_downstream_task_id)
            TaskService.sync_dependency_schedule_type(dependency.downstream_task_id)
        return self.data(TaskDependencySerializer(dependency).data, msg='更新成功')

    def destroy(self, request, *args, **kwargs):
        dependencies = self.get_object()
        if not isinstance(dependencies, list):
            dependencies = [dependencies]

        affected_downstream_ids = set()
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            for dependency in dependencies:
                affected_downstream_ids.add(dependency.downstream_task_id)
                dependency.del_flag = '1'
                dependency.update_by = username
                dependency.save(update_fields=['del_flag', 'update_by', 'update_time'])

            for downstream_task_id in affected_downstream_ids:
                TaskService.sync_dependency_schedule_type(downstream_task_id)
        return self.ok(msg='删除成功')


class TaskInstanceViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = TaskInstance.objects.select_related('task').all()
    serializer_class = TaskInstanceSerializer
    pagination_class = StandardPagination
    http_method_names = ['get']

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = TaskInstanceQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('taskId'):
            qs = qs.filter(task_id=validated_data['taskId'])
        if validated_data.get('status'):
            qs = qs.filter(status=validated_data['status'])
        if validated_data.get('triggerMode'):
            qs = qs.filter(trigger_mode=validated_data['triggerMode'])
        if validated_data.get('triggeredBy'):
            qs = qs.filter(triggered_by=validated_data['triggeredBy'])
        return qs.order_by('-create_time')
