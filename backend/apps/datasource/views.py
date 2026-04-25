import logging

from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from apps.common.encrypt import decrypt_password, encrypt_password
from apps.common.mixins import BaseViewMixin
from apps.dbutils.factory import get_executor
from apps.system.permission import HasRolePermission
from apps.system.views.core import BaseViewSet

from .collectors import create_async_task, create_sync_task, discover_columns, discover_databases, discover_tables
from .executor_info import build_executor_info, build_executor_info_from_payload
from .models import DataSource, SourceMetadataCollectionTask
from .serializers import (
    CollectionStatusQuerySerializer,
    DataSourceCreateSerializer,
    DataSourceQuerySerializer,
    DataSourceSerializer,
    DataSourceTestSerializer,
    DataSourceUpdateSerializer,
    DiscoveryRequestSerializer,
    TableDiscoveryRequestSerializer,
)
from .utils import public_error_message, sanitize_db_error_message

logger = logging.getLogger(__name__)


def _sanitize_db_error_message(exc):
    return sanitize_db_error_message(exc)


def _update_connectivity_snapshot(instance, status, message=''):
    instance.connectivity_status = status
    instance.connectivity_message = message
    instance.connectivity_tested_at = timezone.now()
    instance.save(update_fields=['connectivity_status', 'connectivity_message', 'connectivity_tested_at', 'update_time'])


class DataSourceViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataSource.objects.all().order_by('name')
    serializer_class = DataSourceSerializer
    create_serializer_class = DataSourceCreateSerializer
    update_body_serializer_class = DataSourceUpdateSerializer
    update_body_id_field = 'dataSourceId'

    def get_queryset(self):
        queryset = super().get_queryset()
        serializer = DataSourceQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=False)
        validated_data = getattr(serializer, 'validated_data', {})
        if validated_data.get('dataSourceName'):
            queryset = queryset.filter(name__icontains=validated_data['dataSourceName'])
        if validated_data.get('dbType'):
            queryset = queryset.filter(db_type=validated_data['dbType'])
        if validated_data.get('status'):
            queryset = queryset.filter(status=validated_data['status'])
        return queryset

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return self.error(msg='无法删除：该数据源仍被其他模块引用')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DataSourceUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        connection_fields = ('db_type', 'host', 'port', 'db_name', 'username', 'params')
        connection_changed = any(
            field in serializer.validated_data and serializer.validated_data[field] != getattr(instance, field)
            for field in connection_fields
        )

        raw_password = serializer.validated_data.get('password', '')
        if raw_password:
            serializer.validated_data['password'] = encrypt_password(raw_password)
            connection_changed = True
        else:
            serializer.validated_data.pop('password', None)

        if connection_changed:
            serializer.validated_data['connectivity_status'] = 'unknown'
            serializer.validated_data['connectivity_message'] = ''
            serializer.validated_data['connectivity_tested_at'] = None

        serializer.save(update_by=getattr(request.user, 'username', ''))
        return self.ok(msg='更新成功')

    @action(detail=True, methods=['post'], url_path='test')
    def test_by_id(self, request, pk=None):
        data_source = self.get_object()
        try:
            executor = get_executor(build_executor_info(data_source))
            try:
                executor.test_connection()
                _update_connectivity_snapshot(data_source, 'success', '连接成功')
                return self.ok(msg='连接成功')
            except Exception as exc:
                logger.exception('数据源连接测试失败: datasource=%s', data_source.name)
                message = _sanitize_db_error_message(exc)
                _update_connectivity_snapshot(data_source, 'failed', message)
                return self.error(msg=message)
            finally:
                try:
                    executor.close()
                except Exception:
                    pass
        except ValueError as exc:
            message = f'不支持的数据库类型: {exc}'
            _update_connectivity_snapshot(data_source, 'failed', message)
            return self.error(msg=message)

    @action(detail=False, methods=['post'], url_path='test')
    def test_by_body(self, request):
        serializer = DataSourceTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        password = validated_data.get('password', '')
        data_source_id = request.data.get('dataSourceId')
        if data_source_id and not password:
            try:
                password = decrypt_password(DataSource.objects.get(pk=data_source_id, del_flag='0').password)
            except DataSource.DoesNotExist:
                password = ''

        db_info = build_executor_info_from_payload(validated_data, password=password)
        if db_info['type'] == 'sqlite':
            db_info['host'] = ''
            db_info['port'] = 0
            db_info['username'] = ''
            db_info['password'] = ''

        try:
            executor = get_executor(db_info)
            try:
                executor.test_connection()
                return self.ok(msg='连接成功')
            except Exception as exc:
                logger.exception('数据源连接测试失败: db_type=%s', validated_data.get('db_type'))
                return self.error(msg=_sanitize_db_error_message(exc))
            finally:
                try:
                    executor.close()
                except Exception:
                    pass
        except ValueError as exc:
            return self.error(msg=f'不支持的数据库类型: {exc}')


class DataSourceDiscoveryViewSet(BaseViewMixin, ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]

    def _get_data_source(self, data_source_id):
        return get_object_or_404(DataSource.objects.filter(del_flag='0'), pk=data_source_id)

    def databases(self, request):
        serializer = DiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_source = self._get_data_source(serializer.validated_data['data_source_id'])
        try:
            return self.data(discover_databases(data_source))
        except Exception as exc:
            logger.exception('获取数据库列表失败: datasource_id=%s', data_source.id)
            return self.error(msg=public_error_message(exc))

    def tables(self, request):
        serializer = DiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        data_source = self._get_data_source(validated_data['data_source_id'])
        try:
            rows = discover_tables(data_source, validated_data.get('database_name', ''))
            return self.raw_response({'code': 200, 'msg': '操作成功', 'rows': rows, 'total': len(rows)})
        except Exception as exc:
            logger.exception('获取数据表列表失败: datasource_id=%s', data_source.id)
            return self.error(msg=public_error_message(exc))

    def columns(self, request):
        serializer = TableDiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        data_source = self._get_data_source(validated_data['data_source_id'])
        try:
            rows = discover_columns(
                data_source,
                validated_data.get('table_name', ''),
                validated_data.get('database_name', ''),
            )
            return self.raw_response({'code': 200, 'msg': '操作成功', 'rows': rows, 'total': len(rows)})
        except Exception as exc:
            logger.exception('获取字段列表失败: datasource_id=%s', data_source.id)
            return self.error(msg=public_error_message(exc))

    def collect(self, request):
        serializer = DiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        data_source = self._get_data_source(validated_data['data_source_id'])
        try:
            task = create_sync_task(
                data_source,
                'database' if validated_data.get('database_name') else 'full',
                database_name=validated_data.get('database_name', ''),
            )
        except ValueError as exc:
            return self.error(msg=public_error_message(exc))
        if task.status == 'failed':
            return self.error(msg=task.error_message or '采集失败')
        return self.data({'taskId': task.task_id}, msg='采集完成')

    def collect_table(self, request):
        serializer = TableDiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        data_source = self._get_data_source(validated_data['data_source_id'])
        try:
            task = create_sync_task(
                data_source,
                'table',
                database_name=validated_data.get('database_name', ''),
                table_name=validated_data.get('table_name', ''),
            )
        except ValueError as exc:
            return self.error(msg=public_error_message(exc))
        if task.status == 'failed':
            return self.error(msg=task.error_message or '采集失败')
        return self.data({'taskId': task.task_id}, msg='采集完成')

    def collect_async(self, request):
        serializer = DiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        data_source = self._get_data_source(validated_data['data_source_id'])
        try:
            task = create_async_task(
                data_source,
                'database' if validated_data.get('database_name') else 'full',
                database_name=validated_data.get('database_name', ''),
            )
        except ValueError as exc:
            return self.error(msg=public_error_message(exc))
        return self.data({'taskId': task.task_id}, msg='采集任务已启动')

    def collect_status(self, request):
        serializer = CollectionStatusQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        task = SourceMetadataCollectionTask.objects.filter(
            task_id=serializer.validated_data['task_id'],
            del_flag='0',
        ).first()
        if task is None:
            return self.not_found(msg='采集任务不存在')
        return self.data(
            {
                'taskId': task.task_id,
                'status': task.status,
                'databaseName': task.database_name,
                'tableName': task.table_name,
                'currentTable': task.current_table,
                'totalTables': task.total_tables,
                'collectedTables': task.collected_tables,
                'errorMessage': task.error_message,
                'cancelRequested': task.cancel_requested,
                'startedAt': task.started_at.strftime('%Y-%m-%d %H:%M:%S') if task.started_at else None,
                'finishedAt': task.finished_at.strftime('%Y-%m-%d %H:%M:%S') if task.finished_at else None,
                'progress': 0 if task.total_tables <= 0 else round(task.collected_tables * 100 / task.total_tables),
            }
        )

    def collect_cancel(self, request):
        serializer = CollectionStatusQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = SourceMetadataCollectionTask.objects.filter(
            task_id=serializer.validated_data['task_id'],
            del_flag='0',
        ).first()
        if task is None:
            return self.not_found(msg='采集任务不存在')
        if task.status in ('completed', 'failed', 'cancelled'):
            return self.ok(msg='任务已结束')
        task.cancel_requested = True
        if task.status == 'pending':
            task.status = 'cancelled'
            task.finished_at = timezone.now()
        task.save(update_fields=['cancel_requested', 'status', 'finished_at', 'update_time'])
        return self.ok(msg='任务已取消')
