from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from .models import DataSource
from .serializers import DataSourceSerializer, DataSourceQuerySerializer, DataSourceUpdateSerializer, DataSourceCreateSerializer

from apps.dbutils.factory import get_executor
from apps.common.encrypt import decrypt_password


class DataSourceViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataSource.objects.all().order_by('name')
    serializer_class = DataSourceSerializer
    update_body_serializer_class = DataSourceUpdateSerializer
    update_body_id_field = 'dataSourceId'

    def get_queryset(self):
        qs = super().get_queryset()
        # 过滤条件
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
        _password = s.validated_data.get('password', None)
        if _password and decrypt_password(_password) == instance.password:
            # 新密码与旧密码相同，不更新
            s.validated_data.pop('password', None)
        s.save()
        return self.ok(msg='更新成功')

    @action(detail=True, methods=['post'], url_path='test')
    def test_by_id(self, request, pk=None):
        obj = self.get_object()
        db_info = {
            'type': obj.db_type,
            'host': obj.host,
            'port': obj.port,
            'username': obj.username,
            'password': obj.password,
            'database': obj.db_name,
            'params': obj.params or {},
        }
        ex = get_executor(db_info)
        try:
            ex.test_connection()
        except Exception as e:
            return self.error(msg=str(e))
        finally:
            ex.close()
        return self.ok('连接成功')

    @action(detail=False, methods=['post'], url_path='test')
    def test_by_body(self, request):
        if 'dataSourceId' in request.data:
            instance = DataSource.objects.get(id=request.data['dataSourceId'])
            s = DataSourceUpdateSerializer(instance, request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data
            _password = vd.get('password', None)
            if _password and decrypt_password(_password) == instance.password:
                # 新密码与旧密码相同，不更新
                vd['password'] = instance.password
        else:
            s = DataSourceCreateSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data
        db_info = {
            'type': vd['db_type'],
            'host': vd['host'],
            'port': vd['port'],
            'username': vd['username'],
            'password': vd['password'],
            'database': vd['db_name'],
            'params': vd.get('params') or {},
        }
        ex = get_executor(db_info)
        try:
            ex.test_connection()
        except Exception as e:
            return self.error(msg=str(e))
        finally:
            ex.close()
        return self.ok('连接成功')
