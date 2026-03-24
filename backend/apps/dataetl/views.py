"""
ETL Views

This module defines ViewSets for ETL task management.
视图层只负责请求处理和响应，业务逻辑在服务层
"""

from django.utils import timezone
from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from .models import (
    ETLTask, ETLTaskVersion, ETLFieldMapping, ETLExecutionLog, ETLWatermark,
    ETLTaskTemplate, ETLQualityRule, ETLQualityResult, ETLExecutionProgress
)
from .serializers import (
    ETLTaskSerializer, ETLTaskCreateSerializer, ETLTaskUpdateSerializer,
    ETLTaskQuerySerializer, ETLTaskSimpleSerializer,
    ETLTaskVersionSerializer, ETLTaskVersionCreateSerializer,
    ETLFieldMappingSerializer, ETLFieldMappingCreateSerializer,
    ETLFieldMappingUpdateSerializer, ETLFieldMappingQuerySerializer,
    ETLExecutionLogSerializer, ETLExecutionLogCreateSerializer,
    ETLExecutionLogQuerySerializer,
    ETLWatermarkSerializer, ETLWatermarkQuerySerializer,
    DataXConfigValidateSerializer, DataXConfigGenerateSerializer,
    ETLTaskTemplateSerializer, ETLTaskTemplateCreateSerializer, ETLTaskTemplateQuerySerializer,
    ETLQualityRuleSerializer, ETLQualityRuleCreateSerializer, ETLQualityRuleQuerySerializer,
    ETLQualityResultSerializer, ETLQualityResultQuerySerializer,
    ETLExecutionProgressSerializer,
)
from .services import (
    TaskService, QualityService, MonitoringService,
    ExecutionService, VersionService, ConfigService,
)


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

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """获取ETL任务统计数据"""
        queryset = self.get_queryset()
        task_stats = queryset.aggregate(
            total=Count('id'),
            enabled=Count('id', filter=Q(status='0')),
        )

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        execution_stats = ETLExecutionLog.objects.filter(
            create_time__gte=today_start
        ).aggregate(
            today_executions=Count('id'),
            failed_executions=Count('id', filter=Q(status='failed')),
        )

        return self.data({
            'totalTasks': task_stats['total'],
            'enabledTasks': task_stats['enabled'],
            'todayExecutions': execution_stats['today_executions'],
            'failedExecutions': execution_stats['failed_executions'],
        })

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_task(self, request, pk=None):
        """执行ETL任务"""
        task = self.get_object()

        try:
            executed_by = request.user.username if request.user.is_authenticated else 'system'
            execution_service = ExecutionService()
            execution_id = execution_service.submit_task(task, executed_by, 'manual')

            return self.data({
                'executionId': execution_id,
                'message': '任务已提交执行'
            })
        except ValueError as e:
            return Response({
                'code': 500,
                'msg': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'提交任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='create-version')
    def create_version(self, request, pk=None):
        """创建任务版本快照"""
        task = self.get_object()
        change_log = request.data.get('changeLog', '')
        create_by = request.user.username if request.user.is_authenticated else 'system'

        try:
            version = VersionService.create_version(task, change_log, create_by)
            serializer = ETLTaskVersionSerializer(version)
            return self.data(serializer.data)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'创建版本失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='versions')
    def task_versions(self, request, pk=None):
        """获取任务的所有版本"""
        task = self.get_object()
        versions = VersionService.get_task_versions(task)
        serializer = ETLTaskVersionSerializer(versions, many=True)
        return self.data(serializer.data)

    @action(detail=True, methods=['post'], url_path='rollback')
    def rollback_version(self, request, pk=None):
        """回滚到指定版本"""
        task = self.get_object()
        version_number = request.data.get('versionNumber')

        if not version_number:
            return Response({
                'code': 400,
                'msg': '请指定版本号'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            VersionService.rollback_version(task, version_number)
            return self.data({'message': f'已回滚到版本 {version_number}'})
        except ValueError as e:
            return Response({
                'code': 404,
                'msg': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'回滚失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='validate-config')
    def validate_config(self, request, pk=None):
        """验证DataX配置"""
        task = self.get_object()

        try:
            config_service = ConfigService()
            is_valid, warnings, config = config_service.validate_datax_config(task)

            return self.data({
                'valid': is_valid,
                'warnings': warnings,
                'config': config
            })
        except ValueError as e:
            return Response({
                'code': 400,
                'msg': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'配置验证失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='datx-config')
    def generate_datx_config(self, request, pk=None):
        """生成DataX JSON配置"""
        task = self.get_object()
        execution_date = request.query_params.get('executionDate')

        try:
            config_service = ConfigService()
            result = config_service.generate_datax_config(task, execution_date)
            return self.data(result)
        except ValueError as e:
            return Response({
                'code': 400,
                'msg': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'配置生成失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='execute-dry-run')
    def dry_run(self, request, pk=None):
        """模拟执行（不实际写入数据）"""
        task = self.get_object()

        try:
            config_service = ConfigService()
            result = config_service.dry_run(task)
            return self.data(result)
        except ValueError as e:
            return Response({
                'code': 400,
                'msg': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'模拟执行失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='from-template')
    def create_from_template(self, request):
        """从模板创建任务"""
        template_id = request.data.get('templateId')
        params = request.data.get('params', {})

        if not template_id:
            return Response({
                'code': 400,
                'msg': '请提供模板ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = TaskService.create_task_from_template(template_id, params)
            serializer = ETLTaskSerializer(task)
            return self.data(serializer.data)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'创建任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='clone')
    def clone_task(self, request, pk=None):
        """克隆任务"""
        task = self.get_object()
        new_task_name = request.data.get('taskName')
        new_task_code = request.data.get('taskCode')

        if not new_task_name or not new_task_code:
            return Response({
                'code': 400,
                'msg': '请提供新任务名称和编码'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_task = TaskService.clone_task(task.id, new_task_name, new_task_code)
            serializer = ETLTaskSerializer(new_task)
            return self.data(serializer.data)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'克隆任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='statistics')
    def get_statistics(self, request, pk=None):
        """获取任务统计信息"""
        task = self.get_object()
        days = int(request.query_params.get('days', 7))

        try:
            stats = MonitoringService.get_task_statistics(task.id, days)
            return self.data(stats)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取统计信息失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        try:
            task_id = mappings_data[0].get('taskId') if mappings_data else None
            if not task_id:
                raise ValueError('缺少taskId')

            count = TaskService.create_field_mapping_batch(task_id, mappings_data)

            # 获取创建后的映射列表
            mappings = ETLFieldMapping.objects.filter(task_id=task_id)
            serializer = ETLFieldMappingSerializer(mappings, many=True)
            return self.data({
                'message': f'成功创建 {count} 个字段映射',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'批量创建失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        # 日期范围筛选
        start_time = self.request.query_params.get('startTime')
        end_time = self.request.query_params.get('endTime')
        if start_time:
            queryset = queryset.filter(create_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(create_time__lte=end_time)

        return queryset

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """获取执行日志统计数据"""
        queryset = self.get_queryset()
        stats = queryset.aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
            avg_duration=Avg('duration_seconds', filter=Q(duration_seconds__isnull=False)),
        )

        total = stats['total'] or 0
        success = stats['success'] or 0
        failed = stats['failed'] or 0
        avg_duration = round(stats['avg_duration'] or 0, 2)

        return self.data({
            'total': total,
            'success': success,
            'failed': failed,
            'successRate': round(success / total * 100, 2) if total > 0 else 0,
            'failedRate': round(failed / total * 100, 2) if total > 0 else 0,
            'avgDuration': avg_duration,
        })

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

    @action(detail=True, methods=['get'], url_path='progress')
    def get_progress(self, request, pk=None):
        """获取执行进度（实时）"""
        execution = self.get_object()

        try:
            metrics = MonitoringService.get_execution_metrics(execution.execution_id)
            return self.data(metrics)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取进度失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_execution(self, request, pk=None):
        """取消执行"""
        execution = self.get_object()

        if execution.status != 'running':
            return Response({
                'code': 400,
                'msg': '任务不在执行状态'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            execution_service = ExecutionService()
            success = execution_service.cancel_execution(execution)

            if success:
                return self.data({'message': '任务已取消'})
            else:
                return Response({
                    'code': 500,
                    'msg': '取消任务失败'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'取消任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ETLWatermark ViewSet ====================

class ETLWatermarkViewSet(BaseViewSet):
    """ETL水印视图集合"""

    queryset = ETLWatermark.objects.all()
    serializer_class = ETLWatermarkSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        task_id = self.request.query_params.get('taskId')

        # 应用筛选条件
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-task')
    def get_watermark_by_task(self, request):
        """获取任务的最新水印值"""
        task_id = request.query_params.get('taskId')
        if not task_id:
            return Response({
                'code': 400,
                'msg': '请提供任务ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            watermark = ETLWatermark.objects.filter(
                task_id=task_id
            ).order_by('-update_time').first()

            if watermark:
                serializer = ETLWatermarkSerializer(watermark)
                return self.data(serializer.data)
            else:
                return self.data({
                    'watermarkValue': None,
                    'message': '该任务暂无水印记录'
                })

        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取水印失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """禁用直接创建水印"""
        return Response({
            'code': 403,
            'msg': '水印由系统自动管理，不允许手动创建'
        }, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """禁用更新水印"""
        return Response({
            'code': 403,
            'msg': '水印由系统自动管理，不允许手动修改'
        }, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """禁用删除水印"""
        return Response({
            'code': 403,
            'msg': '水印不允许删除'
        }, status=status.HTTP_403_FORBIDDEN)


# ==================== ETLTaskTemplate ViewSet ====================

class ETLTaskTemplateViewSet(BaseViewSet):
    """ETL任务模板视图集"""

    queryset = ETLTaskTemplate.objects.all()
    serializer_class = ETLTaskTemplateSerializer
    create_serializer_class = ETLTaskTemplateCreateSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        template_name = self.request.query_params.get('templateName')
        template_code = self.request.query_params.get('templateCode')
        task_type = self.request.query_params.get('taskType')
        category = self.request.query_params.get('category')
        is_system = self.request.query_params.get('isSystem')

        # 应用筛选条件
        if template_name:
            queryset = queryset.filter(template_name__icontains=template_name)
        if template_code:
            queryset = queryset.filter(template_code__icontains=template_code)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if category:
            queryset = queryset.filter(category__icontains=category)
        if is_system is not None:
            queryset = queryset.filter(is_system=is_system.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'], url_path='system')
    def list_system_templates(self, request):
        """获取系统模板列表"""
        queryset = self.get_queryset().filter(is_system=True)
        serializer = ETLTaskTemplateSerializer(queryset, many=True)
        return self.data(serializer.data)

    @action(detail=False, methods=['get'], url_path='user')
    def list_user_templates(self, request):
        """获取用户自定义模板列表"""
        queryset = self.get_queryset().filter(is_system=False)
        serializer = ETLTaskTemplateSerializer(queryset, many=True)
        return self.data(serializer.data)

    @action(detail=False, methods=['post'], url_path='create-task')
    def create_task_from_template(self, request):
        """从模板创建任务"""
        template_id = request.data.get('templateId')
        params = request.data.get('params', {})

        if not template_id:
            return Response({
                'code': 400,
                'msg': '请提供模板ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = TaskService.create_task_from_template(template_id, params)
            serializer = ETLTaskSerializer(task)
            return self.data(serializer.data)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'创建任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='increment-usage')
    def increment_usage(self, request, pk=None):
        """增加模板使用次数"""
        template = self.get_object()
        template.usage_count += 1
        template.save(update_fields=['usage_count'])
        return self.data({'message': '使用次数已更新', 'usageCount': template.usage_count})


# ==================== ETLQualityRule ViewSet ====================

class ETLQualityRuleViewSet(BaseViewSet):
    """ETL质检规则视图集"""

    queryset = ETLQualityRule.objects.all()
    serializer_class = ETLQualityRuleSerializer
    create_serializer_class = ETLQualityRuleCreateSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        rule_name = self.request.query_params.get('ruleName')
        rule_code = self.request.query_params.get('ruleCode')
        rule_type = self.request.query_params.get('ruleType')
        table_id = self.request.query_params.get('tableId')
        enabled = self.request.query_params.get('enabled')

        # 应用筛选条件
        if rule_name:
            queryset = queryset.filter(rule_name__icontains=rule_name)
        if rule_code:
            queryset = queryset.filter(rule_code__icontains=rule_code)
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        if table_id:
            queryset = queryset.filter(table_id=table_id)
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')

        return queryset

    @action(detail=False, methods=['post'], url_path='test')
    def test_rule(self, request):
        """测试质检规则"""
        rule_id = request.data.get('ruleId')
        task_id = request.data.get('taskId')

        if not rule_id or not task_id:
            return Response({
                'code': 400,
                'msg': '请提供规则ID和任务ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            rule = ETLQualityRule.objects.get(id=rule_id)
            task = ETLTask.objects.get(id=task_id)

            quality_service = QualityService()
            passed, result = quality_service._check_rule(rule, task)

            return self.data({
                'passed': passed,
                'result': result
            })
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'测试失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle_enabled(self, request, pk=None):
        """切换规则启用状态"""
        rule = self.get_object()
        rule.enabled = not rule.enabled
        rule.save(update_fields=['enabled'])
        return self.data({'message': '状态已更新', 'enabled': rule.enabled})


# ==================== ETLQualityResult ViewSet ====================

class ETLQualityResultViewSet(BaseViewSet):
    """ETL质检结果视图集"""

    queryset = ETLQualityResult.objects.all()
    serializer_class = ETLQualityResultSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        task_id = self.request.query_params.get('taskId')
        execution_id = self.request.query_params.get('executionId')
        rule_id = self.request.query_params.get('ruleId')
        status_value = self.request.query_params.get('status')

        # 应用筛选条件
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if execution_id:
            queryset = queryset.filter(execution_id__icontains=execution_id)
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset

    def create(self, request, *args, **kwargs):
        """禁用直接创建质检结果"""
        return Response({
            'code': 403,
            'msg': '质检结果由系统自动创建，不允许手动创建'
        }, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """禁用更新质检结果"""
        return Response({
            'code': 403,
            'msg': '质检结果不允许修改'
        }, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """禁用删除质检结果"""
        return Response({
            'code': 403,
            'msg': '质检结果不允许删除'
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='by-execution')
    def get_results_by_execution(self, request):
        """获取指定执行的所有质检结果"""
        execution_id = request.query_params.get('executionId')
        if not execution_id:
            return Response({
                'code': 400,
                'msg': '请提供执行ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = ETLQualityResult.objects.filter(
                execution_id=execution_id
            ).order_by('-check_time')

            serializer = ETLQualityResultSerializer(results, many=True)
            return self.data(serializer.data)

        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取质检结果失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ETLExecutionProgress ViewSet ====================

class ETLExecutionProgressViewSet(BaseViewSet):
    """ETL执行进度视图集"""

    queryset = ETLExecutionProgress.objects.all()
    serializer_class = ETLExecutionProgressSerializer

    def get_queryset(self):
        """获取查询集，支持筛选"""
        queryset = super().get_queryset()

        # 获取查询参数
        execution_id = self.request.query_params.get('executionId')

        # 应用筛选条件
        if execution_id:
            queryset = queryset.filter(execution__execution_id__icontains=execution_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """禁用直接创建进度"""
        return Response({
            'code': 403,
            'msg': '执行进度由系统自动创建，不允许手动创建'
        }, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """禁用更新进度"""
        return Response({
            'code': 403,
            'msg': '执行进度不允许手动修改'
        }, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """禁用删除进度"""
        return Response({
            'code': 403,
            'msg': '执行进度不允许删除'
        }, status=status.HTTP_403_FORBIDDEN)
