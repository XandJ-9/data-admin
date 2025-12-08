from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.system.views.core import BaseViewSet, BaseViewMixin
from apps.system.permission import HasRolePermission
from apps.datameta.models import MetaColumn, MetaTable
from .models import DataSource
from .serializers import DataSourceSerializer, DataSourceQuerySerializer, DataSourceUpdateSerializer, DataSourceCreateSerializer
from apps.dbutils import list_tables, get_table_schema, get_table_info, list_tables_info, get_databases

from apps.dbutils.factory import get_executor
from django.template import Template, Context
from django.db import transaction

from apps.common.encrypt import decrypt_password

class DatametaMixin:
    def _load_ds(self, ds_id):
        try:
            return DataSource.objects.get(pk=int(ds_id), del_flag='0')
        except Exception:
            return None

    def _build_info(self, ds):
        return {
            'type': ds.db_type,
            'host': ds.host,
            'port': ds.port,
            'username': ds.username,
            'password': ds.password,
            'database': ds.db_name,
            'params': ds.params or {},
        }

    def _collect_table(self, info, ds_id, table):
        # 获取表级详细信息（数据库名、表注释、创建/更新时间等）
        tinfo = get_table_info(info, table) or {}
        comment = tinfo.get('comment') or ''
        database_name = tinfo.get('databaseName') or ''
        # 更新或创建表元数据
        obj, created = MetaTable.objects.update_or_create(
            data_source_id=ds_id,
            table_name=table,
            database=database_name,
            defaults={'comment': comment, 'del_flag': '0'}
        )
        # 记录采集/更新者
        user = getattr(getattr(self, 'request', None), 'user', None)
        if user and getattr(user, 'username', None):
            if created:
                obj.create_by = user.username
                obj.save(update_fields=['create_by'])
            else:
                obj.update_by = user.username
                obj.save(update_fields=['update_by', 'update_time'])
        # 删除数据表对应的列
        MetaColumn.objects.filter(data_source_id=ds_id, table=obj).delete()

        cols = get_table_schema(info, table)
        for c in cols:
            col, c_created = MetaColumn.objects.update_or_create(
                data_source_id=ds_id,
                table=obj,
                name=c.get('name'),
                defaults={
                    'order': c.get('order') or 0,
                    'type': c.get('type') or '',
                    'notnull': bool(c.get('notnull')),
                    'default': str(c.get('default') or ''),
                    'primary': bool(c.get('primary')),
                    'comment': c.get('comment') or '',
                    'del_flag': '0'
                }
            )
            if user and getattr(user, 'username', None):
                if c_created:
                    col.create_by = user.username
                    col.save(update_fields=['create_by'])
                else:
                    col.update_by = user.username
                    col.save(update_fields=['update_by', 'update_time'])


class DataSourceViewSet(DatametaMixin,BaseViewSet):
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
        # vd = getattr(s, 'validated_data', {})
        # obj = DataSource.objects.create(**vd)
        return self.ok(msg='创建成功')


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = DataSourceUpdateSerializer(instance, data=request.data)
        s.is_valid(raise_exception=True)
        _password = s.validated_data.get('password',None)
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
            _password = vd.get('password',None)
            if _password and decrypt_password(_password) == instance.password:
                # 新密码与旧密码相同，不更新
                vd['password'] = instance.password
        else:
            s = DataSourceCreateSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data
        # print(f'vd:{vd}')
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

    @action(detail=False, methods=['post'], url_path='tables')
    def tables(self, request):
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            rows = list_tables_info(info)
            return self.raw_response({'rows': rows, 'total': len(rows)})
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='columns')
    def columns(self, request):
        ds_id = request.data.get('dataSourceId')
        table = request.data.get('tableName')
        dbname = request.data.get('databaseName')
        if not ds_id or not table:
            return self.error('缺少参数 dataSourceId 或 tableName')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            cols = get_table_schema(info, table)
            rows = [
                {
                    'order': c.get('order') or 0,
                    'name': c.get('name'),
                    'type': c.get('type') or '',
                    'notnull': bool(c.get('notnull')),
                    'default': str(c.get('default') or ''),
                    'primary': bool(c.get('primary')),
                    'comment': c.get('comment') or '',
                }
                for c in cols
            ]
            return self.raw_response({'rows': rows, 'total': len(rows)})
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='databases')
    def databases(self, request):
        ds_id = request.data.get('dataSourceId')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        try:
            dbs = get_databases(info)
            return self.raw_response({'data': dbs})
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='collect')
    def collect(self, request):
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            tbls = list_tables(info)
            with transaction.atomic():
                for t in tbls:
                    self._collect_table(info, ds.id, t)
            return self.ok('采集完成')
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='collect-table')
    def collect_table(self, request):
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        table = request.data.get('tableName')
        if not ds_id or not table:
            return self.error('缺少参数 dataSourceId 或 tableName')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            with transaction.atomic():
               self._collect_table(info, ds.id, table)
            return self.ok('采集完成')
        except Exception as e:
            return self.error(str(e))