from django.contrib.auth import get_user_model
from io import StringIO
from types import SimpleNamespace
from django.core.management import call_command
from django.test import TestCase
from django.core.cache import cache
from captcha.models import CaptchaStore
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from .models import Menu, Role, RoleMenu, UserRole
from .permission import HasRolePermission
from .views.core import BaseViewSet, GetInfoView, LoginView


class WritableRoleSerializer(serializers.ModelSerializer):
    roleId = serializers.IntegerField(source='role_id', required=False)
    roleName = serializers.CharField(source='role_name')
    roleKey = serializers.CharField(source='role_key')
    roleSort = serializers.IntegerField(source='role_sort')

    class Meta:
        model = Role
        fields = ['roleId', 'roleName', 'roleKey', 'roleSort']


class BaseViewSetCreateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='base_view_tester', password='password123')

    def test_perform_create_should_not_update_existing_record_by_default(self):
        role = Role.objects.create(
            role_name='原角色',
            role_key='base_view_create_role',
            role_sort=1,
            create_by='tester',
        )
        serializer = WritableRoleSerializer(data={
            'roleId': role.role_id,
            'roleName': '被误传新增修改的角色',
            'roleKey': 'base_view_create_role_changed',
            'roleSort': 9,
        })
        serializer.is_valid(raise_exception=True)

        view = BaseViewSet()
        view.request = self.factory.post('/system/role', {})
        view.request.user = self.user

        with self.assertRaises(ValidationError):
            view.perform_create(serializer)

        role.refresh_from_db()
        self.assertEqual(role.role_name, '原角色')
        self.assertEqual(role.role_key, 'base_view_create_role')
        self.assertEqual(role.role_sort, 1)

    def test_perform_create_should_reuse_existing_record_when_enabled(self):
        role = Role.objects.create(
            role_name='原角色',
            role_key='base_view_reuse_role',
            role_sort=1,
            create_by='tester',
        )
        serializer = WritableRoleSerializer(data={
            'roleId': role.role_id,
            'roleName': '显式复用后角色',
            'roleKey': 'base_view_reuse_role_changed',
            'roleSort': 8,
        })
        serializer.is_valid(raise_exception=True)

        view = BaseViewSet()
        view.create_reuse_existing = True
        view.request = self.factory.post('/system/role', {})
        view.request.user = self.user

        view.perform_create(serializer)

        role.refresh_from_db()
        self.assertEqual(role.role_name, '显式复用后角色')
        self.assertEqual(role.role_key, 'base_view_reuse_role_changed')
        self.assertEqual(role.role_sort, 8)


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


class HasRolePermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = HasRolePermission()
        self.user = get_user_model().objects.create_user(username='perm_user', password='password123')
        self.role = Role.objects.create(
            role_name='任务角色',
            role_key='task_operator',
            role_sort=1,
            status='0',
            create_by='tester',
        )
        UserRole.objects.create(user=self.user, role=self.role, create_by='tester')

    def test_should_allow_action_when_role_has_menu_permission(self):
        menu = Menu.objects.create(
            menu_name='任务执行',
            order_num=1,
            menu_type='F',
            perms='datatask:task:execute',
            status='0',
            create_by='tester',
        )
        RoleMenu.objects.create(role=self.role, menu=menu, create_by='tester')
        request = self.factory.post('/data-api/datatask/task/1/execute')
        request.user = self.user
        view = SimpleNamespace(action='execute_task', permission_map={'execute_task': 'datatask:task:execute'})

        self.assertTrue(self.permission.has_permission(request, view))

    def test_should_deny_action_when_role_lacks_menu_permission(self):
        request = self.factory.post('/data-api/datatask/task/1/execute')
        request.user = self.user
        view = SimpleNamespace(action='execute_task', permission_map={'execute_task': 'datatask:task:execute'})

        self.assertFalse(self.permission.has_permission(request, view))

    def test_admin_role_should_bypass_menu_permission(self):
        admin_role = Role.objects.create(
            role_name='管理员',
            role_key='admin',
            role_sort=0,
            status='0',
            create_by='tester',
        )
        admin_user = get_user_model().objects.create_user(username='admin_perm_user', password='password123')
        UserRole.objects.create(user=admin_user, role=admin_role, create_by='tester')
        request = self.factory.post('/data-api/datatask/task/1/execute')
        request.user = admin_user
        view = SimpleNamespace(action='execute_task', permission_map={'execute_task': 'datatask:task:execute'})

        self.assertTrue(self.permission.has_permission(request, view))


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
    def test_initdata_should_keep_current_business_roots_and_disable_legacy_orchestration_root(self):
        with patch.dict('os.environ', {
            'DATA_ADMIN_ADMIN_PASSWORD': 'admin-test-password',
            'DATA_ADMIN_USER_PASSWORD': 'user-test-password',
        }):
            call_command('initdata', force=True, stdout=StringIO())

        self.assertTrue(Menu.objects.filter(path='/data-asset', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(path='/data-service', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(path='/datadev', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(path='/datatask', del_flag='0').exists())
        self.assertFalse(Menu.objects.filter(path='/data-orchestration', del_flag='0').exists())

    def test_initdata_should_split_data_integration_home_and_task_menu(self):
        with patch.dict('os.environ', {
            'DATA_ADMIN_ADMIN_PASSWORD': 'admin-test-password',
            'DATA_ADMIN_USER_PASSWORD': 'user-test-password',
        }):
            call_command('initdata', force=True, stdout=StringIO())

        data_integration_root = Menu.objects.get(path='/data-integration', del_flag='0')
        self.assertEqual(data_integration_root.redirect, '/data-integration/home')
        self.assertTrue(Menu.objects.filter(parent_id=data_integration_root.menu_id, path='home', route_name='DataIntegrationHome', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(parent_id=data_integration_root.menu_id, path='task', route_name='DataIntegrationTask', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(path='task/create', route_name='DataIntegrationTaskCreate', active_menu='/data-integration/task', del_flag='0').exists())
        self.assertTrue(Menu.objects.filter(path='task/:taskId(\\d+)', route_name='DataIntegrationTaskDetail', active_menu='/data-integration/task', del_flag='0').exists())
