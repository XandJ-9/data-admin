from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.common.pagination import StandardPagination
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet

from .models import Task, TaskDependency, TaskInstance
from .serializers import (
    TaskDependencyQuerySerializer,
    TaskDependencySerializer,
    TaskInstanceQuerySerializer,
    TaskInstanceSerializer,
    TaskQuerySerializer,
    TaskSerializer,
)


class TaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = StandardPagination
    http_method_names = ['get']

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = TaskQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
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


class TaskDependencyViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = TaskDependency.objects.select_related('upstream_task', 'downstream_task').all()
    serializer_class = TaskDependencySerializer
    pagination_class = None
    http_method_names = ['get']

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
