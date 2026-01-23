"""
ETL模块视图 - 简化版
基于场景驱动的RESTful API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from .models import ETLTask, ETLExecution, ETLTemplate, ETLTaskDependency
from .serializers import (
    ETLTaskSerializer,
    ETLTaskCreateSerializer,
    ETLExecutionSerializer,
    ETLExecutionListSerializer,
    ETLTemplateSerializer,
    ETLTaskDependencySerializer,
    ETLTaskDependencyCreateSerializer,
    DependencyCheckSerializer,
)
from .services.dependency import DependencyService


class ETLTaskViewSet(BaseViewSet):
    """ETL任务视图集"""

    serializer_class = ETLTaskSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]

    def get_queryset(self):
        queryset = ETLTask.objects.filter(del_flag='0')

        # 筛选条件
        scenario = self.request.query_params.get('scenario')
        if scenario:
            queryset = queryset.filter(scenario=scenario)

        task_status = self.request.query_params.get('status')
        if task_status:
            queryset = queryset.filter(status=task_status)

        schedule_type = self.request.query_params.get('schedule_type')
        if schedule_type:
            queryset = queryset.filter(schedule_type=schedule_type)

        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        return queryset.order_by('-create_time')

    def get_serializer_class(self):
        if self.action == 'create':
            return ETLTaskCreateSerializer
        return ETLTaskSerializer

    @action(detail=False, methods=['get'])
    def scenarios(self, request):
        """获取支持的场景列表"""
        scenarios = [
            {
                'value': 'biz_to_stg',
                'label': '业务库 → STG层',
                'description': '将业务系统数据库的数据同步到数仓STG缓冲层',
                'icon': 'database',
                'color': '#409EFF',
                'tags': ['推荐新手', '全量同步'],
                'requiredFields': ['source_datasource', 'source_table'],
                'optionalFields': ['where_condition', 'batch_size'],
                'defaults': {
                    'sync_mode': 'full',
                    'executor_type': 'datax',
                    'target_layer': 'stg',
                    'batch_size': 10000
                }
            },
            {
                'value': 'stg_to_ods',
                'label': 'STG层 → ODS层',
                'description': '对STG层数据进行清洗、标准化后同步到ODS原始层',
                'icon': 'folder',
                'color': '#67C23A',
                'tags': ['数据标准化', '增量同步'],
                'requiredFields': ['source_table'],
                'optionalFields': ['transform_rules', 'incremental_field'],
                'defaults': {
                    'sync_mode': 'incremental',
                    'executor_type': 'spark_sql',
                    'target_layer': 'ods',
                    'batch_size': 50000
                }
            },
            {
                'value': 'warehouse_transform',
                'label': '数仓层计算转换',
                'description': '在DWD/DWS/ADS层使用Spark SQL进行复杂的数据聚合和计算',
                'icon': 'data-analysis',
                'color': '#F56C6C',
                'tags': ['高级用户', 'SQL开发'],
                'requiredFields': ['target_layer', 'sql_script'],
                'optionalFields': ['schedule_cron'],
                'defaults': {
                    'sync_mode': 'full',
                    'executor_type': 'spark_sql',
                    'schedule_type': 'scheduled'
                }
            },
            {
                'value': 'warehouse_to_biz',
                'label': '数仓层 → 业务库',
                'description': '将数仓计算结果推送到业务数据库',
                'icon': 'upload',
                'color': '#E6A23C',
                'tags': ['结果导出', '定时推送'],
                'requiredFields': ['source_table', 'target_datasource', 'target_table'],
                'optionalFields': ['batch_size', 'concurrency'],
                'defaults': {
                    'sync_mode': 'full',
                    'executor_type': 'datax',
                    'target_layer': 'ads',
                    'batch_size': 10000
                }
            },
            {
                'value': 'db_to_db',
                'label': '数据库互相同步',
                'description': '在不同数据库之间同步数据，支持异构数据库',
                'icon': 'switch',
                'color': '#909399',
                'tags': ['灵活配置', '数据迁移'],
                'requiredFields': ['source_datasource', 'source_table', 'target_datasource', 'target_table'],
                'optionalFields': ['where_condition', 'incremental_field', 'batch_size'],
                'defaults': {
                    'sync_mode': 'incremental',
                    'executor_type': 'datax',
                    'batch_size': 10000
                }
            }
        ]

        return self.ok({'scenarios': scenarios})

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """手动执行任务"""
        task = self.get_object()

        # 检查任务状态
        if task.status == '1':
            return self.error('任务已停用，无法执行')

        # 检查是否有正在运行的执行
        running_exec = ETLExecution.objects.filter(
            task=task,
            status='running'
        ).first()

        if running_exec:
            return self.error(f'任务正在运行中，执行ID: {running_exec.id}')

        # 创建新的执行记录
        execution = ETLExecution.objects.create(
            task=task,
            status='pending',
            execution_snapshot=self._get_task_snapshot(task)
        )

        # TODO: 实际执行任务的逻辑
        # 这里需要调用执行器来执行任务
        # from apps.dataetl.executors.executor_factory import get_executor
        # executor = get_executor(task)
        # executor.execute(execution)

        return self.ok({
            'execution_id': execution.id,
            'message': '任务已提交执行'
        })

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止正在运行的任务"""
        task = self.get_object()

        running_exec = ETLExecution.objects.filter(
            task=task,
            status='running'
        ).first()

        if not running_exec:
            return self.error('没有正在运行的任务')

        # TODO: 实际停止任务的逻辑
        running_exec.status = 'cancelled'
        running_exec.save()

        return self.ok({'message': '任务已停止'})

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """获取任务的执行历史"""
        task = self.get_object()
        executions = task.executions.all()[:20]  # 最近20次
        serializer = ETLExecutionListSerializer(executions, many=True)
        return self.ok({
            'rows': serializer.data,
            'total': executions.count()
        })

    @action(detail=False, methods=['get'])
    def templates(self, request):
        """获取任务模板"""
        scenario = request.query_params.get('scenario')

        templates = ETLTemplate.objects.filter(
            del_flag='0',
            is_system=True
        )

        if scenario:
            templates = templates.filter(scenario=scenario)

        serializer = ETLTemplateSerializer(templates, many=True)
        return self.ok({
            'rows': serializer.data,
            'total': templates.count()
        })

    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """获取任务的所有依赖"""
        task = self.get_object()
        dependencies = ETLTaskDependency.objects.filter(successor=task)

        # 检查依赖是否满足
        can_execute, unsatisfied = DependencyService.check_dependencies_satisfied(task.id)

        serializer = ETLTaskDependencySerializer(dependencies, many=True)
        return self.ok({
            'rows': serializer.data,
            'total': dependencies.count(),
            'can_execute': can_execute,
            'unsatisfied_dependencies': unsatisfied
        })

    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """添加任务依赖"""
        task = self.get_object()  # successor

        serializer = ETLTaskDependencyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        predecessor_id = serializer.validated_data['predecessor_id']

        # 使用 DependencyService 添加依赖
        success, message = DependencyService.add_dependency(
            task_id=task.id,
            dependency_id=predecessor_id
        )

        if success:
            return self.ok({'message': message})
        else:
            return self.error(message)

    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, pk=None):
        """移除任务依赖"""
        task = self.get_object()

        dependency_id = request.data.get('dependency_id')
        if not dependency_id:
            return self.error('请提供 dependency_id')

        success, message = DependencyService.remove_dependency(
            task_id=task.id,
            dependency_id=dependency_id
        )

        if success:
            return self.ok({'message': message})
        else:
            return self.error(message)

    @action(detail=True, methods=['get'])
    def check_dependencies(self, request, pk=None):
        """检查任务是否可以执行（依赖是否满足）"""
        task = self.get_object()

        can_execute, message = DependencyService.can_execute_task(task.id)

        if can_execute:
            return self.ok({
                'can_execute': True,
                'message': '任务可以执行'
            })
        else:
            return self.ok({
                'can_execute': False,
                'message': message
            })

    @action(detail=True, methods=['get'])
    def dependency_chain(self, request, pk=None):
        """获取完整依赖链"""
        task = self.get_object()

        chain = DependencyService.get_dependency_chain(task.id)

        return self.ok({
            'chain': [
                {
                    'id': t.id,
                    'name': t.name,
                    'scenario': t.scenario,
                    'status': t.status
                }
                for t in chain
            ]
        })

    def _get_task_snapshot(self, task):
        """获取任务配置快照"""
        return {
            'name': task.name,
            'scenario': task.scenario,
            'source_datasource_id': task.source_datasource_id,
            'source_table': task.source_table,
            'target_datasource_id': task.target_datasource_id,
            'target_table': task.target_table,
            'sync_mode': task.sync_mode,
            'field_mappings': task.field_mappings,
            'sql_script': task.sql_script,
        }


class ETLExecutionViewSet(BaseViewSet):
    """ETL执行记录视图集"""

    serializer_class = ETLExecutionSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]

    def get_queryset(self):
        queryset = ETLExecution.objects.filter(del_flag='0')

        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        exec_status = self.request.query_params.get('status')
        if exec_status:
            queryset = queryset.filter(status=exec_status)

        return queryset.order_by('-create_time')

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取执行日志详情"""
        execution = self.get_object()
        return self.ok({
            'logs': execution.logs,
            'error_message': execution.error_message
        })

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """获取执行进度（用于SSE推送）"""
        execution = self.get_object()

        return self.ok({
            'status': execution.status,
            'progress': execution.progress,
            'current_stage': execution.current_stage,
            'rows_read': execution.rows_read,
            'rows_written': execution.rows_written,
            'duration': execution.duration,
            'start_time': execution.start_time,
            'end_time': execution.end_time
        })


class ETLTemplateViewSet(BaseViewSet):
    """ETL模板视图集"""

    serializer_class = ETLTemplateSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]

    def get_queryset(self):
        queryset = ETLTemplate.objects.filter(del_flag='0')

        scenario = self.request.query_params.get('scenario')
        if scenario:
            queryset = queryset.filter(scenario=scenario)

        is_system = self.request.query_params.get('is_system')
        if is_system is not None:
            queryset = queryset.filter(is_system=is_system)

        return queryset.order_by('-is_system', '-usage_count', '-create_time')

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """应用模板创建任务"""
        template = self.get_object()

        # 增加使用次数
        template.usage_count += 1
        template.save()

        return self.ok({
            'template_config': template.template_config,
            'message': f'已应用模板: {template.name}'
        })
