from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission

from apps.datasource.models import DataSource
from .models import MetaTable, MetaColumn
from .serializers import MetaTableSerializer, MetaColumnSerializer



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

