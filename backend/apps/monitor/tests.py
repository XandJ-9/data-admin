import json

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import SimpleTestCase, TestCase
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from .middleware import _build_response_snapshot, _deep_mask
from .views import ServerView, _collect_monitor_value, _empty_cpu_info


class MonitorMiddlewareTests(SimpleTestCase):
    def test_deep_mask_should_mask_nested_sensitive_fields(self):
        payload = {
            'data': {
                'accessToken': 'secret-token',
                'profile': {
                    'refresh_token': 'refresh-secret',
                    'password': 'plain-password',
                },
                'items': [
                    {'authorization': 'Bearer x'},
                    {'name': 'safe'},
                ],
            }
        }

        masked = _deep_mask(payload)

        self.assertEqual(masked['data']['accessToken'], '****')
        self.assertEqual(masked['data']['profile']['refresh_token'], '****')
        self.assertEqual(masked['data']['profile']['password'], '****')
        self.assertEqual(masked['data']['items'][0]['authorization'], '****')

    def test_build_response_snapshot_should_not_log_sensitive_response_values(self):
        response = Response({
            'code': 200,
            'msg': '登录成功',
            'data': {
                'accessToken': 'secret-token',
                'user': {'name': 'admin'},
            },
        })

        status_val, json_result = _build_response_snapshot(response, '')
        snapshot = json.loads(json_result)

        self.assertEqual(status_val, 0)
        self.assertNotIn('secret-token', json_result)
        self.assertEqual(snapshot['response']['code'], 200)
        self.assertEqual(snapshot['response']['dataType'], 'dict')
        self.assertIn('accessToken', snapshot['response']['dataKeys'])

    def test_build_response_snapshot_should_omit_non_json_body(self):
        response = HttpResponse('<html>token=secret</html>', status=200)

        _, json_result = _build_response_snapshot(response, '')

        self.assertNotIn('secret', json_result)
        self.assertIn('<omitted non-json body>', json_result)


class MonitorViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='monitor_tester', password='password123')

    def test_collect_monitor_value_should_return_warning_and_fallback(self):
        fallback = _empty_cpu_info()

        value, warning = _collect_monitor_value(
            'cpu',
            lambda: (_ for _ in ()).throw(RuntimeError('probe failed')),
            fallback,
        )

        self.assertEqual(value, fallback)
        self.assertEqual(warning['scope'], 'cpu')
        self.assertIn('CPU 指标采集失败', warning['message'])

    @patch('apps.monitor.views._get_sys_files', return_value=[])
    @patch('apps.monitor.views._get_local_ip', return_value='127.0.0.1')
    @patch('apps.monitor.views._get_mem_info', return_value={'total': 1.0, 'used': 0.5, 'free': 0.5, 'usage': 50.0, 'available': True})
    @patch('apps.monitor.views._get_cpu_info', side_effect=RuntimeError('cpu probe failed'))
    def test_server_view_should_include_warnings_when_probe_fails(self, _cpu_mock, _mem_mock, _ip_mock, _sys_files_mock):
        view = ServerView.as_view({'get': 'get'})
        request = self.factory.get('/data-api/monitor/server')
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertFalse(response.data['data']['cpu']['available'])
        self.assertEqual(len(response.data['data']['warnings']), 1)
        self.assertEqual(response.data['data']['warnings'][0]['scope'], 'cpu')