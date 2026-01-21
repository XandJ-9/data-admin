from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import uuid

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission

from .models import IntegrationTask, TaskExecutionLog, DataLineage, IntegrationTaskVersion
from .serializers import (
    IntegrationTaskSerializer,
    IntegrationTaskQuerySerializer,
    IntegrationTaskCreateSerializer,
    IntegrationTaskUpdateSerializer,
    TaskExecutionLogSerializer,
    TaskExecutionLogQuerySerializer,
    DataLineageSerializer,
    DataLineageQuerySerializer,
    IntegrationTaskVersionSerializer,
)


class IntegrationTaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = IntegrationTask.objects.filter(del_flag='0').order_by('-update_time')
    serializer_class = IntegrationTaskSerializer
    update_body_serializer_class = IntegrationTaskUpdateSerializer
    update_body_id_field = 'taskId'

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        name = params.get('taskName') or params.get('name')
        if name:
            qs = qs.filter(name__icontains=name)
        t = params.get('taskType') or params.get('type')
        if t:
            qs = qs.filter(type=t)
        status = params.get('status')
        if status in ('0', '1'):
            qs = qs.filter(status=status)
        return qs

    def list(self, request, *args, **kwargs):
        q = IntegrationTaskQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return self.error('查询参数错误')
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        ser = IntegrationTaskCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # 处理外键字段
        validated_data = ser.validated_data.copy()
        source_datasource_id = validated_data.pop('sourceDatasourceId', None)
        target_datasource_id = validated_data.pop('targetDatasourceId', None)

        # 创建任务
        task = IntegrationTask(**validated_data)
        if source_datasource_id:
            from apps.datasource.models import DataSource
            task.source_datasource_id = source_datasource_id
        if target_datasource_id:
            from apps.datasource.models import DataSource
            task.target_datasource_id = target_datasource_id

        self.perform_create(task)

        return self.data(IntegrationTaskSerializer(task).data)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        ser = IntegrationTaskUpdateSerializer(instance=obj, data=request.data)
        ser.is_valid(raise_exception=True)

        # 处理外键字段
        validated_data = ser.validated_data.copy()
        if 'sourceDatasourceId' in validated_data:
            from apps.datasource.models import DataSource
            validated_data['source_datasource_id'] = validated_data.pop('sourceDatasourceId')
        if 'targetDatasourceId' in validated_data:
            from apps.datasource.models import DataSource
            validated_data['target_datasource_id'] = validated_data.pop('targetDatasourceId')

        self.perform_update(ser)
        return self.data(ser.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        手动触发任务执行

        POST /dataetl/{id}/execute
        """
        task = self.get_object()

        try:
            from .models import TaskExecutionLog
            from .executors.factory import get_executor

            # 创建执行日志
            execution_log = TaskExecutionLog.objects.create(
                task=task,
                execution_id=f"{task.id}_{uuid.uuid4().hex[:12]}",
                status='running',
                triggered_by='manual',
                create_by=request.user.username if request.user.is_authenticated else '',
                update_by=request.user.username if request.user.is_authenticated else '',
            )

            # 获取执行器并执行
            executor = get_executor(task, execution_log)
            is_valid, error_msg = executor.validate()

            if not is_valid:
                execution_log.status = 'failed'
                execution_log.error_message = error_msg
                execution_log.save()
                return self.error(f'任务验证失败: {error_msg}')

            # 执行任务
            result = executor.execute()

            # 更新执行日志
            executor.update_execution_log(result)

            # 同步血缘关系
            if result['status'] == 'success':
                executor._sync_lineage()

            return self.data({
                'executionId': execution_log.execution_id,
                'status': result['status'],
                'rowsRead': result.get('rows_read', 0),
                'rowsWritten': result.get('rows_written', 0),
                'message': '执行成功' if result['status'] == 'success' else result.get('error_message', '')
            })

        except Exception as e:
            return self.error(f'任务执行失败: {str(e)}')

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        查询任务执行历史

        GET /dataetl/{id}/executions
        """
        task = self.get_object()
        logs = task.executions.all().order_by('-create_time')[:50]

        from django.core.paginator import Paginator
        paginator = Paginator(logs, 10)
        page = request.query_params.get('pageNum', 1)
        logs_page = paginator.get_page(page)

        serializer = TaskExecutionLogSerializer(logs_page, many=True)
        return self.data({
            'rows': serializer.data,
            'total': paginator.count
        })

    @action(detail=False, methods=['get'])
    def lineage(self, request):
        """
        查询数据血缘

        GET /dataetl/lineage/?table=user&direction=downstream
        """
        table = request.query_params.get('table')
        direction = request.query_params.get('direction', 'downstream')

        if not table:
            return self.error('table参数必填')

        if direction == 'downstream':
            lineages = DataLineage.objects.filter(source_table=table, del_flag='0')
        else:
            lineages = DataLineage.objects.filter(target_table=table, del_flag='0')

        lineages = lineages.select_related().order_by('-create_time')[:100]

        serializer = DataLineageSerializer(lineages, many=True)
        return self.data(serializer.data)


class TaskExecutionLogViewSet(BaseViewSet):
    """任务执行日志ViewSet"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = TaskExecutionLog.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = TaskExecutionLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        task_id = self.request.query_params.get('taskId')
        status = self.request.query_params.get('status')

        if task_id:
            qs = qs.filter(task_id=task_id)
        if status:
            qs = qs.filter(status=status)

        return qs

    def list(self, request, *args, **kwargs):
        q = TaskExecutionLogQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return self.error('查询参数错误')
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """获取执行日志详情"""
        log = self.get_object()

        # 返回详细信息
        data = TaskExecutionLogSerializer(log).data

        # 附加堆栈跟踪
        if log.stack_trace:
            data['stackTrace'] = log.stack_trace

        return self.data(data)


class DataLineageViewSet(BaseViewSet):
    """数据血缘ViewSet"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataLineage.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = DataLineageSerializer

    def list(self, request, *args, **kwargs):
        q = DataLineageQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return self.error('查询参数错误')

        table = request.query_params.get('table')
        direction = request.query_params.get('direction', 'downstream')

        if table:
            if direction == 'downstream':
                self.queryset = self.queryset.filter(source_table=table)
            else:
                self.queryset = self.queryset.filter(target_table=table)

        return super().list(request, *args, **kwargs)


class IntegrationTaskVersionViewSet(BaseViewSet):
    """任务版本管理ViewSet"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = IntegrationTaskVersion.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = IntegrationTaskVersionSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        激活指定版本

        POST /dataetl/version/{id}/activate
        """
        version = self.get_object()
        task = version.task

        # 取消其他版本
        IntegrationTaskVersion.objects.filter(
            task=task, is_active=True, del_flag='0'
        ).update(is_active=False)

        # 激活当前版本
        version.is_active = True
        version.save(update_fields=['is_active'])

        return self.ok('版本激活成功')

    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        版本对比

        GET /dataetl/version/compare?version1=<id>&version2=<id>
        """
        from jsondiff import diff

        version1_id = request.query_params.get('version1')
        version2_id = request.query_params.get('version2')

        if not version1_id or not version2_id:
            return self.error('version1和version2参数必填')

        try:
            v1 = IntegrationTaskVersion.objects.get(id=version1_id)
            v2 = IntegrationTaskVersion.objects.get(id=version2_id)

            # 比对JSON差异
            differences = list(diff(v1.config_snapshot, v2.config_snapshot))

            return self.data({
                'version1': IntegrationTaskVersionSerializer(v1).data,
                'version2': IntegrationTaskVersionSerializer(v2).data,
                'differences': differences
            })

        except IntegrationTaskVersion.DoesNotExist:
            return self.error('版本不存在')
        except Exception as e:
            return self.error(f'版本对比失败: {str(e)}')
