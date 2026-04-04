import json
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.dbutils.factory import get_executor
from apps.common.encrypt import decrypt_password, encrypt_password

from .models import DataSource
from .serializers import (
    DataSourceSerializer, DataSourceQuerySerializer,
    DataSourceUpdateSerializer, DataSourceCreateSerializer,
)

logger = logging.getLogger(__name__)


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

    def create(self, request, *args, **kwargs):
        s = DataSourceCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return self.ok(msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = DataSourceUpdateSerializer(instance, data=request.data)
        s.is_valid(raise_exception=True)

        # 处理密码：如果前端传来空密码或加密后的密码与原密码相同，则不更新密码
        _password = s.validated_data.get('password', '')
        if _password:
            try:
                decrypted_pwd = decrypt_password(_password)
                if decrypted_pwd == instance.password or decrypted_pwd == '':
                    s.validated_data.pop('password', None)
            except Exception:
                # 如果解密失败，说明是新密码（未加密），保留它
                pass
        else:
            s.validated_data.pop('password', None)

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
            'password': obj.password,
            'database': obj.db_name,
            'params': self._parse_params(obj.params),
        }

        try:
            ex = get_executor(db_info)
            try:
                ex.test_connection()
                return self.ok('连接成功')
            except Exception as e:
                logger.error(f"数据源连接测试失败: {obj.name}, 错误: {str(e)}")
                return self.error(msg=f'连接失败: {str(e)}')
            finally:
                try:
                    ex.close()
                except Exception:
                    pass
        except ValueError as e:
            return self.error(msg=f'不支持的数据库类型: {str(e)}')

    @action(detail=False, methods=['post'], url_path='test')
    def test_by_body(self, request):
        """测试数据源连接（按请求体，不落库）"""
        if 'dataSourceId' in request.data and request.data['dataSourceId']:
            instance = DataSource.objects.get(id=request.data['dataSourceId'])
            s = DataSourceUpdateSerializer(instance, request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data

            # 处理密码：如果前端传来空值或加密密码，则使用原密码
            _password = vd.get('password', '')
            if not _password:
                vd['password'] = instance.password
            else:
                try:
                    decrypted_pwd = decrypt_password(_password)
                    if decrypted_pwd == instance.password or decrypted_pwd == '':
                        vd['password'] = instance.password
                except Exception:
                    # 如果解密失败，说明是新密码，直接使用
                    pass
        else:
            s = DataSourceCreateSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data

        db_info = {
            'type': vd['db_type'],
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
                logger.error(f"数据源连接测试失败: {vd.get('db_type')}, 错误: {str(e)}")
                return self.error(msg=f'连接失败: {str(e)}')
            finally:
                try:
                    ex.close()
                except Exception:
                    pass
        except ValueError as e:
            return self.error(msg=f'不支持的数据库类型: {str(e)}')
