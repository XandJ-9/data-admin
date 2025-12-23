from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DataTask, TaskLog, AlertRule, AlertRecord
from .serializers import DataTaskSerializer, TaskLogSerializer, AlertRuleSerializer, AlertRecordSerializer
from apps.common.pagination import StandardPagination
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.system.views.core import BaseViewSet

class DataTaskViewSet(BaseViewSet):
    queryset = DataTask.objects.all().order_by('-create_time')
    serializer_class = DataTaskSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task_name', 'task_type']
    ordering_fields = ['create_time', 'status']

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        task = self.get_object()
        task.status = 'running'
        task.save()
        return Response({'status': 'task started'})

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        task = self.get_object()
        task.status = 'failed' # Or stopped/idle
        task.save()
        return Response({'status': 'task stopped'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        task = self.get_object()
        task.status = 'paused'
        task.save()
        return Response({'status': 'task paused'})

class TaskLogViewSet(BaseViewSet):
    queryset = TaskLog.objects.all()
    serializer_class = TaskLogSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task__task_name', 'status']
    ordering_fields = ['create_time']

class AlertRuleViewSet(BaseViewSet):
    queryset = AlertRule.objects.all().order_by('-create_time')
    serializer_class = AlertRuleSerializer
    pagination_class = StandardPagination

class AlertRecordViewSet(BaseViewSet):
    queryset = AlertRecord.objects.all()
    serializer_class = AlertRecordSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task_name', 'status']
    ordering_fields = ['trigger_time']
    
    @action(detail=True, methods=['post'])
    def handle(self, request, pk=None):
        record = self.get_object()
        record.status = 'handled'
        record.handle_note = request.data.get('note', '')
        record.save()
        return Response({'status': 'alert handled'})
