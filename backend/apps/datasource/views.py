import json
import logging

from django.db.models import ProtectedError
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.dbutils.factory import get_executor
from apps.common.encrypt import decrypt_password, encrypt_password

from .models import DataSource
from .serializers import (
    DataSourceSerializer, DataSourceQuerySerializer,
    DataSourceUpdateSerializer, DataSourceCreateSerializer, DataSourceTestSerializer,
)

logger = logging.getLogger(__name__)


def _sanitize_db_error_message(exc):
    error_message = str(exc or '').lower()
    if any(keyword in error_message for keyword in (
        'access denied',
        'authentication failed',
        'password authentication failed',
        'login failed',
        'invalid credentials',
    )):
        return '连接失败：认证失败，请检查用户名和密码'
    if any(keyword in error_message for keyword in (
        'connection refused',
        'could not connect',
        'timeout',
        'timed out',
        'network is unreachable',
        'name or service not known',
        'temporary failure in name resolution',
    )):
        return '连接失败：无法连接到数据库，请检查主机、端口和网络'
    if any(keyword in error_message for keyword in (
        'unknown database',
        'does not exist',
        'unknown schema',
        'catalog',
        'schema',
    )):
        return '连接失败：数据库配置无效，请检查库名或 schema'
    return '连接失败：请检查连接配置'


def _update_connectivity_snapshot(instance, status, message=''):
    instance.connectivity_status = status
    instance.connectivity_message = message
    instance.connectivity_tested_at = timezone.now()
    instance.save(update_fields=['connectivity_status', 'connectivity_message', 'connectivity_tested_at', 'update_time'])


class DataSourceViewSet(BaseViewSet):
    """数据源管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataSource.objects.all().order_by('name')
    serializer_class = DataSourceSerializer
    update_body_serializer_class = DataSourceUpdateSerializer
    update_body_id_field = 'dataSourceId'

    def get_queryset(self):
        qs = super().get_queryset()
        s = DataSourceQuerySerializer(data=self.request.query_params)
        s.is_valid(raise_exception=False)
        vd = getattr(s, 'validated_data', {})
        if vd.get('dataSourceName'):
            qs = qs.filter(name__icontains=vd['dataSourceName'])
        if vd.get('dbType'):
            qs = qs.filter(db_type=vd['dbType'])
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        return qs

    def destroy(self, request, *args, **kwargs):
        """删除数据源，捕获外键保护异常并返回友好提示"""
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return self.error(msg='无法删除：该数据源被数据集成任务引用，请先删除相关任务后再试')

    def create(self, request, *args, **kwargs):
        s = DataSourceCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return self.ok(msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = DataSourceUpdateSerializer(instance, data=request.data)
        s.is_valid(raise_exception=True)

        connection_fields = ('db_type', 'host', 'port', 'db_name', 'username', 'params')
        connection_config_changed = any(
            field in s.validated_data and s.validated_data[field] != getattr(instance, field)
            for field in connection_fields
        )

        # 密码处理：空则不改，非空则加密新密码
        _password = s.validated_data.get('password', '')
        if _password:
            s.validated_data['password'] = encrypt_password(_password)
            connection_config_changed = True
        else:
            s.validated_data.pop('password', None)

        if connection_config_changed:
            s.validated_data['connectivity_status'] = 'unknown'
            s.validated_data['connectivity_message'] = ''
            s.validated_data['connectivity_tested_at'] = None

        s.save()
        return self.ok(msg='更新成功')

    def _parse_params(self, params_str):
        """解析连接参数字符串为字典"""
        if not params_str:
            return {}
        try:
            return json.loads(params_str)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"无法解析连接参数: {params_str}")
            return {}

    @action(detail=True, methods=['post'], url_path='test')
    def test_by_id(self, request, pk=None):
        """测试数据源连接（按ID）"""
        obj = self.get_object()
        db_info = {
            'type': obj.db_type,
            'host': obj.host,
            'port': obj.port,
            'username': obj.username,
            'password': decrypt_password(obj.password),
            'database': obj.db_name,
            'params': self._parse_params(obj.params),
        }

        try:
            ex = get_executor(db_info)
            try:
                ex.test_connection()
                _update_connectivity_snapshot(obj, 'success', '连接成功')
                return self.ok('连接成功')
            except Exception as e:
                logger.exception(f"数据源连接测试失败: {obj.name}, 错误: {str(e)}")
                message = _sanitize_db_error_message(e)
                _update_connectivity_snapshot(obj, 'failed', message)
                return self.error(msg=message)
            finally:
                try:
                    ex.close()
                except Exception:
                    pass
        except ValueError as e:
            message = f'不支持的数据库类型: {str(e)}'
            _update_connectivity_snapshot(obj, 'failed', message)
            return self.error(msg=message)

    @action(detail=False, methods=['post'], url_path='test')
    def test_by_body(self, request):
        """测试数据源连接（按请求体，不落库）"""
        s = DataSourceTestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data

        # 如果带了 dataSourceId 且密码为空，从库里取已加密密码并解密
        ds_id = request.data.get('dataSourceId')
        if ds_id:
            try:
                instance = DataSource.objects.get(id=ds_id)
                _password = vd.get('password', '')
                if not _password:
                    vd['password'] = decrypt_password(instance.password)
            except DataSource.DoesNotExist:
                pass

        db_info = {
            'type': vd.get('db_type', ''),
            'host': vd.get('host', ''),
            'port': vd.get('port', 0),
            'username': vd.get('username', ''),
            'password': vd.get('password', ''),
            'database': vd.get('db_name', ''),
            'params': self._parse_params(vd.get('params')),
        }

        # SQLite特殊处理
        if db_info['type'] == 'sqlite':
            db_info['host'] = ''
            db_info['port'] = 0
            db_info['username'] = ''
            db_info['password'] = ''

        try:
            ex = get_executor(db_info)
            try:
                ex.test_connection()
                return self.ok('连接成功')
            except Exception as e:
                logger.exception(f"数据源连接测试失败: {vd.get('db_type')}, 错误: {str(e)}")
                return self.error(msg=_sanitize_db_error_message(e))
            finally:
                try:
                    ex.close()
                except Exception:
                    pass
        except ValueError as e:
            return self.error(msg=f'不支持的数据库类型: {str(e)}')
