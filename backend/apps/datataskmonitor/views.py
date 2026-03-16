from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DataTask, TaskLog, AlertRule, AlertRecord, TaskExecution, TaskExecutionLog
from .serializers import (
    DataTaskSerializer,
    TaskLogSerializer,
    AlertRuleSerializer,
    AlertRecordSerializer,
    TaskExecutionSerializer,
    TaskExecutionListSerializer,
    TaskExecutionLogSerializer,
)
from apps.common.pagination import StandardPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from apps.system.views.core import BaseViewSet
from apps.datastudio.models import DataStudioTask
from .taskmanager.executor import TaskExecutor
from .services.execution import TaskExecutionService

class DataTaskViewSet(BaseViewSet):
    queryset = DataTask.objects.all().order_by('-create_time')
    serializer_class = DataTaskSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task_name', 'task_type']
    ordering_fields = ['create_time', 'status']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('source_task')

        qp = self.request.query_params
        task_name = qp.get('taskName') or qp.get('task_name')
        task_type = qp.get('taskType') or qp.get('task_type')
        enabled = qp.get('enabled')
        status_value = qp.get('status')
        source_task_type = qp.get('sourceTaskType') or qp.get('source_task_type')

        if task_name:
            qs = qs.filter(task_name__icontains=task_name)
        if task_type:
            qs = qs.filter(task_type=task_type)
        if enabled in ('0', '1'):
            qs = qs.filter(enabled=enabled)
        if status_value:
            qs = qs.filter(status=status_value)
        if source_task_type:
            qs = qs.filter(source_task__type=source_task_type)

        return qs.filter(source_task__isnull=False).order_by('-create_time')

    def create(self, request, *args, **kwargs):
        return Response({'code': 405, 'msg': '任务来自数据开发模块，禁止在运维模块创建'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({'code': 405, 'msg': '任务来自数据开发模块，禁止在运维模块删除'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        self._ensure_ops_tasks()
        return super().list(request, *args, **kwargs)

    @staticmethod
    def _map_source_type_to_ops_type(source_type: str) -> str:
        if source_type == 'data_integration':
            return 'collection'
        if source_type in ('hive', 'spark', 'spark_sql', 'flink', 'flink_sql', 'python', 'shell'):
            return 'calculation'
        return 'storage'

    def _ensure_ops_tasks(self):
        studio_qs = DataStudioTask.objects.filter(del_flag='0')
        studio_tasks = list(studio_qs.only('id', 'name', 'type', 'status'))
        if not studio_tasks:
            return

        studio_ids = [t.id for t in studio_tasks]
        existing = DataTask.objects.filter(source_task_id__in=studio_ids).only('id', 'source_task_id', 'task_name', 'task_type')
        existing_by_source = {t.source_task_id: t for t in existing}

        to_create = []
        to_update = []
        for st in studio_tasks:
            ops_type = self._map_source_type_to_ops_type(st.type)

            ops = existing_by_source.get(st.id)
            if not ops:
                to_create.append(
                    DataTask(
                        source_task_id=st.id,
                        task_name=st.name,
                        task_type=ops_type,
                        schedule_type='once',
                        schedule_conf='',
                        enabled='0' if st.status == '0' else '1',
                        status='idle',
                        description='',
                    )
                )
                continue

            changed = False
            if ops.task_name != st.name:
                ops.task_name = st.name
                changed = True
            if ops.task_type != ops_type:
                ops.task_type = ops_type
                changed = True

            if changed:
                to_update.append(ops)

        with transaction.atomic():
            if to_create:
                DataTask.objects.bulk_create(to_create, ignore_conflicts=True)
            if to_update:
                DataTask.objects.bulk_update(to_update, ['task_name', 'task_type'])

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        task = self.get_object()
        if task.enabled == '1':
            return Response({'code': 400, 'msg': '任务已禁用，无法启动'}, status=status.HTTP_400_BAD_REQUEST)
        if task.status == 'running':
            return Response({'code': 400, 'msg': '任务运行中'}, status=status.HTTP_400_BAD_REQUEST)

        actor = getattr(getattr(request, 'user', None), 'username', '') or ''
        TaskExecutor.execute(task, actor=actor)
        return Response({'code': 200, 'msg': '操作成功'})

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        task = self.get_object()
        now = timezone.now()
        running_log = TaskLog.objects.filter(task=task, status='running').order_by('-start_time').first()
        if running_log:
            running_log.status = 'failed'
            running_log.end_time = now
            running_log.message = (running_log.message or '') + '\nmanual stop'
            running_log.update_by = getattr(getattr(request, 'user', None), 'username', '') or ''
            running_log.save(update_fields=['status', 'end_time', 'message', 'update_by', 'update_time'])

        task.status = 'idle'
        task.save(update_fields=['status', 'update_time'])
        return Response({'code': 200, 'msg': '操作成功'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        task = self.get_object()
        now = timezone.now()
        running_log = TaskLog.objects.filter(task=task, status='running').order_by('-start_time').first()
        if running_log:
            running_log.status = 'failed'
            running_log.end_time = now
            running_log.message = (running_log.message or '') + '\nmanual pause'
            running_log.update_by = getattr(getattr(request, 'user', None), 'username', '') or ''
            running_log.save(update_fields=['status', 'end_time', 'message', 'update_by', 'update_time'])

        task.status = 'paused'
        task.save(update_fields=['status', 'update_time'])
        return Response({'code': 200, 'msg': '操作成功'})

class TaskLogViewSet(BaseViewSet):
    queryset = TaskLog.objects.all()
    serializer_class = TaskLogSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task__task_name', 'status']
    ordering_fields = ['create_time']

    def get_queryset(self):
        qs = super().get_queryset()
        task_id = self.request.query_params.get('task') or self.request.query_params.get('taskId')
        status_value = self.request.query_params.get('status')
        task_name = self.request.query_params.get('taskName') or self.request.query_params.get('task_name')

        if task_id:
            try:
                qs = qs.filter(task_id=int(task_id))
            except Exception:
                pass
        if status_value:
            qs = qs.filter(status=status_value)
        if task_name:
            qs = qs.filter(task__task_name__icontains=task_name)

        return qs.order_by('-create_time')

class AlertRuleViewSet(BaseViewSet):
    queryset = AlertRule.objects.all().order_by('-create_time')
    serializer_class = AlertRuleSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        task_id = self.request.query_params.get('task') or self.request.query_params.get('taskId')
        if task_id:
            try:
                qs = qs.filter(task_id=int(task_id))
            except Exception:
                pass
        return qs.order_by('-create_time')

class AlertRecordViewSet(BaseViewSet):
    queryset = AlertRecord.objects.all()
    serializer_class = AlertRecordSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task_name', 'status']
    ordering_fields = ['trigger_time']

    def get_queryset(self):
        qs = super().get_queryset()
        task_name = self.request.query_params.get('taskName') or self.request.query_params.get('task_name')
        status_value = self.request.query_params.get('status')
        if task_name:
            qs = qs.filter(task_name__icontains=task_name)
        if status_value:
            qs = qs.filter(status=status_value)
        return qs.order_by('-trigger_time')
    
    @action(detail=True, methods=['post'])
    def handle(self, request, pk=None):
        record = self.get_object()
        note = request.data.get('note', '') if isinstance(request.data, dict) else ''
        record.status = 'handled'
        record.handle_note = note or ''
        record.handle_time = timezone.now()
        record.update_by = getattr(getattr(request, 'user', None), 'username', '') or ''
        record.save(update_fields=['status', 'handle_note', 'handle_time', 'update_by', 'update_time'])
        return Response({'code': 200, 'msg': '操作成功'})


class TaskExecutionViewSet(BaseViewSet):
    """通用任务执行记录视图集"""

    queryset = TaskExecution.objects.filter(del_flag='0').order_by('-start_time')
    serializer_class = TaskExecutionSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['task_type']
    ordering_fields = ['start_time', 'status']

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskExecutionListSerializer
        return TaskExecutionSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # 筛选条件
        task_type = self.request.query_params.get('taskType') or self.request.query_params.get('task_type')
        if task_type:
            qs = qs.filter(task_type=task_type)

        status_value = self.request.query_params.get('status')
        if status_value:
            qs = qs.filter(status=status_value)

        task_id = self.request.query_params.get('taskId') or self.request.query_params.get('task_id')
        if task_id:
            try:
                qs = qs.filter(task_id=int(task_id))
            except Exception:
                pass

        return qs

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取执行日志"""
        execution = self.get_object()

        # 筛选条件
        log_level = request.query_params.get('logLevel') or request.query_params.get('log_level')
        limit = int(request.query_params.get('limit', 100))

        logs = TaskExecutionService.get_logs(execution.id, log_level=log_level, limit=limit)

        serializer = TaskExecutionLogSerializer(logs, many=True)
        return self.ok({
            'rows': serializer.data,
            'total': len(logs)
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消正在运行的任务"""
        execution = self.get_object()

        if execution.status != 'running':
            return self.error('只有运行中的任务可以取消')

        success = TaskExecutionService.cancel_execution(execution.id)
        if success:
            return self.ok({'message': '任务已取消'})
        else:
            return self.error('取消任务失败')

    @action(detail=True, methods=['get'])
    def etl_details(self, request, pk=None):
        """获取ETL特定的执行详情"""
        execution = self.get_object()

        if execution.task_type != 'etl':
            return self.error('此记录不是ETL任务执行记录')

        try:
            etl_details = execution.etl_details
            return self.ok({
                'execution_id': execution.id,
                'task_id': execution.task_id,
                'etl_execution_id': etl_details.id if etl_details else None,
                'source_rows': etl_details.rows_read if etl_details else 0,
                'target_rows': etl_details.rows_written if etl_details else 0,
                'rows_failed': etl_details.rows_failed if etl_details else 0,
            })
        except Exception:
            return self.error('ETL执行详情不存在')


class TaskExecutionLogViewSet(BaseViewSet):
    """任务执行日志视图集"""

    queryset = TaskExecutionLog.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = TaskExecutionLogSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['message']
    ordering_fields = ['create_time']
    filterset_fields = ['execution', 'logLevel']

    def get_queryset(self):
        qs = super().get_queryset()

        execution_id = self.request.query_params.get('executionId') or self.request.query_params.get('execution_id')
        if execution_id:
            try:
                qs = qs.filter(execution_id=int(execution_id))
            except Exception:
                pass

        log_level = self.request.query_params.get('logLevel') or self.request.query_params.get('log_level')
        if log_level:
            qs = qs.filter(log_level=log_level)

        return qs
