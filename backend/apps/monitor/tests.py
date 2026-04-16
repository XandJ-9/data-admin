import json

from django.http import HttpResponse
from django.test import SimpleTestCase
from rest_framework.response import Response

from .middleware import _build_response_snapshot, _deep_mask


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