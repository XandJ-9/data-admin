from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.common.encrypt import encrypt_password

from .models import DataSource
from .views import DataSourceDiscoveryViewSet, DataSourceViewSet, _sanitize_db_error_message


class _FailingExecutor:
    def __init__(self, error):
        self.error = error
        self.closed = False

    def test_connection(self):
        raise self.error

    def close(self):
        self.closed = True


class _PassingExecutor:
    def __init__(self):
        self.closed = False

    def test_connection(self):
        return None

    def close(self):
        self.closed = True


class DataSourceSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')

    def test_sanitize_db_error_message_should_hide_driver_details(self):
        message = _sanitize_db_error_message(RuntimeError("Access denied for user 'root'@'127.0.0.1'"))

        self.assertEqual(message, '连接失败：认证失败，请检查用户名和密码')

    @patch('apps.datasource.views.get_executor')
    def test_test_by_body_should_return_sanitized_error_message(self, mock_get_executor):
        mock_get_executor.return_value = _FailingExecutor(
            RuntimeError("Access denied for user 'root'@'127.0.0.1' (using password: YES)")
        )
        view = DataSourceViewSet.as_view({'post': 'test_by_body'})
        request = self.factory.post(
            '/data-api/datasource/datasource/test',
            {
                'dataSourceName': 'test-source',
                'dbType': 'mysql',
                'host': '127.0.0.1',
                'port': 3306,
                'dbName': 'demo',
                'username': 'root',
                'password': 'secret',
                'params': '{}',
                'status': '0',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['msg'], '连接失败：认证失败，请检查用户名和密码')
        self.assertNotIn('Access denied', response.data['msg'])


class DataSourceConnectivityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')

    def create_datasource(self, **overrides):
        payload = {
            'name': 'demo-source',
            'db_type': 'mysql',
            'host': '127.0.0.1',
            'port': 3306,
            'db_name': 'demo',
            'username': 'root',
            'password': encrypt_password('secret'),
            'params': '{}',
            'status': '0',
        }
        payload.update(overrides)
        return DataSource.objects.create(**payload)

    @patch('apps.datasource.views.get_executor')
    def test_test_by_id_should_persist_connectivity_status(self, mock_get_executor):
        mock_get_executor.return_value = _PassingExecutor()
        datasource = self.create_datasource()
        view = DataSourceViewSet.as_view({'post': 'test_by_id'})
        request = self.factory.post(f'/data-api/datasource/datasource/{datasource.id}/test', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(datasource.id))

        datasource.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(datasource.connectivity_status, 'success')
        self.assertEqual(datasource.connectivity_message, '连接成功')
        self.assertIsNotNone(datasource.connectivity_tested_at)

    def test_update_should_reset_connectivity_status_when_connection_changes(self):
        tested_at = timezone.now()
        datasource = self.create_datasource(
            connectivity_status='success',
            connectivity_message='连接成功',
            connectivity_tested_at=tested_at,
        )
        view = DataSourceViewSet.as_view({'put': 'update'})
        request = self.factory.put(
            f'/data-api/datasource/datasource/{datasource.id}',
            {
                'dataSourceId': datasource.id,
                'dataSourceName': datasource.name,
                'dbType': datasource.db_type,
                'host': '192.168.1.10',
                'port': datasource.port,
                'dbName': datasource.db_name,
                'username': datasource.username,
                'password': '',
                'params': datasource.params,
                'status': datasource.status,
                'remark': datasource.remark,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(datasource.id))

        datasource.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(datasource.host, '192.168.1.10')
        self.assertEqual(datasource.connectivity_status, 'unknown')
        self.assertEqual(datasource.connectivity_message, '')
        self.assertIsNone(datasource.connectivity_tested_at)


class DataSourceDiscoveryTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')
        self.data_source = DataSource.objects.create(
            name='sqlite-demo',
            db_type='sqlite',
            db_name='/tmp/demo.sqlite3',
            status='0',
        )

    @patch('apps.datasource.views.discover_databases')
    def test_databases_should_return_fallback_rows(self, mock_discover_databases):
        mock_discover_databases.return_value = ['/tmp/demo.sqlite3']
        view = DataSourceDiscoveryViewSet.as_view({'post': 'databases'})
        request = self.factory.post('/data-api/datasource/collection/databases', {'dataSourceId': self.data_source.id}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data'], ['/tmp/demo.sqlite3'])

    @patch('apps.datasource.views.discover_tables')
    def test_tables_should_return_normalized_table_rows(self, mock_discover_tables):
        mock_discover_tables.return_value = [
            {
                'tableName': 'orders',
                'databaseName': 'demo',
                'tableType': 'BASE TABLE',
                'tableComment': '订单表',
                'comment': '订单表',
                'createTime': '',
                'updateTime': '',
            }
        ]
        view = DataSourceDiscoveryViewSet.as_view({'post': 'tables'})
        request = self.factory.post(
            '/data-api/datasource/collection/tables',
            {'dataSourceId': self.data_source.id, 'databaseName': 'demo'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['tableComment'], '订单表')
        self.assertEqual(response.data['rows'][0]['tableType'], 'BASE TABLE')

