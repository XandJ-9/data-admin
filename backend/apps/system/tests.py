from django.contrib.auth import get_user_model
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.core.cache import cache
from captcha.models import CaptchaStore
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Menu, Role, RoleMenu, UserRole
from .views.core import GetInfoView, LoginView


class GetInfoViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='common_user', password='password123')
        self.role = Role.objects.create(
            role_name='普通角色',
            role_key='common',
            role_sort=2,
            status='0',
            create_by='tester',
        )
        self.query_menu = Menu.objects.create(
            menu_name='任务查询',
            order_num=1,
            menu_type='F',
            perms='datatask:task:list',
            status='0',
            create_by='tester',
        )
        self.view_menu = Menu.objects.create(
            menu_name='集成查看',
            order_num=2,
            menu_type='F',
            perms='dataintegration:task:view',
            status='0',
            create_by='tester',
        )
        self.blank_menu = Menu.objects.create(
            menu_name='空权限',
            order_num=3,
            menu_type='C',
            perms='',
            status='0',
            create_by='tester',
        )
        UserRole.objects.create(user=self.user, role=self.role, create_by='tester')
        RoleMenu.objects.create(role=self.role, menu=self.query_menu, create_by='tester')
        RoleMenu.objects.create(role=self.role, menu=self.view_menu, create_by='tester')
        RoleMenu.objects.create(role=self.role, menu=self.blank_menu, create_by='tester')

    def test_get_info_should_return_role_permissions(self):
        view = GetInfoView.as_view()
        request = self.factory.get('/system/getInfo')
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['roles'], ['common'])
        self.assertEqual(
            response.data['permissions'],
            ['dataintegration:task:view', 'datatask:task:list'],
        )


class LoginViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.view = LoginView.as_view()
        self.user = get_user_model().objects.create_user(username='tester', password='Password123!')

    def _captcha_pair(self):
        hashkey = CaptchaStore.generate_key()
        captcha = CaptchaStore.objects.get(hashkey=hashkey)
        return hashkey, captcha.response

    def test_login_success_returns_token(self):
        uuid, code = self._captcha_pair()
        request = self.factory.post(
            '/system/login',
            {
                'username': 'tester',
                'password': 'Password123!',
                'uuid': uuid,
                'code': code,
            },
            format='json',
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('code'), 200)
        self.assertTrue(response.data.get('token'))
        self.assertTrue(response.data.get('refreshToken'))

    def test_login_with_invalid_captcha_should_fail(self):
        uuid, _ = self._captcha_pair()
        request = self.factory.post(
            '/system/login',
            {
                'username': 'tester',
                'password': 'Password123!',
                'uuid': uuid,
                'code': 'wrong-code',
            },
            format='json',
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('code'), 400)
        self.assertIn('验证码', response.data.get('msg', ''))

    def test_login_failures_should_trigger_rate_limit(self):
        for _ in range(LoginView.LOGIN_FAIL_LIMIT):
            uuid, code = self._captcha_pair()
            request = self.factory.post(
                '/system/login',
                {
                    'username': 'tester',
                    'password': 'wrong-password',
                    'uuid': uuid,
                    'code': code,
                },
                format='json',
            )
            response = self.view(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.get('code'), 400)

        uuid, code = self._captcha_pair()
        request = self.factory.post(
            '/system/login',
            {
                'username': 'tester',
                'password': 'Password123!',
                'uuid': uuid,
                'code': code,
            },
            format='json',
        )
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('code'), 429)


class InitDataMenuTests(TestCase):
    def test_initdata_should_enable_data_asset_and_data_service_roots(self):
        call_command('initdata', force=True, stdout=StringIO())

        self.assertTrue(Menu.objects.filter(path='/data-asset', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(path='/data-service', del_flag='0').exists())
        self.assertFalse(Menu.objects.filter(path='/datadev', del_flag='0').exists())
        self.assertFalse(Menu.objects.filter(path='/datatask', del_flag='0').exists())
