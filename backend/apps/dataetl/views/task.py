from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLTask, ETLExecutionLog
from ..serializers import (
    ETLTaskSerializer, ETLTaskCreateSerializer, ETLTaskUpdateSerializer,
    ETLTaskSimpleSerializer, ETLTaskVersionSerializer,
)
from ..services import TaskService, MonitoringService, ExecutionService, VersionService, ConfigService


class ETLTaskViewSet(BaseViewSet):
    queryset = ETLTask.objects.all()
    serializer_class = ETLTaskSerializer
    create_serializer_class = ETLTaskCreateSerializer
    update_serializer_class = ETLTaskUpdateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        p = self.request.query_params
        if p.get('taskName'):
            queryset = queryset.filter(task_name__icontains=p['taskName'])
        if p.get('taskCode'):
            queryset = queryset.filter(task_code__icontains=p['taskCode'])
        if p.get('etlType'):
            queryset = queryset.filter(etl_type=p['etlType'])
        if p.get('executorType'):
            queryset = queryset.filter(executor_type=p['executorType'])
        if p.get('status'):
            queryset = queryset.filter(status=p['status'])
        if p.get('sourceDatasourceId'):
            queryset = queryset.filter(source_datasource_id=p['sourceDatasourceId'])
        if p.get('targetDatasourceId'):
            queryset = queryset.filter(target_datasource_id=p['targetDatasourceId'])
        return queryset

    @action(detail=False, methods=['get'], url_path='simple')
    def simple_list(self, request):
        return self.data(ETLTaskSimpleSerializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        task_stats = self.get_queryset().aggregate(
            total=Count('id'), enabled=Count('id', filter=Q(status='0')),
        )
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        exec_stats = ETLExecutionLog.objects.filter(create_time__gte=today_start).aggregate(
            today_executions=Count('id'),
            failed_executions=Count('id', filter=Q(status='failed')),
        )
        return self.data({
            'totalTasks': task_stats['total'],
            'enabledTasks': task_stats['enabled'],
            'todayExecutions': exec_stats['today_executions'],
            'failedExecutions': exec_stats['failed_executions'],
        })

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        task = self.get_object()
        try:
            executed_by = request.user.username if request.user.is_authenticated else 'system'
            execution_id = ExecutionService().submit_task(task, executed_by, 'manual')
            return self.data({'executionId': execution_id, 'message': '任务已提交执行'})
        except ValueError as e:
            return Response({'code': 400, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'code': 500, 'msg': f'提交任务失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='create-version')
    def create_version(self, request, pk=None):
        task = self.get_object()
        create_by = request.user.username if request.user.is_authenticated else 'system'
        try:
            version = VersionService.create_version(task, request.data.get('changeLog', ''), create_by)
            return self.data(ETLTaskVersionSerializer(version).data)
        except Exception as e:
            return Response({'code': 500, 'msg': f'创建版本失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='versions')
    def task_versions(self, request, pk=None):
        return self.data(ETLTaskVersionSerializer(VersionService.get_task_versions(self.get_object()), many=True).data)

    @action(detail=True, methods=['post'], url_path='rollback')
    def rollback_version(self, request, pk=None):
        version_number = request.data.get('versionNumber')
        if not version_number:
            return Response({'code': 400, 'msg': '请指定版本号'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            VersionService.rollback_version(self.get_object(), version_number)
            return self.data({'message': f'已回滚到版本 {version_number}'})
        except ValueError as e:
            return Response({'code': 404, 'msg': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'code': 500, 'msg': f'回滚失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='validate-config')
    def validate_config(self, request, pk=None):
        try:
            is_valid, warnings, config = ConfigService().validate_datax_config(self.get_object())
            return self.data({'valid': is_valid, 'warnings': warnings, 'config': config})
        except ValueError as e:
            return Response({'code': 400, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'code': 500, 'msg': f'配置验证失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='datx-config')
    def generate_datx_config(self, request, pk=None):
        try:
            result = ConfigService().generate_datax_config(self.get_object(), request.query_params.get('executionDate'))
            return self.data(result)
        except ValueError as e:
            return Response({'code': 400, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'code': 500, 'msg': f'配置生成失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='execute-dry-run')
    def dry_run(self, request, pk=None):
        try:
            return self.data(ConfigService().dry_run(self.get_object()))
        except ValueError as e:
            return Response({'code': 400, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'code': 500, 'msg': f'模拟执行失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='from-template')
    def create_from_template(self, request):
        template_id = request.data.get('templateId')
        if not template_id:
            return Response({'code': 400, 'msg': '请提供模板ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = TaskService.create_task_from_template(template_id, request.data.get('params', {}))
            return self.data(ETLTaskSerializer(task).data)
        except Exception as e:
            return Response({'code': 500, 'msg': f'创建任务失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='clone')
    def clone_task(self, request, pk=None):
        new_name, new_code = request.data.get('taskName'), request.data.get('taskCode')
        if not new_name or not new_code:
            return Response({'code': 400, 'msg': '请提供新任务名称和编码'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return self.data(ETLTaskSerializer(TaskService.clone_task(self.get_object().id, new_name, new_code)).data)
        except Exception as e:
            return Response({'code': 500, 'msg': f'克隆任务失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='statistics')
    def get_statistics(self, request, pk=None):
        try:
            return self.data(MonitoringService.get_task_statistics(self.get_object().id, int(request.query_params.get('days', 7))))
        except Exception as e:
            return Response({'code': 500, 'msg': f'获取统计信息失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
