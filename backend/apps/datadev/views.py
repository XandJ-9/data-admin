import hashlib
import logging
import uuid

from django.db import transaction
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.common.pagination import StandardPagination

from .models import DataDevScript, DataDevScriptVersion, DataDevScriptExecution
from .serializers import (
    ScriptListSerializer,
    ScriptCreateSerializer,
    ScriptUpdateSerializer,
    ScriptQuerySerializer,
    ScriptVersionSerializer,
    ScriptVersionCreateSerializer,
    ScriptExecutionSerializer,
    ScriptExecutionQuerySerializer,
)

logger = logging.getLogger(__name__)


class ScriptViewSet(BaseViewSet):
    """数据开发脚本管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevScript.objects.select_related('datasource').all()
    serializer_class = ScriptListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        s = ScriptQuerySerializer(data=self.request.query_params)
        s.is_valid(raise_exception=False)
        vd = getattr(s, 'validated_data', {})
        if vd.get('scriptName'):
            qs = qs.filter(script_name__icontains=vd['scriptName'])
        if vd.get('scriptType'):
            qs = qs.filter(script_type=vd['scriptType'])
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        if vd.get('layer') is not None:
            qs = qs.filter(layer=vd['layer'])
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ScriptListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ScriptListSerializer(qs, many=True)
        return self.data(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ScriptListSerializer(instance)
        result = serializer.data
        # 附带当前版本内容
        current_version = instance.versions.filter(is_current=True).first()
        if current_version:
            result['content'] = current_version.content
            result['versionNumber'] = current_version.version_number
        else:
            result['content'] = ''
            result['versionNumber'] = 0
        return self.data(result)

    def create(self, request, *args, **kwargs):
        s = ScriptCreateSerializer(data=request.data, context={'request': request})
        s.is_valid(raise_exception=True)
        s.save()
        return self.ok(msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = ScriptUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data

        update_fields = {}
        if 'scriptName' in vd:
            update_fields['script_name'] = vd['scriptName']
        if 'scriptType' in vd:
            update_fields['script_type'] = vd['scriptType']
        if 'description' in vd:
            update_fields['description'] = vd['description']
        if 'status' in vd:
            update_fields['status'] = vd['status']
        if 'tags' in vd:
            update_fields['tags'] = vd['tags']
        if 'remark' in vd:
            update_fields['remark'] = vd['remark']
        if 'layer' in vd:
            update_fields['layer'] = vd['layer']

        update_fields['update_by'] = (
            request.user.username if hasattr(request, 'user') else ''
        )

        for attr, value in update_fields.items():
            setattr(instance, attr, value)
        instance.save()
        return self.ok(msg='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.del_flag = '1'
        instance.save(update_fields=['del_flag'])
        return self.ok(msg='删除成功')

    # ── 版本管理 ──────────────────────────────

    @action(detail=True, methods=['get'], url_path='versions')
    def list_versions(self, request, pk=None):
        """获取脚本所有版本"""
        script = self.get_object()
        versions = script.versions.all()
        serializer = ScriptVersionSerializer(versions, many=True)
        return self.data(serializer.data)

    @action(detail=True, methods=['post'], url_path='versions/create')
    def create_version(self, request, pk=None):
        """创建新版本（默认草稿版本）"""
        script = self.get_object()
        s = ScriptVersionCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        content = s.validated_data['content']
        change_log = s.validated_data.get('changeLog', '')

        self._create_version_snapshot(
            script=script,
            content=content,
            change_log=change_log,
            is_released=False,
            username=request.user.username if hasattr(request, 'user') else '',
        )
        return self.ok(msg='草稿版本保存成功')

    @action(detail=True, methods=['post'], url_path='versions/publish')
    def publish_version(self, request, pk=None):
        """发布新版本（正式可用）"""
        script = self.get_object()
        s = ScriptVersionCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        content = s.validated_data['content']
        change_log = s.validated_data.get('changeLog', '')

        self._create_version_snapshot(
            script=script,
            content=content,
            change_log=change_log,
            is_released=True,
            username=request.user.username if hasattr(request, 'user') else '',
        )
        return self.ok(msg='发布成功')

    def _create_version_snapshot(self, script, content, change_log, is_released, username):
        """创建版本快照，并维护当前版本与脚本发布状态。"""
        with transaction.atomic():
            script.versions.filter(is_current=True).update(is_current=False)
            max_ver = script.versions.aggregate(
                max_v=Max('version_number')
            )['max_v'] or 0
            DataDevScriptVersion.objects.create(
                script=script,
                version_number=max_ver + 1,
                content=content,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
                change_log=change_log,
                is_current=True,
                is_released=is_released,
                create_by=username,
            )
            script.status = 'published' if is_released else 'draft'
            script.update_by = username
            script.save(update_fields=['status', 'update_by', 'update_time'])

    @action(detail=True, methods=['post'], url_path=r'versions/(?P<version_id>\d+)/rollback')
    def rollback_version(self, request, pk=None, version_id=None):
        """回滚到指定版本"""
        script = self.get_object()
        target = script.versions.filter(id=version_id).first()
        if not target:
            return self.error(msg='版本不存在')
        if not target.is_released:
            return self.error(msg='只能回滚到正式版本')

        with transaction.atomic():
            script.versions.filter(is_current=True).update(is_current=False)
            target.is_current = True
            target.save(update_fields=['is_current'])
            script.status = 'published'
            script.update_by = request.user.username if hasattr(request, 'user') else ''
            script.save(update_fields=['status', 'update_by', 'update_time'])
        return self.ok(msg='回滚成功')

    # ── 执行管理 ──────────────────────────────

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_script(self, request, pk=None):
        """触发脚本执行"""
        script = self.get_object()
        current_version = script.versions.filter(is_current=True).first()

        execution = DataDevScriptExecution.objects.create(
            script=script,
            version=current_version,
            execution_id=uuid.uuid4().hex,
            status='pending',
            executor_type='sparksql',
            executor_params=request.data.get('params'),
            executed_by=request.user.username if hasattr(request, 'user') else '',
        )

        # TODO: 对接执行器适配层（apps.executors），异步触发执行
        # 首期仅创建记录，后续接入实际执行能力
        return self.data(
            {'executionId': execution.execution_id},
            msg='已提交 Spark SQL 执行请求（待执行器处理）',
        )

    @action(detail=True, methods=['get'], url_path='executions')
    def list_executions(self, request, pk=None):
        """获取脚本执行记录"""
        script = self.get_object()
        qs = script.executions.all()

        s = ScriptExecutionQuerySerializer(data=request.query_params)
        s.is_valid(raise_exception=False)
        vd = getattr(s, 'validated_data', {})
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        if vd.get('executedBy'):
            qs = qs.filter(executed_by=vd['executedBy'])

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ScriptExecutionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ScriptExecutionSerializer(qs, many=True)
        return self.data(serializer.data)


class ScriptExecutionViewSet(BaseViewSet):
    """脚本执行记录（全局查询）"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevScriptExecution.objects.select_related('script', 'version').all()
    serializer_class = ScriptExecutionSerializer
    pagination_class = StandardPagination
    http_method_names = ['get']

    def get_queryset(self):
        qs = super().get_queryset()
        s = ScriptExecutionQuerySerializer(data=self.request.query_params)
        s.is_valid(raise_exception=False)
        vd = getattr(s, 'validated_data', {})
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        if vd.get('executedBy'):
            qs = qs.filter(executed_by=vd['executedBy'])
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ScriptExecutionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ScriptExecutionSerializer(qs, many=True)
        return self.data(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ScriptExecutionSerializer(instance)
        return self.data(serializer.data)
