from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.common.encrypt import encrypt_password
from apps.datasource.models import DataSource

from .models import InterfaceField, InterfaceInfo, ReportInfo, ReportInterfaceRelation
from .serializers import InterfaceInfoCreateSerializer
from .views import InterfaceInfoViewSet, ReportInfoViewSet


class _MockExecutor:
    def __init__(self, responses):
        self.responses = list(responses)

    def execute_query(self, sql, params=None, page_size=None, offset=None):
        if not self.responses:
            raise AssertionError('No mocked executor response left')
        return self.responses.pop(0)

    def close(self):
        return None


class InterfacePublishTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')
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

    def test_publish_from_query_should_create_interface_and_fields(self):
        view = InterfaceInfoViewSet.as_view({'post': 'publish_from_query'})
        request = self.factory.post(
            '/data-api/dataservice/interface-info/publish',
            {
                'dataSourceId': self.data_source.id,
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
