from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.db import transaction

from apps.system.views.core import BaseViewSet, BaseViewMixin
from apps.system.permission import HasRolePermission

from apps.datasource.models import DataSource
from apps.dbutils import list_tables, get_table_schema, get_table_info, list_tables_info, get_databases
from .models import MetaTable, MetaColumn
from .serializers import MetaTableSerializer, MetaColumnSerializer


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

class MetaTableViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaTable.objects.filter(del_flag='0').order_by('table_name')
    serializer_class = MetaTableSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # 数据源过滤
        ds_id = self.request.query_params.get('dataSourceId')
        if ds_id:
            try:
                qs = qs.filter(data_source_id=int(ds_id))
            except Exception:
                pass
        # 表名模糊
        tname = self.request.query_params.get('tableName')
        if tname:
            qs = qs.filter(table_name__icontains=tname)
        # 数据库名模糊
        dbname = self.request.query_params.get('databaseName')
        if dbname:
            qs = qs.filter(database__icontains=dbname)
        # 创建/修改时间范围
        def _parse_dt(val):
            from datetime import datetime
            if not val:
                return None
            try:
                val = str(val).rstrip('Z')
                return datetime.fromisoformat(val)
            except Exception:
                return None
        c_start = _parse_dt(self.request.query_params.get('createTimeStart'))
        c_end = _parse_dt(self.request.query_params.get('createTimeEnd'))
        if c_start:
            qs = qs.filter(create_time__gte=c_start)
        if c_end:
            qs = qs.filter(create_time__lte=c_end)
        u_start = _parse_dt(self.request.query_params.get('updateTimeStart'))
        u_end = _parse_dt(self.request.query_params.get('updateTimeEnd'))
        if u_start:
            qs = qs.filter(update_time__gte=u_start)
        if u_end:
            qs = qs.filter(update_time__lte=u_end)
        return qs

class MetaColumnViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaColumn.objects.filter(del_flag='0').order_by('order')
    serializer_class = MetaColumnSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ds_id = self.request.query_params.get('dataSourceId')
        if ds_id:
            try:
                qs = qs.filter(data_source_id=int(ds_id))
            except Exception:
                pass
        table = self.request.query_params.get('tableName')
        if table:
            qs = qs.filter(table__table_name=table)
        database = self.request.query_params.get('databaseName')
        if database:
            qs = qs.filter(table__database=database)
        return qs

class BusinessDataView(DatametaMixin,BaseViewMixin,ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]

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