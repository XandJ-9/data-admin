"""
ETL Views

This module defines ViewSets for ETL task management.
"""

import uuid
import threading
from datetime import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from .models import ETLTask, ETLTaskVersion, ETLFieldMapping, ETLExecutionLog
from .serializers import (
    ETLTaskSerializer, ETLTaskCreateSerializer, ETLTaskUpdateSerializer,
    ETLTaskQuerySerializer, ETLTaskSimpleSerializer,
    ETLTaskVersionSerializer, ETLTaskVersionCreateSerializer,
    ETLFieldMappingSerializer, ETLFieldMappingCreateSerializer,
    ETLFieldMappingUpdateSerializer, ETLFieldMappingQuerySerializer,
    ETLExecutionLogSerializer, ETLExecutionLogCreateSerializer,
    ETLExecutionLogQuerySerializer
)
from .executors import ExecutorFactory


# ==================== ETLTask ViewSet ====================

class ETLTaskViewSet(BaseViewSet):
    """ETL任务视图集合"""

    queryset = ETLTask.objects.all()
    serializer_class = ETLTaskSerializer
    create_serializer_class = ETLTaskCreateSerializer
    update_serializer_class = ETLTaskUpdateSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        task_name = self.request.query_params.get('taskName')
        task_code = self.request.query_params.get('taskCode')
        etl_type = self.request.query_params.get('etlType')
        executor_type = self.request.query_params.get('executorType')
        status_value = self.request.query_params.get('status')
        source_datasource_id = self.request.query_params.get('sourceDatasourceId')
        target_datasource_id = self.request.query_params.get('targetDatasourceId')

        # 应用筛选条件
        if task_name:
            queryset = queryset.filter(task_name__icontains=task_name)
        if task_code:
            queryset = queryset.filter(task_code__icontains=task_code)
        if etl_type:
            queryset = queryset.filter(etl_type=etl_type)
        if executor_type:
            queryset = queryset.filter(executor_type=executor_type)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if source_datasource_id:
            queryset = queryset.filter(source_datasource_id=source_datasource_id)
        if target_datasource_id:
            queryset = queryset.filter(target_datasource_id=target_datasource_id)

        return queryset

    @action(detail=False, methods=['get'], url_path='simple')
    def simple_list(self, request):
        """获取简单列表（用于下拉框）"""
        queryset = self.get_queryset()
        serializer = ETLTaskSimpleSerializer(queryset, many=True)
        return self.data(serializer.data)

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        """
        执行ETL任务

        创建执行日志并异步执行任务
        """
        task = self.get_object()

        # 检查任务状态
        if task.status != '0':
            return Response({
                'code': 500,
                'msg': '任务已停用，无法执行'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 生成执行ID
        execution_id = f"ETL-{uuid.uuid4().hex[:16].upper()}"

        # 创建执行日志
        log = ETLExecutionLog.objects.create(
            task=task,
            execution_id=execution_id,
            status='pending',
            trigger_type='manual',
            executed_by=request.user.username if request.user.is_authenticated else 'system',
            executor_params=task.executor_params
        )

        # 异步执行任务
        thread = threading.Thread(
            target=self._execute_async,
            args=(task, log)
        )
        thread.daemon = True
        thread.start()

        return self.data({
            'executionId': execution_id,
            'message': '任务已提交执行'
        })

    def _execute_async(self, task, log):
        """
        异步执行ETL任务

        Args:
            task: ETLTask实例
            log: ETLExecutionLog实例
        """
        try:
            # 更新状态为执行中
            log.status = 'running'
            log.start_time = timezone.now()
            log.save()

            # 创建执行器实例
            executor = ExecutorFactory.create_executor(
                task.executor_type,
                task,
                task.executor_params
            )

            # 验证配置
            is_valid, error_message = executor.validate()
            if not is_valid:
                raise Exception(f"任务配置验证失败: {error_message}")

            # 执行任务
            result = executor.execute()

            # 更新执行日志
            log.status = result.get('status', 'failed')
            log.end_time = timezone.now()
            log.duration_seconds = result.get('duration_seconds')
            log.total_rows = result.get('total_rows')
            log.success_rows = result.get('success_rows')
            log.failed_rows = result.get('failed_rows')
            log.error_message = result.get('error_message')
            log.save()

        except Exception as e:
            # 执行失败
            log.status = 'failed'
            log.end_time = timezone.now()
            if log.start_time:
                log.duration_seconds = int((log.end_time - log.start_time).total_seconds())
            log.error_message = str(e)
            log.save()

    @action(detail=True, methods=['post'], url_path='create-version')
    def create_version(self, request, pk=None):
        """
        创建任务版本快照

        保存当前任务配置为新版本
        """
        task = self.get_object()

        # 获取最新的版本号
        latest_version = ETLTaskVersion.objects.filter(task=task).order_by('-version_number').first()
        version_number = (latest_version.version_number + 1) if latest_version else 1

        # 创建版本快照
        change_log = request.data.get('changeLog', '')

        # 创建配置快照
        config_snapshot = {
            'taskName': task.task_name,
            'taskCode': task.task_code,
            'description': task.description,
            'etlType': task.etl_type,
            'executorType': task.executor_type,
            'executeStrategy': task.execute_strategy,
            'sourceDatasourceId': task.source_datasource_id,
            'targetDatasourceId': task.target_datasource_id,
            'sourceTableId': task.source_table_id,
            'targetTable': task.target_table,
            'sqlConfig': task.sql_config,
            'executorParams': task.executor_params,
            'status': task.status,
        }

        # 取消所有旧版本的当前标记
        ETLTaskVersion.objects.filter(task=task).update(is_current=False)

        # 创建新版本
        version = ETLTaskVersion.objects.create(
            task=task,
            version_number=version_number,
            config_snapshot=config_snapshot,
            change_log=change_log,
            is_current=True,
            create_by=request.user.username if request.user.is_authenticated else 'system'
        )

        serializer = ETLTaskVersionSerializer(version)
        return self.data(serializer.data)

    @action(detail=True, methods=['get'], url_path='versions')
    def task_versions(self, request, pk=None):
        """获取任务的所有版本"""
        task = self.get_object()
        versions = ETLTaskVersion.objects.filter(task=task).order_by('-version_number')
        serializer = ETLTaskVersionSerializer(versions, many=True)
        return self.data(serializer.data)

    @action(detail=True, methods=['post'], url_path='rollback')
    def rollback_version(self, request, pk=None):
        """
        回滚到指定版本

        Body参数:
            versionNumber: 要回滚到的版本号
        """
        task = self.get_object()
        version_number = request.data.get('versionNumber')

        if not version_number:
            return Response({
                'code': 400,
                'msg': '请指定版本号'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取目标版本
        try:
            version = ETLTaskVersion.objects.get(task=task, version_number=version_number)
        except ETLTaskVersion.DoesNotExist:
            return Response({
                'code': 404,
                'msg': '版本不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 恢复配置
        snapshot = version.config_snapshot
        task.task_name = snapshot.get('taskName', task.task_name)
        task.description = snapshot.get('description', task.description)
        task.etl_type = snapshot.get('etlType', task.etl_type)
        task.executor_type = snapshot.get('executorType', task.executor_type)
        task.execute_strategy = snapshot.get('executeStrategy', task.execute_strategy)
        task.source_datasource_id = snapshot.get('sourceDatasourceId', task.source_datasource_id)
        task.target_datasource_id = snapshot.get('targetDatasourceId', task.target_datasource_id)
        task.source_table_id = snapshot.get('sourceTableId', task.source_table_id)
        task.target_table = snapshot.get('targetTable', task.target_table)
        task.sql_config = snapshot.get('sqlConfig', task.sql_config)
        task.executor_params = snapshot.get('executorParams', task.executor_params)
        task.status = snapshot.get('status', task.status)
        task.save()

        return self.data({'message': f'已回滚到版本 {version_number}'})


# ==================== ETLFieldMapping ViewSet ====================

class ETLFieldMappingViewSet(BaseViewSet):
    """ETL字段映射视图集合"""

    queryset = ETLFieldMapping.objects.all()
    serializer_class = ETLFieldMappingSerializer
    create_serializer_class = ETLFieldMappingCreateSerializer
    update_serializer_class = ETLFieldMappingUpdateSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        task_id = self.request.query_params.get('taskId')
        source_field_name = self.request.query_params.get('sourceFieldName')
        target_field_name = self.request.query_params.get('targetFieldName')

        # 应用筛选条件
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if source_field_name:
            queryset = queryset.filter(source_field_name__icontains=source_field_name)
        if target_field_name:
            queryset = queryset.filter(target_field_name__icontains=target_field_name)

        return queryset

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_create(self, request):
        """批量创建字段映射"""
        mappings_data = request.data.get('mappings', [])

        if not mappings_data:
            return Response({
                'code': 400,
                'msg': '请提供映射数据'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_mappings = []
        for mapping_data in mappings_data:
            serializer = ETLFieldMappingCreateSerializer(data=mapping_data)
            if serializer.is_valid():
                mapping = serializer.save()
                created_mappings.append(mapping)

        serializer = ETLFieldMappingSerializer(created_mappings, many=True)
        return self.data(serializer.data)


# ==================== ETLExecutionLog ViewSet ====================

class ETLExecutionLogViewSet(BaseViewSet):
    """ETL执行日志视图集合"""

    queryset = ETLExecutionLog.objects.all()
    serializer_class = ETLExecutionLogSerializer
    create_serializer_class = ETLExecutionLogCreateSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        task_id = self.request.query_params.get('taskId')
        execution_id = self.request.query_params.get('executionId')
        status_value = self.request.query_params.get('status')
        trigger_type = self.request.query_params.get('triggerType')
        executed_by = self.request.query_params.get('executedBy')

        # 应用筛选条件
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if execution_id:
            queryset = queryset.filter(execution_id__icontains=execution_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        if executed_by:
            queryset = queryset.filter(executed_by__icontains=executed_by)

        return queryset

    def create(self, request, *args, **kwargs):
        """禁用直接创建执行日志"""
        return Response({
            'code': 403,
            'msg': '执行日志由系统自动创建，不允许手动创建'
        }, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """禁用更新执行日志"""
        return Response({
            'code': 403,
            'msg': '执行日志不允许修改'
        }, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """禁用删除执行日志"""
        return Response({
            'code': 403,
            'msg': '执行日志不允许删除'
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'], url_path='detail')
    def execution_detail(self, request, pk=None):
        """获取执行日志详细信息"""
        log = self.get_object()
        serializer = ETLExecutionLogSerializer(log)
        return self.data(serializer.data)
