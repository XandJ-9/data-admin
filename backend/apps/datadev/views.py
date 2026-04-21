import hashlib
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.pagination import StandardPagination
from apps.datatask.services import TaskService
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet

from .models import (
    DataDevDirectory,
    DataDevModel,
    DataDevModelField,
    DataDevScript,
    DataDevScriptExecution,
    DataDevScriptVersion,
)
from .serializers import (
    DataDevDirectoryCreateSerializer,
    DataDevDirectorySerializer,
    DataDevDirectoryUpdateSerializer,
    DataModelCreateUpdateSerializer,
    DataModelDetailSerializer,
    DataModelListSerializer,
    DataModelQuerySerializer,
    ScriptCreateSerializer,
    ScriptExecutionQuerySerializer,
    ScriptExecutionSerializer,
    ScriptListSerializer,
    ScriptQuerySerializer,
    ScriptUpdateSerializer,
    ScriptVersionCreateSerializer,
    ScriptVersionSerializer,
)

logger = logging.getLogger(__name__)


class DataDevDirectoryViewSet(BaseViewSet):
    """数据目录管理（兼容保留，不再作为主工作流）。"""

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
        serializer = DataDevDirectoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
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
        except DjangoValidationError as exc:
            raise DRFValidationError({'detail': exc.messages})
        return self.ok(msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataDevDirectoryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
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
        except DjangoValidationError as exc:
            raise DRFValidationError({'detail': exc.messages})
        return self.ok(msg='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        has_children = DataDevDirectory.objects.filter(parent_id=instance.directory_id, del_flag='0').exists()
        if has_children:
            return self.error(msg='当前目录存在子目录，无法删除')
        DataDevDirectory.objects.filter(pk=instance.pk).update(del_flag='1')
        return self.ok(msg='删除成功')

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        tree_data = self._build_tree(list(self.get_queryset()), DataDevDirectory.ROOT_PARENT_ID)
        return Response({'code': 200, 'msg': '操作成功', 'data': tree_data, 'unassignedScriptCount': 0})

    def _build_tree(self, items, parent_id):
        result = []
        for item in items:
            if item.parent_id == parent_id:
                node = DataDevDirectorySerializer(item).data
                node['scriptCount'] = 0
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
        target_parent = DataDevDirectory.objects.filter(directory_id=parent_id, del_flag='0').first()
        if target_parent is None:
            raise DRFValidationError({'parentId': '父目录不存在'})
        ancestor_path = instance.ancestors or DataDevDirectory.ROOT_ANCESTORS
        descendant_prefix = f"{ancestor_path},{instance.directory_id}"
        if target_parent.ancestors == descendant_prefix or target_parent.ancestors.startswith(f"{descendant_prefix},"):
            raise DRFValidationError({'parentId': '父目录不能选择当前目录或其子目录'})


class ScriptViewSet(BaseViewSet):
    """加工作业管理。"""

    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevScript.objects.select_related('datasource', 'target_model').all()
    serializer_class = ScriptListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = ScriptQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        vd = getattr(serializer, 'validated_data', {})
        if vd.get('scriptName'):
            qs = qs.filter(script_name__icontains=vd['scriptName'])
        if vd.get('scriptType'):
            qs = qs.filter(script_type=vd['scriptType'])
        if vd.get('scriptRole'):
            qs = qs.filter(script_role=vd['scriptRole'])
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        if 'targetModelId' in vd:
            if vd['targetModelId'] is None:
                qs = qs.filter(target_model_id__isnull=True)
            else:
                qs = qs.filter(target_model_id=vd['targetModelId'])
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
        current_version = instance.versions.filter(is_current=True).first()
        result['content'] = current_version.content if current_version else ''
        result['versionNumber'] = current_version.version_number if current_version else 0
        return self.data(result)

    def create(self, request, *args, **kwargs):
        serializer = ScriptCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        content = vd.pop('content', '')
        username = getattr(request.user, 'username', '')
        target_model = self._resolve_target_model(vd.get('targetModelId'))
        script_role = vd.get('scriptRole') or ('python_job' if vd['scriptType'] == 'python' else 'transform')
        with transaction.atomic():
            script = DataDevScript.objects.create(
                script_name=vd['scriptName'],
                script_code=vd['scriptCode'],
                script_type=vd['scriptType'],
                script_role=script_role,
                engine_type='mvp' if vd['scriptType'] == 'python' else vd.get('engineType', 'spark'),
                description=vd.get('description', ''),
                target_model=target_model,
                tags=vd.get('tags', []),
                remark=vd.get('remark', ''),
                owner=username,
                create_by=username,
                update_by=username,
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
        return self.data({'scriptId': script.id}, msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ScriptUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        username = getattr(request.user, 'username', '')
        with transaction.atomic():
            if 'scriptName' in vd:
                instance.script_name = vd['scriptName']
            if 'scriptType' in vd:
                instance.script_type = vd['scriptType']
            if 'scriptRole' in vd:
                instance.script_role = vd['scriptRole']
            if 'engineType' in vd:
                instance.engine_type = vd['engineType']
            if 'description' in vd:
                instance.description = vd['description']
            if 'status' in vd:
                instance.status = vd['status']
            if 'targetModelId' in vd:
                instance.target_model = self._resolve_target_model(vd['targetModelId'])
            if 'tags' in vd:
                instance.tags = vd['tags']
            if 'remark' in vd:
                instance.remark = vd['remark']
            if instance.script_type != 'sql':
                instance.engine_type = 'mvp'
            elif not instance.engine_type:
                instance.engine_type = 'spark'
            instance.update_by = username
            instance.save()
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

    @action(detail=True, methods=['get'], url_path='versions')
    def list_versions(self, request, pk=None):
        script = self.get_object()
        serializer = ScriptVersionSerializer(script.versions.all(), many=True)
        return self.data(serializer.data)

    @action(detail=True, methods=['post'], url_path='versions/create')
    def create_version(self, request, pk=None):
        script = self.get_object()
        serializer = ScriptVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._create_version_snapshot(
            script=script,
            content=serializer.validated_data['content'],
            change_log=serializer.validated_data.get('changeLog', ''),
            is_released=False,
            username=request.user.username if hasattr(request, 'user') else '',
        )
        return self.ok(msg='草稿版本保存成功')

    @action(detail=True, methods=['post'], url_path='versions/publish')
    def publish_version(self, request, pk=None):
        script = self.get_object()
        serializer = ScriptVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._create_version_snapshot(
            script=script,
            content=serializer.validated_data['content'],
            change_log=serializer.validated_data.get('changeLog', ''),
            is_released=True,
            username=request.user.username if hasattr(request, 'user') else '',
        )
        return self.ok(msg='发布成功')

    def _create_version_snapshot(self, script, content, change_log, is_released, username):
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
                draft_version = script.versions.filter(is_released=False).order_by('-version_number').first()
                if draft_version:
                    draft_version.content = content
                    draft_version.content_hash = hashlib.sha256(content.encode()).hexdigest()
                    draft_version.change_log = change_log
                    draft_version.is_current = True
                    draft_version.save(update_fields=['content', 'content_hash', 'change_log', 'is_current'])
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

    @action(detail=True, methods=['post'], url_path=r'versions/(?P<version_id>\d+)/rollback')
    def rollback_version(self, request, pk=None, version_id=None):
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

    @action(detail=True, methods=['post'], url_path='publish-task')
    def publish_task(self, request, pk=None):
        script = self.get_object()
        try:
            self._validate_publishable(script)
        except DRFValidationError as exc:
            detail = exc.detail
            if isinstance(detail, dict):
                first_value = next(iter(detail.values()), '发布任务前请先完成必要治理信息')
                if isinstance(first_value, (list, tuple)):
                    message = str(first_value[0]) if first_value else '发布任务前请先完成必要治理信息'
                else:
                    message = str(first_value)
                return Response({'code': 400, 'msg': message, 'errors': detail})
            return Response({'code': 400, 'msg': str(detail), 'errors': detail})
        username = request.user.username if hasattr(request, 'user') else ''
        task = TaskService.sync_datadev_source_task(script, username=username)
        return self.data({'taskId': task.id, 'taskCode': task.task_code}, msg='已发布到任务运维')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_script(self, request, pk=None):
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
        script = self.get_object()
        qs = script.executions.select_related('version', 'task_instance').all()
        serializer = ScriptExecutionQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=False)
        vd = getattr(serializer, 'validated_data', {})
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        if vd.get('executedBy'):
            qs = qs.filter(executed_by=vd['executedBy'])
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ScriptExecutionSerializer(page, many=True).data)
        return self.data(ScriptExecutionSerializer(qs, many=True).data)

    def _resolve_target_model(self, target_model_id):
        if target_model_id in (None, ''):
            return None
        target_model = DataDevModel.objects.filter(id=target_model_id, del_flag='0').first()
        if target_model is None:
            raise DRFValidationError({'targetModelId': '指定的目标模型不存在'})
        return target_model

    def _validate_publishable(self, script):
        current_version = script.versions.filter(is_current=True).first()
        if current_version is None or not current_version.content.strip():
            raise DRFValidationError({'detail': '发布任务前请先保存加工作业内容'})
        if script.script_role != 'explore' and script.target_model_id is None:
            raise DRFValidationError({'targetModelId': '当前作业类型发布前必须绑定目标模型'})
        if script.target_model_id is None:
            return
        target_model = script.target_model
        if not target_model.owner:
            raise DRFValidationError({'targetModelId': '目标模型缺少负责人，无法发布任务'})
        if not target_model.table_comment:
            raise DRFValidationError({'targetModelId': '目标模型缺少表注释，无法发布任务'})
        active_fields = list(target_model.model_fields.filter(del_flag='0').order_by('ordinal_position', 'id'))
        if not active_fields:
            raise DRFValidationError({'targetModelId': '目标模型至少需要定义一个字段'})
        missing_comment = next((field.field_name for field in active_fields if not field.field_comment), None)
        if missing_comment:
            raise DRFValidationError({'targetModelId': f'目标模型字段 {missing_comment} 缺少字段注释'})


class ScriptExecutionViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevScriptExecution.objects.select_related('script', 'version', 'task_instance').all()
    serializer_class = ScriptExecutionSerializer
    pagination_class = StandardPagination
    http_method_names = ['get']

    def get_queryset(self):
        qs = super().get_queryset()
        serializer = ScriptExecutionQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        vd = getattr(serializer, 'validated_data', {})
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        if vd.get('executedBy'):
            qs = qs.filter(executed_by=vd['executedBy'])
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ScriptExecutionSerializer(page, many=True).data)
        return self.data(ScriptExecutionSerializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return self.data(ScriptExecutionSerializer(self.get_object()).data)


class DataModelViewSet(BaseViewSet):
    """数据建模模块。"""

    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataDevModel.objects.prefetch_related('model_fields').all()
    serializer_class = DataModelListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('model_fields')
        serializer = DataModelQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        vd = getattr(serializer, 'validated_data', {})
        if vd.get('modelName'):
            qs = qs.filter(model_name__icontains=vd['modelName'])
        if vd.get('layer'):
            qs = qs.filter(layer=vd['layer'])
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return self.data(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataModelDetailSerializer(instance)
        result = serializer.data
        result['fields'] = result.get('fields', [])
        result['generatedSql'] = TaskService.build_datamodel_create_sql(instance)
        return self.data(result)

    def create(self, request, *args, **kwargs):
        serializer = DataModelCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        username = request.user.username if hasattr(request, 'user') else ''
        with transaction.atomic():
            model = DataDevModel.objects.create(
                model_name=vd['modelName'],
                model_code=vd['modelCode'],
                layer=vd['layer'],
                table_name=vd['tableName'],
                schema_name=vd.get('schemaName', ''),
                table_comment=vd['tableComment'],
                engine_type=vd['engineType'],
                owner=vd['owner'],
                description=vd.get('description', ''),
                remark=vd.get('remark', ''),
                create_by=username,
                update_by=username,
            )
            self._replace_fields(model, vd['fields'], username)
            TaskService.sync_datamodel_source_task(model, username=username)
        return self.data({'modelId': model.id}, msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataModelCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        username = request.user.username if hasattr(request, 'user') else ''
        with transaction.atomic():
            instance.model_name = vd['modelName']
            instance.model_code = vd['modelCode']
            instance.layer = vd['layer']
            instance.table_name = vd['tableName']
            instance.schema_name = vd.get('schemaName', '')
            instance.table_comment = vd['tableComment']
            instance.engine_type = vd['engineType']
            instance.owner = vd['owner']
            instance.description = vd.get('description', '')
            instance.remark = vd.get('remark', '')
            instance.update_by = username
            instance.save()
            self._replace_fields(instance, vd['fields'], username)
            TaskService.sync_datamodel_source_task(instance, username=username)
        return self.data({'modelId': instance.id}, msg='保存成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            DataDevModelField.objects.filter(model=instance, del_flag='0').update(del_flag='1')
            DataDevModel.objects.filter(pk=instance.pk).update(del_flag='1')
            TaskService.soft_delete_source_task(source_module='datadev.model', source_record_id=instance.id, username=request.user.username)
        return self.ok(msg='删除成功')

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_model(self, request, pk=None):
        model = self.get_object()
        username = request.user.username if hasattr(request, 'user') else ''
        result = TaskService.execute_datamodel_task(model, username=username)
        if result['ok']:
            return self.data(result['data'], msg=result['msg'])
        if result['data'] is None:
            return self.error(msg=result['msg'])
        return Response({'code': 400, 'msg': result['msg'], 'data': result['data']})

    def _replace_fields(self, model, fields_payload, username):
        DataDevModelField.objects.filter(model=model, del_flag='0').update(del_flag='1')
        field_objects = []
        for index, item in enumerate(fields_payload, start=1):
            field_objects.append(DataDevModelField(
                model=model,
                field_name=item['fieldName'],
                field_type=item['fieldType'],
                field_comment=item['fieldComment'],
                is_nullable=item.get('isNullable', True),
                ordinal_position=item.get('ordinalPosition') or index,
                create_by=username,
                update_by=username,
            ))
        DataDevModelField.objects.bulk_create(field_objects)
