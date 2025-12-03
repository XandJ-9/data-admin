from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.system.views.core import BaseViewSet, BaseViewMixin
from apps.system.permission import HasRolePermission
from apps.datasource.models import DataSource
from .models import QueryLog
from .serializers import DataServiceQuerySerializer, DataServiceQueryLogSerializer

from apps.dbutils.factory import get_executor
from django.template import Template, Context


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

        info = {
            'type': ds.db_type,
            'host': ds.host,
            'port': ds.port,
            'username': ds.username,
            'password': ds.password,
            'database': ds.db_name,
            'params': ds.params or {},
        }

        ex = get_executor(info)
        import time
        start = time.perf_counter()
        status_flag = 'success'
        error_msg = ''
        sql_raw = vd['sql']
        params_map = vd.get('params') or None

        # 先渲染模板 SQL
        try:
            rendered_sql = Template(sql_raw).render(Context(params_map)) if params_map else sql_raw
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            duration = int((time.perf_counter() - start) * 1000)
            try:
                QueryLog.objects.create(
                    data_source=ds,
                    sql_text=sql_raw,
                    username=getattr(request.user, 'username', '') or '',
                    status=status_flag,
                    duration_ms=duration,
                    error_msg=error_msg,
                )
            except Exception:
                pass
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
            duration = int((time.perf_counter() - start) * 1000)
            try:
                QueryLog.objects.create(
                    data_source=ds,
                    sql_text=rendered_sql,
                    username=getattr(request.user, 'username', '') or '',
                    status=status_flag,
                    duration_ms=duration,
                    error_msg=error_msg,
                )
            except Exception:
                pass
            ex.close()


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