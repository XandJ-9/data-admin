from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Menu, Role, RoleMenu, UserRole
from .views.core import GetInfoView


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
