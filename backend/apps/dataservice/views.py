from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.system.views.core import BaseViewSet, BaseViewMixin
from apps.system.permission import HasRolePermission
from apps.system.models import User
from apps.datasource.models import DataSource
from .models import QueryLog
from .serializers import (
    DataServiceQuerySerializer, DataServiceQueryLogSerializer,
    InterfaceInfoSerializer, InterfaceInfoCreateSerializer, InterfaceInfoUpdateSerializer,
    InterfaceFieldSerializer, InterfaceFieldUpdateSerializer,
)
from .models import InterfaceInfo, InterfaceField
from .custom import make_interface_workbook

from apps.dbutils.factory import get_executor
from django.template import Template, Context

import time

def _build_info(ds: DataSource):
    return {
        'type': ds.db_type,
        'host': ds.host,
        'port': ds.port,
        'username': ds.username,
        'password': ds.password,
        'database': ds.db_name,
        'params': ds.params or {},
    }

def _render_sql(sql_raw: str, params_map: dict):
    return Template(sql_raw).render(Context(params_map)) if params_map else sql_raw

def _log_query(ds: DataSource, sql_text: str, status_flag: str, start: float, error_msg: str, user: User):
    duration = int((time.perf_counter() - start) * 1000)
    try:
        QueryLog.objects.create(
            data_source=ds,
            sql_text=sql_text,
            username=getattr(user, 'username', '') or '',
            status=status_flag,
            duration_ms=duration,
            error_msg=str(error_msg or ''),
        )
    except Exception:
        pass


class QueryServiceView(BaseViewMixin, ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]

    # 使用 POST /dataservice/query 执行查询
    def query(self, request):
        s = DataServiceQuerySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data

        # 读取数据源
        try:
            ds = DataSource.objects.get(id=vd['dataSourceId'])
        except DataSource.DoesNotExist:
            return self.not_found('数据源不存在')

        info = _build_info(ds)
        ex = get_executor(info)
        start = time.perf_counter()
        status_flag = 'success'
        error_msg = ''
        sql_raw = vd['sql']
        params_map = vd.get('params') or None

        # 先渲染模板 SQL
        try:
            rendered_sql = _render_sql(sql_raw, params_map)
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            _log_query(ds, sql_raw, status_flag, start, error_msg, request.user)
            ex.close()
            return self.error(error_msg)

        # 执行查询
        try:
            res = ex.execute_query(
                sql=rendered_sql,
                page_size=vd.get('pageSize', 100),
                offset=vd.get('offset', 0),
            )
            return self.data(res)
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            return self.error(error_msg)
        finally:
            _log_query(ds, rendered_sql, status_flag, start, error_msg, request.user)
            ex.close()

    def export(self, request):
        # 验证请求体
        s = DataServiceQuerySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data

        # 读取数据源
        try:
            ds = DataSource.objects.get(id=vd['dataSourceId'])
        except DataSource.DoesNotExist:
            return self.not_found('数据源不存在')

        info = _build_info(ds)

        ex = get_executor(info)
        start = time.perf_counter()
        status_flag = 'success'
        error_msg = ''
        sql_raw = vd['sql']
        params_map = vd.get('params') or None

        # 渲染模板 SQL
        try:
            rendered_sql = _render_sql(sql_raw, params_map)
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            _log_query(ds, sql_raw, status_flag, start, error_msg, request.user)
            ex.close()
            return self.error(error_msg)

        # 执行查询（导出固定取前 10000 行，从 0 开始）
        try:
            res = ex.execute_query(
                sql=rendered_sql,
                page_size=10000,
                offset=0,
            )
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            duration = int((time.perf_counter() - start) * 1000)
            try:
                _log_query(ds, rendered_sql, status_flag, start, error_msg, request.user)
            except Exception:
                pass
            ex.close()
            return self.error(error_msg)
        finally:
            _log_query(ds, rendered_sql, status_flag, start, error_msg, request.user)
            # 不在 finally 关闭，导出完成后再关闭

        # 生成 CSV 响应
        data = res or {}
        columns = data.get('columns') or []
        rows = data.get('rows') or []
        import datetime
        filename = f"query_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        resp = self.csv_response(columns, rows, filename, bom=True)
        ex.close()
        return resp

class QueryLogViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = QueryLog.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = DataServiceQueryLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user_name = self.request.query_params.get('userName', '')
        status_value = self.request.query_params.get('status', '')
        if user_name:
            qs = qs.filter(username__icontains=user_name)
        if status_value in ('success', 'fail'):
            qs = qs.filter(status=status_value)
        return qs.order_by('-create_time')


class InterfaceInfoViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = InterfaceInfo.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = InterfaceInfoSerializer
    update_body_serializer_class = InterfaceInfoUpdateSerializer
    update_body_id_field = 'interfaceId'

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get('interfaceName', '')
        code = self.request.query_params.get('interfaceCode', '')
        db_type = self.request.query_params.get('interfaceDbType', '')
        if name:
            qs = qs.filter(interface_name__icontains=name)
        if code:
            qs = qs.filter(interface_code__icontains=code)
        if db_type:
            qs = qs.filter(interface_db_type=db_type)
        return qs.order_by('-create_time')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_by_id(self, request, pk=None, execute_type='1'):
        try:
            interface = InterfaceInfo.objects.get(id=pk, del_flag='0')
        except InterfaceInfo.DoesNotExist:
            return self.not_found('接口不存在')
        ds_id = interface.interface_datasource
        if not ds_id:
            return self.error('接口未配置数据源')
        try:
            ds = DataSource.objects.get(id=ds_id)
        except DataSource.DoesNotExist:
            return self.not_found('数据源不存在')
        info = _build_info(ds)
        ex = get_executor(info)
        start = time.perf_counter()
        status_flag = 'success'
        error_msg = ''
        sql_raw = interface.interface_sql or ''
        params_map = request.data.get('params') or None
        # 渲染模板 SQL
        try:
            rendered_sql = _render_sql(sql_raw, params_map)
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            _log_query(ds, sql_raw, status_flag, start, error_msg, request.user)
            ex.close()
            return self.error(error_msg)
        # 执行查询
        try:
            res = ex.execute_query(
                sql=rendered_sql,
                page_size=int(request.data.get('pageSize') or 100),
                offset=int(request.data.get('offset') or 0),
            )
            return self.data(res)
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            return self.error(error_msg)
        finally:
            _log_query(ds, rendered_sql, status_flag, start, error_msg, request.user)
            ex.close()

    @action(detail=True, methods=['post'], url_path='export')
    def export_by_id(self, request, pk=None):
        # 复用 execute 逻辑，取结果并导出为 CSV
        exec_resp = self.execute_by_id(request, pk, execute_type='2')
        if isinstance(exec_resp, Response) and getattr(exec_resp, 'status_code', 200) != 200:
            return exec_resp
        data = exec_resp.data.get('data', None) or {}
        columns = data.get('columns', None)
        rows = data.get('rows', None)
        # 写 CSV
        filename = f"interface_{pk}_export.csv"
        resp = self.csv_response(columns, rows, filename, bom=False)
        return resp

    @action(detail=True, methods=['get'], url_path='export-meta')
    def export_meta(self, request, pk=None):
        # 使用样式化 Excel 生成器导出接口定义（基本信息 + 字段列表）
        try:
            interface = InterfaceInfo.objects.get(id=pk, del_flag='0')
        except InterfaceInfo.DoesNotExist:
            return self.not_found('接口不存在')

        fields = InterfaceField.objects.filter(interface=interface, del_flag='0').order_by('interface_para_position')

        wb = make_interface_workbook(interface, list(fields))

        import datetime
        filename = f"interface_meta_{pk}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self.excel_response(filename, wb)


class InterfaceFieldViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = InterfaceField.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = InterfaceFieldSerializer
    update_body_serializer_class = InterfaceFieldUpdateSerializer
    update_body_id_field = 'fieldId'

    def get_queryset(self):
        qs = super().get_queryset()
        interface_id = self.request.query_params.get('interfaceId')
        try:
            interface_id = int(interface_id) if interface_id is not None else None
        except Exception:
            interface_id = None
        if interface_id:
            qs = qs.filter(interface_id=interface_id)
        return qs.order_by('-create_time')
