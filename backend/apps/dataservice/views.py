from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.system.views.core import BaseViewSet, BaseViewMixin
from apps.system.permission import HasRolePermission
from apps.system.models import User
from apps.datasource.models import DataSource
from .models import QueryLog
from .serializers import (
    DataServiceQuerySerializer, DataServiceQueryLogSerializer, InterfacePublishSerializer,
    InterfaceChangeStatusSerializer, InterfaceInfoSerializer, InterfaceInfoCreateSerializer,
    InterfaceInfoUpdateSerializer, InterfaceFieldSerializer, InterfaceFieldUpdateSerializer,
    ReportInfoSerializer, ReportInfoUpdateSerializer,
)
from .models import InterfaceInfo, InterfaceField, ReportInfo, ReportInterfaceRelation
from .custom import make_interface_workbook, parse_interface_workbook
from .query_wrapper import InterfaceQueryWrapper

from apps.dbutils.factory import get_executor
from django.template import Template, Context
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.db.models import F, Prefetch
from openpyxl import load_workbook

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

def _render_sql(sql_raw: str, params_map: dict, default_map: dict = {}):
    context_map = {**default_map, **(params_map or {})}
    # return Template(sql_raw).render(Context(context_map)) if params_map else sql_raw
    return Template(sql_raw).render(Context(context_map))

def _log_query(ds: DataSource, sql_text: str, status_flag: str, start: float, error_msg: str, user: User, query_type: str = 'sql'):
    duration = int((time.perf_counter() - start) * 1000)
    try:
        QueryLog.objects.create(
            data_source=ds,
            sql_text=sql_text,
            username=getattr(user, 'username', '') or '',
            status=status_flag,
            duration_ms=duration,
            error_msg=str(error_msg or ''),
            query_type=query_type
        )
    except Exception:
        pass


def _normalize_output_columns(columns):
    normalized_columns = []
    seen_names = set()
    for index, column in enumerate(columns or [], start=1):
        column_name = str(column or '').strip() or f'column_{index}'
        if column_name in seen_names:
            raise ValueError(f'查询结果字段“{column_name}”重复，请在 SQL 中设置唯一别名后再发布')
        seen_names.add(column_name)
        normalized_columns.append(column_name)
    if not normalized_columns:
        raise ValueError('请先执行 SQL，确保查询结果中包含可发布字段')
    return normalized_columns


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
            # import traceback
            # traceback.print_exception(e)
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
                page_size=vd.get('pageSize', 10000),
                offset=vd.get('offset', 0),
            )
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
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
        enable = self.request.query_params.get('enable', '')
        user_name = self.request.query_params.get('userName', '')
        if name:
            qs = qs.filter(interface_name__icontains=name)
        if code:
            qs = qs.filter(interface_code__icontains=code)
        if db_type:
            qs = qs.filter(interface_db_type=db_type)
        if enable in ('0', '1'):
            qs = qs.filter(enable=enable)
        if user_name:
            qs = qs.filter(user_name__icontains=user_name)
        return qs.order_by('-create_time')

    def perform_create(self, serializer):
        username = getattr(self.request.user, 'username', '') or ''
        interface_code = str(serializer.validated_data.get('interface_code') or '').strip()
        if interface_code and InterfaceInfo.objects.filter(interface_code=interface_code).exists():
            raise ValidationError('接口编码已存在，请更换后再创建')
        if username and not str(serializer.validated_data.get('user_name') or '').strip():
            serializer.validated_data['user_name'] = username
        try:
            super().perform_create(serializer)
        except IntegrityError as exc:
            if 'interface_code' in str(exc).lower() or 'unique' in str(exc).lower():
                raise ValidationError('接口编码已存在，请更换后再创建')
            raise

    def perform_update(self, serializer):
        username = getattr(self.request.user, 'username', '') or ''
        interface_code = str(serializer.validated_data.get('interface_code') or '').strip()
        current_id = getattr(serializer.instance, 'id', None)
        if interface_code and InterfaceInfo.objects.filter(interface_code=interface_code).exclude(id=current_id).exists():
            raise ValidationError('接口编码已存在，请更换后再保存')
        current_owner = getattr(serializer.instance, 'user_name', '') if serializer.instance else ''
        if not str(serializer.validated_data.get('user_name') or '').strip():
            serializer.validated_data['user_name'] = current_owner or username
        try:
            super().perform_update(serializer)
        except IntegrityError as exc:
            if 'interface_code' in str(exc).lower() or 'unique' in str(exc).lower():
                raise ValidationError('接口编码已存在，请更换后再保存')
            raise

    @action(detail=False, methods=['put'], url_path='changeStatus')
    def change_status(self, request):
        serializer = InterfaceChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interface_id = serializer.validated_data['interfaceId']
        enable_value = serializer.validated_data['enable']

        try:
            interface = InterfaceInfo.objects.get(id=interface_id, del_flag='0')
        except InterfaceInfo.DoesNotExist:
            return self.not_found('接口不存在')

        interface.enable = enable_value
        username = getattr(request.user, 'username', '') or ''
        if username:
            interface.update_by = username
            interface.save(update_fields=['enable', 'update_by', 'update_time'])
        else:
            interface.save(update_fields=['enable', 'update_time'])
        return self.ok('接口状态修改成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        interfaces = instance if isinstance(instance, list) else [instance]
        online_interfaces = [item.interface_name for item in interfaces if item.enable == '1']
        if online_interfaces:
            if len(online_interfaces) == 1:
                return self.error(f'接口“{online_interfaces[0]}”仍处于上线状态，请先下线后再删除')
            return self.error('选中的接口中包含已上线接口，请先下线后再删除')

        username = getattr(request.user, 'username', '') or ''
        interface_ids = [item.id for item in interfaces]
        with transaction.atomic():
            for item in interfaces:
                item.del_flag = '1'
                if username:
                    item.update_by = username
                    item.save(update_fields=['del_flag', 'update_by', 'update_time'])
                else:
                    item.save(update_fields=['del_flag', 'update_time'])

            field_updates = {'del_flag': '1', 'update_time': timezone.now()}
            if username:
                field_updates['update_by'] = username
            InterfaceField.objects.filter(interface_id__in=interface_ids, del_flag='0').update(**field_updates)
        return self.ok('删除成功')

    @action(detail=False, methods=['post'], url_path='publish')
    def publish_from_query(self, request):
        serializer = InterfacePublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if InterfaceInfo.objects.filter(interface_code=validated_data['interfaceCode']).exists():
            return self.error('接口编码已存在，请更换后再发布')

        try:
            data_source = DataSource.objects.get(id=validated_data['dataSourceId'], del_flag='0')
        except DataSource.DoesNotExist:
            return self.not_found('数据源不存在')

        try:
            output_columns = _normalize_output_columns(validated_data.get('outputColumns'))
        except ValueError as exc:
            return self.error(str(exc))

        params_map = validated_data.get('params') or {}
        username = getattr(request.user, 'username', '') or ''

        with transaction.atomic():
            interface = InterfaceInfo.objects.create(
                interface_name=validated_data['interfaceName'],
                interface_code=validated_data['interfaceCode'],
                interface_desc=validated_data.get('interfaceDesc') or '由 SQL 查询发布',
                interface_db_type=data_source.db_type,
                interface_db_name=data_source.db_name,
                interface_sql=validated_data['sql'],
                is_total=validated_data.get('isTotal', '0'),
                total_sql=validated_data.get('totalSql') or '',
                is_paging=validated_data.get('isPaging', '1'),
                is_date_option='0',
                is_second_table='0',
                is_login_visit='0',
                alarm_type='0',
                enable=validated_data.get('enable', '1'),
                user_name=username,
                interface_datasource=data_source.id,
                create_by=username,
                update_by=username,
            )

            input_position = 1
            for param_code, default_value in params_map.items():
                normalized_code = str(param_code or '').strip()
                if not normalized_code:
                    continue
                InterfaceField.objects.create(
                    interface=interface,
                    interface_para_code=normalized_code,
                    interface_para_name=normalized_code,
                    interface_para_position=input_position,
                    interface_para_type='1',
                    interface_data_type='1',
                    interface_para_default='' if default_value is None else str(default_value),
                    interface_show_flag='1',
                    interface_export_flag='0',
                    interface_para_desc='SQL 模板参数',
                    create_by=username,
                    update_by=username,
                )
                input_position += 1

            for output_position, column_name in enumerate(output_columns, start=1):
                InterfaceField.objects.create(
                    interface=interface,
                    interface_para_code=column_name,
                    interface_para_name=column_name,
                    interface_para_position=output_position,
                    interface_para_type='2',
                    interface_data_type='1',
                    interface_show_flag='1',
                    interface_export_flag='1',
                    interface_para_desc='SQL 查询结果字段',
                    create_by=username,
                    update_by=username,
                )

        return self.data({'interfaceId': interface.id})

    def _execute_interface_payload(self, request, interface, page_size, offset, record_log=True):
        if interface.enable != '1':
            return {'code': '-1', 'message': '接口已下线，不能执行查询'}

        ds_id = interface.interface_datasource
        if not ds_id:
            return {'code': '-1', 'message': '接口未配置数据源'}

        try:
            ds = DataSource.objects.get(id=ds_id)
        except DataSource.DoesNotExist:
            return {'code': '-1', 'message': '数据源不存在'}

        info = _build_info(ds)
        ex = get_executor(info)
        start = time.perf_counter()
        status_flag = 'success'
        error_msg = ''
        sql_raw = interface.interface_sql or ''
        total_sql_raw = interface.total_sql or ''
        params_map = request.data.get('params') or None

        try:
            rendered_sql = _render_sql(sql_raw, params_map)
            rendered_total_sql = _render_sql(total_sql_raw, params_map) if interface.is_total == '1' and total_sql_raw else None
            wrapper = InterfaceQueryWrapper(
                interface=interface,
                executor=ex,
                offset=offset,
                page_size=page_size,
            )
            result = wrapper.execute(rendered_sql, rendered_total_sql)
            if result.get('code') != '0':
                status_flag = 'fail'
                error_msg = result.get('message') or '接口查询失败'
            return result
        except Exception as exc:
            status_flag = 'fail'
            error_msg = str(exc)
            return {'code': '-1', 'message': f'接口查询失败：{error_msg}'}
        finally:
            if record_log:
                _log_query(ds, sql_raw, status_flag, start, error_msg, request.user, query_type='interface')
            ex.close()

    @action(detail=True, methods=['post'], url_path='test')
    def test_by_id(self, request, pk=None):
        """试运行接口（限 10 行，不记录日志）"""
        try:
            interface = InterfaceInfo.objects.get(id=pk, del_flag='0')
        except InterfaceInfo.DoesNotExist:
            return Response({'code': '-1', 'message': '接口不存在'})
        result = self._execute_interface_payload(request, interface, page_size=10, offset=0, record_log=False)
        return Response(result)

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_by_id(self, request, pk=None, execute_type='1'):
        try:
            interface = InterfaceInfo.objects.get(id=pk, del_flag='0')
        except InterfaceInfo.DoesNotExist:
            return Response({'code': '-1', 'message': '接口不存在'})

        result = self._execute_interface_payload(
            request,
            interface,
            page_size=int(request.data.get('pageSize') or 100),
            offset=int(request.data.get('offset') or 0),
        )
        return Response(result)

    @action(detail=True, methods=['post'], url_path='export')
    def export_by_id(self, request, pk=None):
        obj = self.get_object()
        result = self._execute_interface_payload(
            request,
            obj,
            page_size=int(request.data.get('pageSize') or 10000),
            offset=int(request.data.get('offset') or 0),
        )
        if result.get('code') != '0':
            return Response(result)

        output_fields = list(
            InterfaceField.objects.filter(
                interface=obj,
                del_flag='0',
                interface_para_type='2',
            ).order_by('interface_para_position', 'id')
        )
        columns = [field.interface_para_code for field in output_fields]
        records = result.get('data') or []
        if isinstance(records, dict):
            records = records.get('list') or []
        if not columns and records:
            columns = list(records[0].keys())
        rows = [[record.get(column) for column in columns] for record in records]
        filename = f"接口数据导出-{obj.interface_name}.csv"
        return self.csv_response(columns, rows, filename, bom=False)

    @action(detail=True, methods=['post'], url_path='export-meta')
    def export_meta(self, request, pk=None):
        # 使用样式化 Excel 生成器导出接口定义（基本信息 + 字段列表）
        # try:
        #     interface = InterfaceInfo.objects.get(id=pk, del_flag='0')
        # except InterfaceInfo.DoesNotExist:
        #     return self.not_found('接口不存在')

        interface = self.get_object()
        fields = InterfaceField.objects.filter(interface=interface, del_flag='0').order_by('interface_para_position')
        wb = make_interface_workbook(interface, list(fields))

        filename = f"{interface.interface_name}.xlsx"
        return self.excel_response(filename, wb)
    
    @action(detail=False, methods=['post'], url_path='export')
    def export_by_body(self, request):
        """按请求体导出数据（dataSourceId + sql + params），等同于 /dataservice/export"""
        s = DataServiceQuerySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data
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
        try:
            rendered_sql = _render_sql(sql_raw, params_map)
        except Exception as e:
            ex.close()
            return self.error(str(e))
        try:
            res = ex.execute_query(
                sql=rendered_sql,
                page_size=vd.get('pageSize', 10000),
                offset=vd.get('offset', 0),
            )
        except Exception as e:
            status_flag = 'fail'
            error_msg = str(e)
            ex.close()
            _log_query(ds, rendered_sql, status_flag, start, error_msg, request.user)
            return self.error(error_msg)
        finally:
            _log_query(ds, rendered_sql, status_flag, start, error_msg, request.user)
        data = res or {}
        columns = data.get('columns') or []
        rows = data.get('rows') or []
        import datetime
        filename = f"interface_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        resp = self.csv_response(columns, rows, filename, bom=True)
        ex.close()
        return resp

    @action(detail=False, methods=['post'], url_path='import-meta')
    def import_meta(self, request):
        """导入接口定义 Excel """
        file = request.FILES.get('file')
        if not file:
            return self.error('请上传 Excel 文件')
        
        try:
            wb = load_workbook(file, data_only=True)
            results = parse_interface_workbook(wb)
        except Exception as e:
            return self.error(f'解析 Excel 失败: {str(e)}')
            
        if not results:
            return self.error('未解析到有效的接口定义')
            
        success_count = 0
        try:
            with transaction.atomic():
                for info, fields in results:
                    # 1. 保存/更新接口信息
                    # 查找是否存在
                    obj, created = InterfaceInfo.objects.update_or_create(
                        interface_code=info.interface_code,
                        defaults={
                            'interface_name': info.interface_name,
                            'interface_desc': info.interface_desc,
                            'interface_db_type': info.interface_db_type,
                            'interface_db_name': info.interface_db_name,
                            'interface_sql': info.interface_sql,
                            'is_total': info.is_total,
                            'total_sql': info.total_sql,
                            'is_paging': info.is_paging,
                            'is_date_option': info.is_date_option,
                            'is_second_table': info.is_second_table,
                            'is_login_visit': info.is_login_visit,
                            'alarm_type': info.alarm_type,
                            'enable': info.enable,
                            'user_name': info.user_name,
                            # 'interface_datasource': info.interface_datasource, # 不更新数据源，避免误改
                            'del_flag': '0', # 确保未删除
                            # 报表归属信息
                            'platform_name': info.platform_name,
                            'module_name': info.module_name,
                            'report_name': info.report_name,
                            'report_code': info.report_code,
                        }
                    )
                    
                    # 2. 保存字段信息
                    # 先删除旧字段
                    InterfaceField.objects.filter(interface=obj).delete()
                    
                    # 批量创建新字段
                    for field in fields:
                        field.interface = obj
                        field.del_flag = '0'
                    
                    InterfaceField.objects.bulk_create(fields)
                    success_count += 1
                    
        except Exception as e:
            return self.error(f'导入失败: {str(e)}')
            
        return self.ok(msg=f'成功导入 {success_count} 个接口')


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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        position = instance.interface_para_position
        para_type = instance.interface_para_type
        interface = instance.interface
        
        response = super().destroy(request, *args, **kwargs)
        
        # 删除成功后，后续字段位置前移
        if response.status_code == 200:
            InterfaceField.objects.filter(
                interface=interface,
                interface_para_type=para_type,
                del_flag='0',
                interface_para_position__gt=position
            ).update(interface_para_position=F('interface_para_position') - 1)
            
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        instance = serializer.instance
        # 新增字段时，自动调整后续字段位置
        if instance:
            InterfaceField.objects.filter(
                interface=instance.interface,
                interface_para_type=instance.interface_para_type,
                del_flag='0',
                interface_para_position__gte=instance.interface_para_position
            ).exclude(id=instance.id).update(
                interface_para_position=F('interface_para_position') + 1
            )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_position = instance.interface_para_position
        old_type = instance.interface_para_type
        
        super().perform_update(serializer)
        
        new_instance = serializer.instance
        if not new_instance:
            return

        new_position = new_instance.interface_para_position
        new_type = new_instance.interface_para_type

        # 如果类型改变
        if old_type != new_type:
            # 旧组：删除（后续前移）
            InterfaceField.objects.filter(
                interface=new_instance.interface,
                interface_para_type=old_type,
                del_flag='0',
                interface_para_position__gt=old_position
            ).update(interface_para_position=F('interface_para_position') - 1)

            # 新组：插入（后续后移）
            InterfaceField.objects.filter(
                interface=new_instance.interface,
                interface_para_type=new_type,
                del_flag='0',
                interface_para_position__gte=new_position
            ).exclude(id=new_instance.id).update(
                interface_para_position=F('interface_para_position') + 1
            )
        else:
            # 类型不变，位置改变
            if old_position != new_position:
                qs = InterfaceField.objects.filter(
                    interface=new_instance.interface,
                    interface_para_type=new_type,
                    del_flag='0'
                ).exclude(id=new_instance.id)

                if new_position < old_position:
                    # 前移：[new, old) 后移
                    qs.filter(
                        interface_para_position__gte=new_position,
                        interface_para_position__lt=old_position
                    ).update(interface_para_position=F('interface_para_position') + 1)
                else:
                    # 后移：(old, new] 前移
                    qs.filter(
                        interface_para_position__gt=old_position,
                        interface_para_position__lte=new_position
                    ).update(interface_para_position=F('interface_para_position') - 1)



class ReportInfoViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = ReportInfo.objects.filter(del_flag='0').order_by('-create_time')
    serializer_class = ReportInfoSerializer
    update_body_serializer_class = ReportInfoUpdateSerializer
    update_body_id_field = 'reportId'

    def get_queryset(self):
        active_relations = Prefetch(
            'report_interfaces',
            queryset=ReportInterfaceRelation.objects.filter(del_flag='0').select_related('interface').order_by('interface_position', 'id'),
            to_attr='prefetched_active_relations',
        )
        qs = super().get_queryset().prefetch_related(active_relations)
        report_name = self.request.query_params.get('reportName', '')
        report_code = self.request.query_params.get('reportCode', '')
        user_name = self.request.query_params.get('userName', '')
        if report_name:
            qs = qs.filter(report_name__icontains=report_name)
        if report_code:
            qs = qs.filter(report_code__icontains=report_code)
        if user_name:
            qs = qs.filter(user_name__icontains=user_name)
        return qs.order_by('-create_time')

    def perform_create(self, serializer):
        username = getattr(self.request.user, 'username', '') or ''
        report_code = str(serializer.validated_data.get('report_code') or '').strip()
        if report_code and ReportInfo.objects.filter(report_code=report_code).exists():
            raise ValidationError('报表编码已存在，请更换后再创建')
        if username and not str(serializer.validated_data.get('user_name') or '').strip():
            serializer.validated_data['user_name'] = username
        try:
            super().perform_create(serializer)
        except IntegrityError as exc:
            if 'report_code' in str(exc).lower() or 'unique' in str(exc).lower():
                raise ValidationError('报表编码已存在，请更换后再创建')
            raise

    def perform_update(self, serializer):
        username = getattr(self.request.user, 'username', '') or ''
        report_code = str(serializer.validated_data.get('report_code') or '').strip()
        current_id = getattr(serializer.instance, 'id', None)
        if report_code and ReportInfo.objects.filter(report_code=report_code).exclude(id=current_id).exists():
            raise ValidationError('报表编码已存在，请更换后再保存')
        current_owner = getattr(serializer.instance, 'user_name', '') if serializer.instance else ''
        if not str(serializer.validated_data.get('user_name') or '').strip():
            serializer.validated_data['user_name'] = current_owner or username
        try:
            super().perform_update(serializer)
        except IntegrityError as exc:
            if 'report_code' in str(exc).lower() or 'unique' in str(exc).lower():
                raise ValidationError('报表编码已存在，请更换后再保存')
            raise

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        reports = instance if isinstance(instance, list) else [instance]
        username = getattr(request.user, 'username', '') or ''
        report_ids = [item.id for item in reports]
        with transaction.atomic():
            for item in reports:
                item.del_flag = '1'
                if username:
                    item.update_by = username
                    item.save(update_fields=['del_flag', 'update_by', 'update_time'])
                else:
                    item.save(update_fields=['del_flag', 'update_time'])

            ReportInterfaceRelation.objects.filter(report_id__in=report_ids, del_flag='1').delete()
            relation_updates = {'del_flag': '1', 'update_time': timezone.now()}
            if username:
                relation_updates['update_by'] = username
            ReportInterfaceRelation.objects.filter(report_id__in=report_ids, del_flag='0').update(**relation_updates)
        return self.ok('删除成功')
