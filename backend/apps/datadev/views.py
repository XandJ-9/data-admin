import hashlib
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.common.pagination import StandardPagination
from apps.dbutils.factory import get_executor
from apps.datatask.services import TaskService

from .models import DataDevScript, DataDevScriptVersion, DataDevScriptExecution, DataDevDirectory
from .serializers import (
    ScriptListSerializer,
    ScriptCreateSerializer,
    ScriptUpdateSerializer,
    ScriptQuerySerializer,
    ScriptVersionSerializer,
    ScriptVersionCreateSerializer,
    ScriptExecutionSerializer,
    ScriptExecutionQuerySerializer,
    DataDevDirectorySerializer,
    DataDevDirectoryCreateSerializer,
    DataDevDirectoryUpdateSerializer,
)

logger = logging.getLogger(__name__)


class DataDevDirectoryViewSet(BaseViewSet):
    """数据目录管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevDirectory.objects.order_by('order_num', 'directory_id')
    serializer_class = DataDevDirectorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        name = request.query_params.get('directoryName')
        code = request.query_params.get('directoryCode')
        parent_id = request.query_params.get('parentId')
        status_val = request.query_params.get('status')
        if name:
            qs = qs.filter(directory_name__icontains=name)
        if code:
            qs = qs.filter(directory_code__icontains=code)
        if parent_id not in (None, ''):
            qs = qs.filter(parent_id=parent_id)
        if status_val:
            qs = qs.filter(status=status_val)
        serializer = self.get_serializer(qs, many=True)
        return Response({'code': 200, 'msg': '操作成功', 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        s = DataDevDirectoryCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data
        username = getattr(request.user, 'username', '')
        try:
            DataDevDirectory.objects.create(
                parent_id=vd['parentId'],
                directory_name=vd['directoryName'],
                directory_code=vd['directoryCode'],
                order_num=vd.get('orderNum', 0),
                status=vd.get('status', '0'),
                remark=vd.get('remark', ''),
                create_by=username,
                update_by=username,
            )
        except DjangoValidationError as e:
            raise DRFValidationError({'detail': e.messages})
        return self.ok(msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = DataDevDirectoryUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data
        if 'parentId' in vd:
            self._validate_parent_assignment(instance, vd['parentId'])
            instance.parent_id = vd['parentId']
        if 'directoryName' in vd:
            instance.directory_name = vd['directoryName']
        if 'directoryCode' in vd:
            instance.directory_code = vd['directoryCode']
        if 'orderNum' in vd:
            instance.order_num = vd['orderNum']
        if 'status' in vd:
            instance.status = vd['status']
        if 'remark' in vd:
            instance.remark = vd['remark']
        instance.update_by = getattr(request.user, 'username', '')
        try:
            instance.save()
        except DjangoValidationError as e:
            raise DRFValidationError({'detail': e.messages})
        return self.ok(msg='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        has_children = DataDevDirectory.objects.filter(
            parent_id=instance.directory_id,
            del_flag='0',
        ).exists()
        if has_children:
            return self.error(msg='当前目录存在子目录，无法删除')

        has_scripts = DataDevScript.objects.filter(
            directory_id=instance.directory_id,
            del_flag='0',
        ).exists()
        if has_scripts:
            return self.error(msg='当前目录下存在脚本，无法删除')

        # 直接 UPDATE 跳过 save() 覆写，避免触发 full_clean()
        DataDevDirectory.objects.filter(pk=instance.pk).update(del_flag='1')
        return self.ok(msg='删除成功')

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """返回嵌套树形结构，包含每个目录下的脚本数量"""
        qs = list(self.get_queryset().annotate(
            script_count=Count('scripts', filter=Q(scripts__del_flag='0'))
        ))
        tree_data = self._build_tree(qs, DataDevDirectory.ROOT_PARENT_ID)
        unassigned_count = DataDevScript.objects.filter(
            directory_id__isnull=True, del_flag='0'
        ).count()
        return Response({
            'code': 200, 'msg': '操作成功',
            'data': tree_data,
            'unassignedScriptCount': unassigned_count,
        })

    def _build_tree(self, items, parent_id):
        result = []
        for item in items:
            if item.parent_id == parent_id:
                node = DataDevDirectorySerializer(item).data
                node['scriptCount'] = getattr(item, 'script_count', 0)
                children = self._build_tree(items, item.directory_id)
                if children:
                    node['children'] = children
                result.append(node)
        return result

    def _validate_parent_assignment(self, instance, parent_id):
        if parent_id == instance.directory_id:
            raise DRFValidationError({'parentId': '数据目录不能将自身设置为父目录'})
        if parent_id == DataDevDirectory.ROOT_PARENT_ID:
            return

        target_parent = DataDevDirectory.objects.filter(
            directory_id=parent_id,
            del_flag='0',
        ).first()
        if target_parent is None:
            raise DRFValidationError({'parentId': '父目录不存在'})

        ancestor_path = instance.ancestors or DataDevDirectory.ROOT_ANCESTORS
        descendant_prefix = f"{ancestor_path},{instance.directory_id}"
        if (
            target_parent.ancestors == descendant_prefix
            or target_parent.ancestors.startswith(f"{descendant_prefix},")
        ):
            raise DRFValidationError({'parentId': '父目录不能选择当前目录或其子目录'})


class ScriptViewSet(BaseViewSet):
    """数据开发脚本管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevScript.objects.select_related('datasource', 'directory').all()
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
        directory_id = vd.get('directoryId')
        if directory_id is not None:
            if directory_id == 0:
                qs = qs.filter(directory_id__isnull=True)
            else:
                qs = qs.filter(directory_id=directory_id)
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
        vd = s.validated_data
        content = vd.pop('content', '')
        directory_id = vd.pop('directoryId', None)
        username = getattr(request.user, 'username', '')

        # 解析目录：未指定时自动取默认（order_num 最小的正常目录）
        directory = self._resolve_directory(directory_id)
        with transaction.atomic():
            script = DataDevScript.objects.create(
                script_name=vd['scriptName'],
                script_code=vd['scriptCode'],
                script_type=vd['scriptType'],
                description=vd.get('description', ''),
                tags=vd.get('tags', []),
                remark=vd.get('remark', ''),
                directory=directory,
                owner=username,
                create_by=username,
            )

            if content:
                DataDevScriptVersion.objects.create(
                    script=script,
                    version_number=1,
                    content=content,
                    content_hash=hashlib.sha256(content.encode()).hexdigest(),
                    is_current=True,
                    is_released=False,
                    create_by=username,
                )
            TaskService.sync_datadev_source_task(script, username=username)
        return self.ok(msg='创建成功')

    def _resolve_directory(self, directory_id):
        """解析目录对象：有 ID 则查找，无 ID 则取默认（order_num 最小的目录）"""
        if directory_id is not None:
            directory = DataDevDirectory.objects.filter(
                directory_id=directory_id, del_flag='0'
            ).first()
            if directory is None:
                from rest_framework.exceptions import ValidationError as DRFValidationError
                raise DRFValidationError({'directoryId': '指定的数据目录不存在'})
            return directory
        return DataDevDirectory.objects.filter(del_flag='0').order_by('order_num', 'directory_id').first()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = ScriptUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            if 'scriptName' in vd:
                instance.script_name = vd['scriptName']
            if 'scriptType' in vd:
                instance.script_type = vd['scriptType']
            if 'description' in vd:
                instance.description = vd['description']
            if 'status' in vd:
                instance.status = vd['status']
            if 'tags' in vd:
                instance.tags = vd['tags']
            if 'remark' in vd:
                instance.remark = vd['remark']
            if 'directoryId' in vd:
                instance.directory = self._resolve_directory(vd['directoryId'])
            instance.update_by = username
            instance.save()
            TaskService.sync_datadev_source_task(instance, username=username)
        return self.ok(msg='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            instance.del_flag = '1'
            instance.update_by = username
            instance.save(update_fields=['del_flag', 'update_by', 'update_time'])
            TaskService.soft_delete_source_task(
                source_module='datadev.script',
                source_record_id=instance.id,
                username=username,
            )
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

            if is_released:
                max_ver = script.versions.aggregate(max_v=Max('version_number'))['max_v'] or 0
                DataDevScriptVersion.objects.create(
                    script=script,
                    version_number=max_ver + 1,
                    content=content,
                    content_hash=hashlib.sha256(content.encode()).hexdigest(),
                    change_log=change_log,
                    is_current=True,
                    is_released=True,
                    create_by=username,
                )
            else:
                # 草稿版本单例：存在则更新，不存在则创建。
                draft_version = script.versions.filter(is_released=False).order_by('-version_number').first()
                if draft_version:
                    draft_version.content = content
                    draft_version.content_hash = hashlib.sha256(content.encode()).hexdigest()
                    draft_version.change_log = change_log
                    draft_version.is_current = True
                    draft_version.save(
                        update_fields=[
                            'content',
                            'content_hash',
                            'change_log',
                            'is_current',
                        ]
                    )
                else:
                    max_ver = script.versions.aggregate(max_v=Max('version_number'))['max_v'] or 0
                    DataDevScriptVersion.objects.create(
                        script=script,
                        version_number=max_ver + 1,
                        content=content,
                        content_hash=hashlib.sha256(content.encode()).hexdigest(),
                        change_log=change_log,
                        is_current=True,
                        is_released=False,
                        create_by=username,
                    )

            script.status = 'published' if is_released else 'draft'
            script.update_by = username
            script.save(update_fields=['status', 'update_by', 'update_time'])
            TaskService.sync_datadev_source_task(script, username=username)

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
            TaskService.sync_datadev_source_task(script, username=script.update_by)
        return self.ok(msg='回滚成功')

    # ── 执行管理 ──────────────────────────────

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_script(self, request, pk=None):
        """触发脚本执行并返回结果"""
        script = self.get_object()
        username = request.user.username if hasattr(request, 'user') else ''
        runtime_params = request.data.get('params') or {}
        result = TaskService.execute_datadev_script(
            script,
            username=username,
            runtime_params=runtime_params,
        )
        if result['ok']:
            return self.data(result['data'], msg=result['msg'])
        if result['data'] is None:
            return self.error(msg=result['msg'])
        return Response({'code': 400, 'msg': result['msg'], 'data': result['data']})

    @action(detail=True, methods=['get'], url_path='executions')
    def list_executions(self, request, pk=None):
        """获取脚本执行记录"""
        script = self.get_object()
        qs = script.executions.select_related('version', 'task_instance').all()

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
    queryset = DataDevScriptExecution.objects.select_related('script', 'version', 'task_instance').all()
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
