from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLExecutionLog
from ..serializers import ETLExecutionLogSerializer, ETLExecutionLogCreateSerializer
from ..services import MonitoringService, ExecutionService

_FORBIDDEN = lambda msg: Response({'code': 403, 'msg': msg}, status=status.HTTP_403_FORBIDDEN)


class ETLExecutionLogViewSet(BaseViewSet):
    queryset = ETLExecutionLog.objects.all()
    serializer_class = ETLExecutionLogSerializer
    create_serializer_class = ETLExecutionLogCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        p = self.request.query_params
        if p.get('taskId'):
            queryset = queryset.filter(task_id=p['taskId'])
        if p.get('executionId'):
            queryset = queryset.filter(execution_id__icontains=p['executionId'])
        if p.get('status'):
            queryset = queryset.filter(status=p['status'])
        if p.get('triggerType'):
            queryset = queryset.filter(trigger_type=p['triggerType'])
        if p.get('executedBy'):
            queryset = queryset.filter(executed_by__icontains=p['executedBy'])
        if p.get('startTime'):
            queryset = queryset.filter(create_time__gte=p['startTime'])
        if p.get('endTime'):
            queryset = queryset.filter(create_time__lte=p['endTime'])
        return queryset

    def create(self, request, *args, **kwargs):
        return _FORBIDDEN('执行日志由系统自动创建，不允许手动创建')

    def update(self, request, *args, **kwargs):
        return _FORBIDDEN('执行日志不允许修改')

    def destroy(self, request, *args, **kwargs):
        return _FORBIDDEN('执行日志不允许删除')

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        stats = self.get_queryset().aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
            avg_duration=Avg('duration_seconds', filter=Q(duration_seconds__isnull=False)),
        )
        total = stats['total'] or 0
        success = stats['success'] or 0
        failed = stats['failed'] or 0
        return self.data({
            'total': total, 'success': success, 'failed': failed,
            'successRate': round(success / total * 100, 2) if total > 0 else 0,
            'failedRate': round(failed / total * 100, 2) if total > 0 else 0,
            'avgDuration': round(stats['avg_duration'] or 0, 2),
        })

    @action(detail=True, methods=['get'], url_path='detail')
    def execution_detail(self, request, pk=None):
        return self.data(ETLExecutionLogSerializer(self.get_object()).data)

    @action(detail=True, methods=['get'], url_path='progress')
    def get_progress(self, request, pk=None):
        try:
            return self.data(MonitoringService.get_execution_metrics(self.get_object().execution_id))
        except Exception as e:
            return Response({'code': 500, 'msg': f'获取进度失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_execution(self, request, pk=None):
        execution = self.get_object()
        if execution.status != 'running':
            return Response({'code': 400, 'msg': '任务不在执行状态'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if ExecutionService().cancel_execution(execution):
                return self.data({'message': '任务已取消'})
            return Response({'code': 500, 'msg': '取消任务失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'code': 500, 'msg': f'取消任务失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
