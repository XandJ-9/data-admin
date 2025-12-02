from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.db import transaction

from apps.system.views.core import BaseViewSet
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
        MetaTable.objects.update_or_create(
            data_source_id=ds_id,
            table_name=table,
            defaults={'del_flag': '0'}
        )
        cols = get_table_schema(info, table)
        for c in cols:
            MetaColumn.objects.update_or_create(
                data_source_id=ds_id,
                table_name=table,
                name=c.get('name'),
                defaults={
                    'type': c.get('type') or '',
                    'notnull': bool(c.get('notnull')),
                    'default': str(c.get('default') or ''),
                    'primary': bool(c.get('primary')),
                    'del_flag': '0'
                }
            )


class MetaTableViewSet(DatametaMixin,BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaTable.objects.filter(del_flag='0').order_by('table_name')
    serializer_class = MetaTableSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ds_id = self.request.query_params.get('dataSourceId')
        if ds_id:
            try:
                qs = qs.filter(data_source_id=int(ds_id))
            except Exception:
                pass
        return qs

    @action(detail=False, methods=['post'], url_path='collect')
    def collect(self, request):
        ds_id = request.data.get('dataSourceId')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
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
        table = request.data.get('tableName')
        if not ds_id or not table:
            return self.error('缺少参数 dataSourceId 或 tableName')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        try:
            with transaction.atomic():
                self._collect_table(info, ds.id, table)
            return self.ok('采集完成')
        except Exception as e:
            return self.error(str(e))

class MetaColumnViewSet(DatametaMixin,BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaColumn.objects.filter(del_flag='0').order_by('table_name', 'name')
    serializer_class = MetaColumnSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ds_id = self.request.query_params.get('dataSourceId')
        table = self.request.query_params.get('tableName')
        if ds_id:
            try:
                qs = qs.filter(data_source_id=int(ds_id))
            except Exception:
                pass
        if table:
            qs = qs.filter(table_name=table)
        return qs

class BusinessDataView(DatametaMixin,BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]

    @action(detail=False, methods=['get'], url_path='tables')
    def tables(self, request):
        ds_id = request.query_params.get('dataSourceId')
        dbname = request.query_params.get('databaseName')
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

    @action(detail=False, methods=['get'], url_path='columns')
    def columns(self, request):
        ds_id = request.query_params.get('dataSourceId')
        table = request.query_params.get('tableName')
        dbname = request.query_params.get('databaseName')
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

    @action(detail=False, methods=['get'], url_path='databases')
    def databases(self, request):
        ds_id = request.query_params.get('dataSourceId')
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
