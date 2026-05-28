from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.common.encrypt import encrypt_password
from apps.dataasset.models import AssetNamespace, DataAsset
from apps.datasource.models import DataSource
from apps.system.models import Role, UserRole

from .models import InterfaceField, InterfaceInfo, ReportInfo, ReportInterfaceRelation
from .serializers import InterfaceInfoCreateSerializer
from .views import InterfaceInfoViewSet, QueryServiceView, ReportInfoViewSet, _validate_readonly_sql


class _MockExecutor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def execute_query(self, sql, params=None, page_size=None, offset=None):
        self.calls.append({'sql': sql, 'page_size': page_size, 'offset': offset})
        if not self.responses:
            raise AssertionError('No mocked executor response left')
        return self.responses.pop(0)

    def close(self):
        return None


def _build_interface_payload(interface_code='frontend_api', interface_name='前端接口', enable='1'):
    return {
        'interfaceName': interface_name,
        'interfaceCode': interface_code,
        'interfaceDesc': '前端接口测试',
        'interfaceDbType': 'mysql',
        'interfaceDbName': 'demo',
        'interfaceSql': 'select 1 as id',
        'isTotal': '0',
        'totalSql': '',
        'isPaging': '1',
        'isDateOption': '0',
        'isSecondTable': '0',
        'isLoginVisit': '0',
        'alarmType': '0',
        'enable': enable,
    }


def _build_field_payload(interface_id, code='id', position=1, para_type='2'):
    return {
        'interfaceId': interface_id,
        'interfaceParaCode': code,
        'interfaceParaName': f'{code}_name',
        'interfaceParaPosition': position,
        'interfaceParaType': para_type,
        'interfaceDataType': '1',
        'interfaceParaDefault': '',
        'interfaceShowFlag': '1',
        'interfaceExportFlag': '1',
        'interfaceShowDesc': '',
        'interfaceParaDesc': '字段说明',
    }


class InterfacePublishTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')
        admin_role = Role.objects.create(role_name='管理员', role_key='admin', role_sort=0, status='0')
        UserRole.objects.create(user=self.user, role=admin_role)
        self.data_source = DataSource.objects.create(
            name='demo-source',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='demo',
            username='root',
            password=encrypt_password('secret'),
            params='{}',
            status='0',
        )

    def test_readonly_sql_validator_should_reject_mutation_sql(self):
        with self.assertRaises(ValueError):
            _validate_readonly_sql('delete from demo_user')

    def test_readonly_sql_validator_should_reject_multi_statement_sql(self):
        with self.assertRaises(ValueError):
            _validate_readonly_sql('select 1; drop table demo_user')

    @patch('apps.dataservice.views.get_executor')
    def test_query_should_cap_page_size(self, mock_get_executor):
        executor = _MockExecutor([{'columns': ['id'], 'rows': [(1,)]}])
        mock_get_executor.return_value = executor
        view = QueryServiceView.as_view({'post': 'query'})
        request = self.factory.post(
            '/data-api/dataservice/query',
            {
                'dataSourceId': self.data_source.id,
                'sql': 'select id from demo_user',
                'pageSize': 99999,
                'offset': 0,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(executor.calls[0]['page_size'], 500)

    def test_interface_info_serializer_should_require_total_sql_when_total_enabled(self):
        serializer = InterfaceInfoCreateSerializer(data={
            'interfaceName': '汇总接口',
            'interfaceCode': 'summary_api',
            'interfaceDbType': 'mysql',
            'interfaceDbName': 'demo',
            'interfaceSql': 'select 1',
            'isTotal': '1',
            'totalSql': '',
            'isPaging': '1',
            'isDateOption': '0',
            'isSecondTable': '0',
            'isLoginVisit': '0',
            'alarmType': '0',
            'enable': '1',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_project_urlconf_should_include_dataservice_routes(self):
        match = resolve('/data-api/dataservice/query')

        self.assertEqual(match.url_name, 'dataservice-query')

    @patch('apps.dataservice.views.get_executor')
    def test_project_export_route_should_return_csv_attachment(self, mock_get_executor):
        interface = InterfaceInfo.objects.create(
            interface_name='导出接口',
            interface_code='export_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select id, name from demo_user',
            interface_datasource=self.data_source.id,
            is_paging='1',
            enable='1',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='id',
            interface_para_name='用户ID',
            interface_para_position=1,
            interface_para_type='2',
            interface_data_type='2',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='name',
            interface_para_name='用户名',
            interface_para_position=2,
            interface_para_type='2',
            interface_data_type='1',
        )
        mock_get_executor.return_value = _MockExecutor([
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice'), (2, 'Bob')]},
            {'columns': ['total_count'], 'rows': [(2,)]},
        ])

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/data-api/dataservice/interface-info/{interface.id}/export',
            {'params': {}, 'pageSize': 20, 'offset': 0},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('filename=', response['Content-Disposition'])

    def test_publish_from_query_should_create_interface_and_fields(self):
        namespace = AssetNamespace.objects.create(
            data_source=self.data_source,
            environment='default',
            catalog_name='demo',
            schema_name='',
        )
        asset = DataAsset.objects.create(
            namespace=namespace,
            object_name='demo_user',
            display_name='用户表',
        )
        view = InterfaceInfoViewSet.as_view({'post': 'publish_from_query'})
        request = self.factory.post(
            '/data-api/dataservice/interface-info/publish',
            {
                'dataSourceId': self.data_source.id,
                'assetId': asset.id,
                'sql': 'select id, name from demo_user where dt = {{ biz_date }}',
                'params': {'biz_date': '2026-04-19'},
                'outputColumns': ['id', 'name'],
                'interfaceName': '用户列表接口',
                'interfaceCode': 'user_list_api',
                'interfaceDesc': '由 SQL 查询发布',
                'isTotal': '1',
                'totalSql': 'select count(1) from demo_user where dt = {{ biz_date }}',
                'isPaging': '1',
                'enable': '1',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        interface = InterfaceInfo.objects.get(interface_code='user_list_api')
        self.assertEqual(interface.interface_datasource, self.data_source.id)
        self.assertEqual(interface.asset_id, asset.id)
        self.assertEqual(interface.interface_db_type, 'mysql')
        self.assertEqual(interface.interface_db_name, 'demo')
        self.assertEqual(interface.interface_sql, 'select id, name from demo_user where dt = {{ biz_date }}')
        self.assertEqual(interface.is_total, '1')
        self.assertEqual(interface.total_sql, 'select count(1) from demo_user where dt = {{ biz_date }}')
        self.assertEqual(interface.is_paging, '1')

        fields = InterfaceField.objects.filter(interface=interface, del_flag='0').order_by('interface_para_type', 'interface_para_position')
        self.assertEqual(fields.count(), 3)

        input_field = fields.filter(interface_para_type='1').get()
        self.assertEqual(input_field.interface_para_code, 'biz_date')
        self.assertEqual(input_field.interface_para_default, '2026-04-19')

        output_codes = list(fields.filter(interface_para_type='2').values_list('interface_para_code', flat=True))
        self.assertEqual(output_codes, ['id', 'name'])

    def test_publish_from_query_should_reject_duplicate_output_columns(self):
        view = InterfaceInfoViewSet.as_view({'post': 'publish_from_query'})
        request = self.factory.post(
            '/data-api/dataservice/interface-info/publish',
            {
                'dataSourceId': self.data_source.id,
                'sql': 'select id, id from demo_user',
                'params': {},
                'outputColumns': ['id', 'id'],
                'interfaceName': '重复字段接口',
                'interfaceCode': 'duplicated_columns_api',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertIn('重复', response.data['msg'])
        self.assertFalse(InterfaceInfo.objects.filter(interface_code='duplicated_columns_api').exists())

    def test_change_status_should_update_enable(self):
        interface = InterfaceInfo.objects.create(
            interface_name='生命周期接口',
            interface_code='lifecycle_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            enable='1',
        )

        view = InterfaceInfoViewSet.as_view({'put': 'change_status'})
        request = self.factory.put(
            '/data-api/dataservice/interface-info/changeStatus',
            {'interfaceId': interface.id, 'enable': '0'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        interface.refresh_from_db()
        self.assertEqual(interface.enable, '0')

    def test_create_should_default_owner_to_current_user(self):
        view = InterfaceInfoViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataservice/interface-info',
            {
                'interfaceName': '默认负责人接口',
                'interfaceCode': 'default_owner_api',
                'interfaceDbType': 'mysql',
                'interfaceDbName': 'demo',
                'interfaceSql': 'select 1',
                'isTotal': '0',
                'isPaging': '1',
                'isDateOption': '0',
                'isSecondTable': '0',
                'isLoginVisit': '0',
                'alarmType': '0',
                'enable': '1',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        interface = InterfaceInfo.objects.get(interface_code='default_owner_api')
        self.assertEqual(interface.user_name, self.user.username)

    def test_list_should_support_enable_and_owner_filters(self):
        InterfaceInfo.objects.create(
            interface_name='在线接口',
            interface_code='online_owner_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            enable='1',
            user_name='owner_a',
        )
        InterfaceInfo.objects.create(
            interface_name='下线接口',
            interface_code='offline_owner_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            enable='0',
            user_name='owner_b',
        )

        view = InterfaceInfoViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/dataservice/interface-info', {'enable': '1', 'userName': 'owner_a'})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['interfaceCode'], 'online_owner_api')

    def test_destroy_should_require_offline_and_soft_delete_fields(self):
        interface = InterfaceInfo.objects.create(
            interface_name='待删除接口',
            interface_code='delete_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            enable='1',
        )
        field = InterfaceField.objects.create(
            interface=interface,
            interface_para_code='id',
            interface_para_name='id',
            interface_para_position=1,
            interface_para_type='2',
            interface_data_type='1',
        )

        destroy_view = InterfaceInfoViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/dataservice/interface-info/{interface.id}')
        force_authenticate(request, user=self.user)
        response = destroy_view(request, pk=str(interface.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)

        interface.enable = '0'
        interface.save(update_fields=['enable', 'update_time'])
        request = self.factory.delete(f'/data-api/dataservice/interface-info/{interface.id}')
        force_authenticate(request, user=self.user)
        response = destroy_view(request, pk=str(interface.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        interface.refresh_from_db()
        field.refresh_from_db()
        self.assertEqual(interface.del_flag, '1')
        self.assertEqual(field.del_flag, '1')

    def test_execute_by_id_should_block_offline_interface(self):
        interface = InterfaceInfo.objects.create(
            interface_name='下线接口',
            interface_code='offline_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            interface_datasource=self.data_source.id,
            enable='0',
        )

        view = InterfaceInfoViewSet.as_view({'post': 'execute_by_id'})
        request = self.factory.post(
            f'/data-api/dataservice/interface-info/{interface.id}/execute',
            {'params': {}, 'pageSize': 10, 'offset': 0},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(interface.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], '-1')
        self.assertIn('下线', response.data['message'])

    @patch('apps.dataservice.views.get_executor')
    def test_execute_by_id_should_return_wrapped_paging_result(self, mock_get_executor):
        interface = InterfaceInfo.objects.create(
            interface_name='分页接口',
            interface_code='paged_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select id, name from demo_user',
            total_sql='select sum(score) as total_score from demo_user',
            interface_datasource=self.data_source.id,
            is_paging='1',
            is_total='1',
            enable='1',
            report_name='用户报表',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='id',
            interface_para_name='用户ID',
            interface_para_position=1,
            interface_para_type='2',
            interface_data_type='2',
            interface_para_desc='主键',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='name',
            interface_para_name='用户名',
            interface_para_position=2,
            interface_para_type='2',
            interface_data_type='1',
            interface_para_desc='姓名',
        )
        mock_get_executor.return_value = _MockExecutor([
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice'), (2, 'Bob')]},
            {'columns': ['total_count'], 'rows': [(2,)]},
            {'columns': ['name', 'id'], 'rows': [('汇总', 999)]},
        ])

        view = InterfaceInfoViewSet.as_view({'post': 'execute_by_id'})
        request = self.factory.post(
            f'/data-api/dataservice/interface-info/{interface.id}/execute',
            {'params': {}, 'pageSize': 20, 'offset': 0},
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = view(request, pk=str(interface.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], '0')
        self.assertEqual(response.data['message'], 'success')
        self.assertEqual(response.data['reportName'], '用户报表')
        self.assertEqual(response.data['data']['total'], 2)
        self.assertEqual(response.data['data']['list'][0], {'id': 1, 'name': 'Alice'})
        self.assertEqual(response.data['data']['totalList'][0], {'id': 999, 'name': '汇总'})
        self.assertIn('id', response.data['property'])
        self.assertEqual(response.data['property']['id']['paraName'], '用户ID')

    @patch('apps.dataservice.views.get_executor')
    def test_execute_by_id_should_return_wrapped_non_paging_result(self, mock_get_executor):
        interface = InterfaceInfo.objects.create(
            interface_name='非分页接口',
            interface_code='plain_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select city, amount from demo_city',
            total_sql='select sum(amount) as amount, "总计" as city from demo_city',
            interface_datasource=self.data_source.id,
            is_paging='0',
            is_total='1',
            enable='1',
            report_name='城市报表',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='city',
            interface_para_name='城市',
            interface_para_position=1,
            interface_para_type='2',
            interface_data_type='1',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='amount',
            interface_para_name='金额',
            interface_para_position=2,
            interface_para_type='2',
            interface_data_type='3',
        )
        mock_get_executor.return_value = _MockExecutor([
            {'columns': ['city', 'amount'], 'rows': [('上海', 12.5), ('北京', 8.0)]},
            {'columns': ['amount', 'city'], 'rows': [(20.5, '总计')]},
        ])

        view = InterfaceInfoViewSet.as_view({'post': 'execute_by_id'})
        request = self.factory.post(
            f'/data-api/dataservice/interface-info/{interface.id}/execute',
            {'params': {}, 'pageSize': 20, 'offset': 0},
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = view(request, pk=str(interface.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], '0')
        self.assertEqual(response.data['data'][0], {'city': '上海', 'amount': 12.5})
        self.assertEqual(response.data['totaldata'][0], {'city': '总计', 'amount': 20.5})



class ReportInfoTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='reporter', password='password123')
        admin_role = Role.objects.create(role_name='报表测试管理员', role_key='admin', role_sort=0, status='0')
        UserRole.objects.create(user=self.user, role=admin_role)
        self.interface_a = InterfaceInfo.objects.create(
            interface_name='用户接口',
            interface_code='user_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            enable='1',
        )
        self.interface_b = InterfaceInfo.objects.create(
            interface_name='订单接口',
            interface_code='order_api',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select 1',
            enable='1',
        )

    def test_report_create_should_bind_multiple_interfaces(self):
        view = ReportInfoViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataservice/report-info',
            {
                'reportName': '经营分析报表',
                'reportCode': 'ops_report',
                'reportDesc': '日报表',
                'interfaceIds': [self.interface_a.id, self.interface_b.id],
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        report = ReportInfo.objects.get(report_code='ops_report')
        self.assertEqual(report.user_name, self.user.username)
        relation_ids = list(ReportInterfaceRelation.objects.filter(report=report, del_flag='0').order_by('interface_position').values_list('interface_id', flat=True))
        self.assertEqual(relation_ids, [self.interface_a.id, self.interface_b.id])

    def test_report_retrieve_should_return_interface_list(self):
        report = ReportInfo.objects.create(
            report_name='销售报表',
            report_code='sales_report',
            report_desc='月报',
            user_name='owner_a',
        )
        ReportInterfaceRelation.objects.create(report=report, interface=self.interface_a, interface_position=1)
        ReportInterfaceRelation.objects.create(report=report, interface=self.interface_b, interface_position=2)

        view = ReportInfoViewSet.as_view({'get': 'retrieve'})
        request = self.factory.get(f'/data-api/dataservice/report-info/{report.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(report.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['interfaceCount'], 2)
        self.assertEqual(response.data['data']['interfaces'][0]['interfaceCode'], 'user_api')
        self.assertEqual(response.data['data']['interfaces'][1]['interfaceCode'], 'order_api')

    def test_report_destroy_should_soft_delete_relations(self):
        report = ReportInfo.objects.create(
            report_name='删除报表',
            report_code='delete_report',
        )
        relation = ReportInterfaceRelation.objects.create(report=report, interface=self.interface_a, interface_position=1)

        view = ReportInfoViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/dataservice/report-info/{report.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(report.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        report.refresh_from_db()
        relation.refresh_from_db()
        self.assertEqual(report.del_flag, '1')
        self.assertEqual(relation.del_flag, '1')

    def test_report_update_should_allow_rebinding_after_soft_deleted_history(self):
        report = ReportInfo.objects.create(
            report_name='重复更新报表',
            report_code='repeat_update_report',
            user_name=self.user.username,
        )
        ReportInterfaceRelation.objects.create(report=report, interface=self.interface_a, interface_position=1, del_flag='1')
        ReportInterfaceRelation.objects.create(report=report, interface=self.interface_a, interface_position=1)

        view = ReportInfoViewSet.as_view({'put': 'update'})
        request = self.factory.put(
            f'/data-api/dataservice/report-info/{report.id}',
            {
                'reportId': report.id,
                'reportName': '重复更新报表',
                'reportCode': 'repeat_update_report',
                'reportDesc': '更新后',
                'interfaceIds': [self.interface_a.id],
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(report.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(
            ReportInterfaceRelation.objects.filter(report=report, interface=self.interface_a, del_flag='0').count(),
            1,
        )

    def test_report_destroy_should_clear_stale_deleted_relations_before_soft_delete(self):
        report = ReportInfo.objects.create(
            report_name='重复删除报表',
            report_code='repeat_delete_report',
            user_name=self.user.username,
        )
        stale_relation = ReportInterfaceRelation.objects.create(
            report=report,
            interface=self.interface_a,
            interface_position=1,
            del_flag='1',
        )
        active_relation = ReportInterfaceRelation.objects.create(
            report=report,
            interface=self.interface_a,
            interface_position=1,
        )

        view = ReportInfoViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/dataservice/report-info/{report.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(report.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertFalse(ReportInterfaceRelation.objects.filter(id=stale_relation.id).exists())
        active_relation.refresh_from_db()
        self.assertEqual(active_relation.del_flag, '1')


class FrontendApiIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='frontend_tester', password='password123')
        admin_role = Role.objects.create(role_name='前端管理员', role_key='admin', role_sort=0, status='0')
        UserRole.objects.create(user=self.user, role=admin_role)
        self.client.force_authenticate(user=self.user)
        self.data_source = DataSource.objects.create(
            name='frontend-demo-source',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='demo',
            username='root',
            password=encrypt_password('secret'),
            params='{}',
            status='0',
        )

    def _create_interface(self, interface_code='frontend_keep_api', interface_name='前端保底接口', enable='1', is_paging='1'):
        return InterfaceInfo.objects.create(
            interface_name=interface_name,
            interface_code=interface_code,
            interface_desc='接口说明',
            interface_db_type='mysql',
            interface_db_name='demo',
            interface_sql='select id, name from demo_user',
            interface_datasource=self.data_source.id,
            is_total='0',
            is_paging=is_paging,
            enable=enable,
            user_name=self.user.username,
        )

    def _create_output_fields(self, interface):
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='id',
            interface_para_name='ID',
            interface_para_position=1,
            interface_para_type='2',
            interface_data_type='2',
        )
        InterfaceField.objects.create(
            interface=interface,
            interface_para_code='name',
            interface_para_name='名称',
            interface_para_position=2,
            interface_para_type='2',
            interface_data_type='1',
        )

    @patch('apps.dataservice.views.get_executor')
    def test_frontend_query_endpoints_should_work(self, mock_get_executor):
        mock_get_executor.return_value = _MockExecutor([
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice')]},
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice'), (2, 'Bob')]},
        ])

        query_response = self.client.post(
            '/data-api/dataservice/query',
            {
                'dataSourceId': self.data_source.id,
                'sql': 'select id, name from demo_user where dt = {{ biz_date }}',
                'params': {'biz_date': '2026-04-27'},
                'pageSize': 20,
                'offset': 0,
            },
            format='json',
        )
        export_response = self.client.post(
            '/data-api/dataservice/export',
            {
                'dataSourceId': self.data_source.id,
                'sql': 'select id, name from demo_user',
                'params': {},
                'pageSize': 100,
                'offset': 0,
            },
            format='json',
        )
        log_response = self.client.get('/data-api/dataservice/query-log', {'userName': self.user.username, 'status': 'success'})

        self.assertEqual(query_response.status_code, 200)
        self.assertEqual(query_response.json()['code'], 200)
        self.assertEqual(query_response.json()['data']['rows'][0], [1, 'Alice'])
        self.assertEqual(export_response.status_code, 200)
        self.assertIn('text/csv', export_response['Content-Type'])
        self.assertEqual(log_response.status_code, 200)
        self.assertGreaterEqual(log_response.json()['total'], 2)

    def test_frontend_interface_info_endpoints_should_work(self):
        create_response = self.client.post('/data-api/dataservice/interface-info', _build_interface_payload('frontend_create_api', '前端创建接口'), format='json')
        interface_id = InterfaceInfo.objects.get(interface_code='frontend_create_api').id

        list_response = self.client.get('/data-api/dataservice/interface-info', {'interfaceCode': 'frontend_create_api'})
        retrieve_response = self.client.get(f'/data-api/dataservice/interface-info/{interface_id}')
        update_response = self.client.put(
            f'/data-api/dataservice/interface-info/{interface_id}',
            {
                **_build_interface_payload('frontend_create_api', '前端更新接口', enable='0'),
                'interfaceId': interface_id,
                'interfaceDatasource': self.data_source.id,
            },
            format='json',
        )
        status_response = self.client.put(
            '/data-api/dataservice/interface-info/changeStatus',
            {'interfaceId': interface_id, 'enable': '1'},
            format='json',
        )
        delete_response = self.client.delete(f'/data-api/dataservice/interface-info/{interface_id}')

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(list_response.json()['total'], 1)
        self.assertEqual(retrieve_response.json()['data']['interfaceCode'], 'frontend_create_api')
        self.assertEqual(update_response.json()['code'], 200)
        self.assertEqual(status_response.json()['code'], 200)
        self.assertEqual(delete_response.json()['code'], 400)

        self.client.put(
            '/data-api/dataservice/interface-info/changeStatus',
            {'interfaceId': interface_id, 'enable': '0'},
            format='json',
        )
        delete_retry = self.client.delete(f'/data-api/dataservice/interface-info/{interface_id}')
        self.assertEqual(delete_retry.json()['code'], 200)

    def test_frontend_interface_create_should_reject_duplicate_code(self):
        first_response = self.client.post(
            '/data-api/dataservice/interface-info',
            _build_interface_payload('frontend_duplicate_api', '前端重复接口A'),
            format='json',
        )
        second_response = self.client.post(
            '/data-api/dataservice/interface-info',
            _build_interface_payload('frontend_duplicate_api', '前端重复接口B'),
            format='json',
        )

        self.assertEqual(first_response.json()['code'], 200)
        self.assertEqual(second_response.json()['code'], 400)
        self.assertEqual(InterfaceInfo.objects.filter(interface_code='frontend_duplicate_api', del_flag='0').count(), 1)

    def test_frontend_interface_update_should_reject_duplicate_code(self):
        first_interface = self._create_interface(interface_code='frontend_update_dup_a', interface_name='接口A', enable='0')
        self._create_interface(interface_code='frontend_update_dup_b', interface_name='接口B', enable='0')

        response = self.client.put(
            f'/data-api/dataservice/interface-info/{first_interface.id}',
            {
                **_build_interface_payload('frontend_update_dup_b', '接口A更新', enable='0'),
                'interfaceId': first_interface.id,
                'interfaceDatasource': self.data_source.id,
            },
            format='json',
        )

        self.assertEqual(response.json()['code'], 400)

    @patch('apps.dataservice.views.get_executor')
    def test_frontend_interface_runtime_endpoints_should_work(self, mock_get_executor):
        interface = self._create_interface(interface_code='frontend_runtime_api', interface_name='运行时接口')
        self._create_output_fields(interface)
        mock_get_executor.return_value = _MockExecutor([
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice')]},
            {'columns': ['total_count'], 'rows': [(1,)]},
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice'), (2, 'Bob')]},
            {'columns': ['total_count'], 'rows': [(2,)]},
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice'), (2, 'Bob')]},
            {'columns': ['total_count'], 'rows': [(2,)]},
            {'columns': ['id', 'name'], 'rows': [(1, 'Alice'), (2, 'Bob')]},
        ])

        test_response = self.client.post(
            f'/data-api/dataservice/interface-info/{interface.id}/test',
            {'params': {}, 'pageSize': 10, 'offset': 0},
            format='json',
        )
        execute_response = self.client.post(
            f'/data-api/dataservice/interface-info/{interface.id}/execute',
            {'params': {}, 'pageSize': 20, 'offset': 0},
            format='json',
        )
        export_response = self.client.post(
            f'/data-api/dataservice/interface-info/{interface.id}/export',
            {'params': {}, 'pageSize': 20, 'offset': 0},
            format='json',
        )
        export_body_response = self.client.post(
            '/data-api/dataservice/interface-info/export',
            {
                'dataSourceId': self.data_source.id,
                'sql': 'select id, name from demo_user',
                'params': {},
                'pageSize': 100,
                'offset': 0,
            },
            format='json',
        )
        export_meta_response = self.client.post(f'/data-api/dataservice/interface-info/{interface.id}/export-meta', {}, format='json')

        self.assertEqual(test_response.status_code, 200)
        self.assertEqual(test_response.json()['code'], '0')
        self.assertEqual(execute_response.status_code, 200)
        self.assertEqual(execute_response.json()['code'], '0')
        self.assertIn('text/csv', export_response['Content-Type'])
        self.assertIn('text/csv', export_body_response['Content-Type'])
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', export_meta_response['Content-Type'])

    def test_frontend_interface_field_endpoints_should_work(self):
        interface = self._create_interface(interface_code='frontend_field_api', interface_name='字段接口', enable='0')
        create_response = self.client.post('/data-api/dataservice/interface-field', _build_field_payload(interface.id), format='json')
        field_id = InterfaceField.objects.get(interface=interface, interface_para_code='id', del_flag='0').id

        list_response = self.client.get('/data-api/dataservice/interface-field', {'interfaceId': interface.id})
        retrieve_response = self.client.get(f'/data-api/dataservice/interface-field/{field_id}')
        update_response = self.client.put(
            f'/data-api/dataservice/interface-field/{field_id}',
            {
                **_build_field_payload(interface.id, code='name', position=1),
                'fieldId': field_id,
            },
            format='json',
        )
        delete_response = self.client.delete(f'/data-api/dataservice/interface-field/{field_id}')

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(list_response.json()['total'], 1)
        self.assertEqual(retrieve_response.json()['data']['fieldId'], field_id)
        self.assertEqual(update_response.json()['code'], 200)
        self.assertEqual(delete_response.json()['code'], 200)

    @patch('apps.dataservice.views.parse_interface_workbook')
    @patch('apps.dataservice.views.load_workbook')
    def test_frontend_import_meta_endpoint_should_work(self, mock_load_workbook, mock_parse_interface_workbook):
        mock_load_workbook.return_value = object()
        mock_parse_interface_workbook.return_value = [
            (
                InterfaceInfo(
                    interface_name='导入接口',
                    interface_code='imported_api',
                    interface_desc='导入说明',
                    interface_db_type='mysql',
                    interface_db_name='demo',
                    interface_sql='select 1',
                    is_total='0',
                    total_sql='',
                    is_paging='1',
                    is_date_option='0',
                    is_second_table='0',
                    is_login_visit='0',
                    alarm_type='0',
                    enable='1',
                    user_name=self.user.username,
                    platform_name='平台A',
                    module_name='模块A',
                    report_name='报表A',
                    report_code='report_a',
                ),
                [
                    InterfaceField(
                        interface_para_code='id',
                        interface_para_name='ID',
                        interface_para_position=1,
                        interface_para_type='2',
                        interface_data_type='2',
                    )
                ],
            )
        ]
        upload = SimpleUploadedFile(
            'interface_meta.xlsx',
            b'fake-xlsx-content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post('/data-api/dataservice/interface-info/import-meta', {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 200)
        self.assertTrue(InterfaceInfo.objects.filter(interface_code='imported_api').exists())

    def test_frontend_report_endpoints_should_work(self):
        interface = self._create_interface(interface_code='frontend_report_api', interface_name='报表接口')
        create_response = self.client.post(
            '/data-api/dataservice/report-info',
            {
                'reportName': '前端报表',
                'reportCode': 'frontend_report',
                'reportDesc': '报表说明',
                'interfaceIds': [interface.id],
            },
            format='json',
        )
        report_id = ReportInfo.objects.get(report_code='frontend_report').id

        list_response = self.client.get('/data-api/dataservice/report-info', {'reportCode': 'frontend_report'})
        retrieve_response = self.client.get(f'/data-api/dataservice/report-info/{report_id}')
        update_response = self.client.put(
            f'/data-api/dataservice/report-info/{report_id}',
            {
                'reportId': report_id,
                'reportName': '前端报表更新',
                'reportCode': 'frontend_report',
                'reportDesc': '报表更新说明',
                'interfaceIds': [interface.id],
            },
            format='json',
        )
        delete_response = self.client.delete(f'/data-api/dataservice/report-info/{report_id}')

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(list_response.json()['total'], 1)
        self.assertEqual(retrieve_response.json()['data']['reportCode'], 'frontend_report')
        self.assertEqual(update_response.json()['code'], 200)
        self.assertEqual(delete_response.json()['code'], 200)

    def test_frontend_report_create_should_reject_duplicate_code(self):
        interface = self._create_interface(interface_code='frontend_report_dup_api', interface_name='报表重复接口')
        first_response = self.client.post(
            '/data-api/dataservice/report-info',
            {
                'reportName': '报表A',
                'reportCode': 'frontend_report_duplicate',
                'reportDesc': '说明A',
                'interfaceIds': [interface.id],
            },
            format='json',
        )
        second_response = self.client.post(
            '/data-api/dataservice/report-info',
            {
                'reportName': '报表B',
                'reportCode': 'frontend_report_duplicate',
                'reportDesc': '说明B',
                'interfaceIds': [interface.id],
            },
            format='json',
        )

        self.assertEqual(first_response.json()['code'], 200)
        self.assertEqual(second_response.json()['code'], 400)

    def test_frontend_report_update_should_reject_duplicate_code(self):
        interface = self._create_interface(interface_code='frontend_report_update_api', interface_name='报表更新接口')
        first_report = ReportInfo.objects.create(report_name='报表A', report_code='frontend_report_update_a', user_name=self.user.username)
        second_report = ReportInfo.objects.create(report_name='报表B', report_code='frontend_report_update_b', user_name=self.user.username)
        ReportInterfaceRelation.objects.create(report=first_report, interface=interface, interface_position=1)
        ReportInterfaceRelation.objects.create(report=second_report, interface=interface, interface_position=1)

        response = self.client.put(
            f'/data-api/dataservice/report-info/{first_report.id}',
            {
                'reportId': first_report.id,
                'reportName': '报表A更新',
                'reportCode': 'frontend_report_update_b',
                'reportDesc': '更新说明',
                'interfaceIds': [interface.id],
            },
            format='json',
        )

        self.assertEqual(response.json()['code'], 400)
