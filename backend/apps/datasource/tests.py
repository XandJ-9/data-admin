from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .views import DataSourceViewSet, _sanitize_db_error_message


class _FailingExecutor:
    def __init__(self, error):
        self.error = error
        self.closed = False

    def test_connection(self):
        raise self.error

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
            '/data-api/datasource/test',
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