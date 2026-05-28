"""
初始化菜单、角色、用户数据的管理命令。
用法: python manage.py initdata
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.system.management.commands.sync_menu_data import MENU_DATA_FILE, flatten_menu_tree
from apps.system.models import Menu, Role, RoleMenu, User, UserRole, Dept

try:
    from apps.datadev.models import DataDevDirectory
except ModuleNotFoundError:
    DataDevDirectory = None


DISABLED_MENU_ROOT_PATHS = {
    '/data-orchestration'
}


class Command(BaseCommand):
    help = '初始化系统菜单、角色、用户数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新初始化（清除已有菜单/角色数据后重建）',
        )

    def handle(self, *args, **options):
        force = options['force']
        admin_password = os.environ.get('DATA_ADMIN_ADMIN_PASSWORD', 'admin123')
        normal_password = os.environ.get('DATA_ADMIN_USER_PASSWORD', 'user123')

        if not settings.DEBUG:
            if not os.environ.get('DATA_ADMIN_ADMIN_PASSWORD'):
                raise CommandError('DATA_ADMIN_ADMIN_PASSWORD must be set when DJANGO_DEBUG=false')
            if not os.environ.get('DATA_ADMIN_USER_PASSWORD'):
                raise CommandError('DATA_ADMIN_USER_PASSWORD must be set when DJANGO_DEBUG=false')

        if force:
            self.stdout.write(self.style.WARNING('强制模式：将清除已有菜单、角色数据后重建'))

        with transaction.atomic():
            self._init_dept(force)
            self._init_menus(force)
            self._init_datadev_directories(force)
            self._init_roles(force)
            self._init_users(force, admin_password=admin_password, normal_password=normal_password)

        self.stdout.write(self.style.SUCCESS('初始化完成！'))
        self.stdout.write('  管理员账号: admin')
        self.stdout.write('  普通用户: user')

    # ------------------------------------------------------------------ 部门
    def _init_dept(self, force):
        if force:
            Dept.objects.all().delete()

        if Dept.objects.filter(del_flag='0').exists():
            self.stdout.write('部门数据已存在，跳过')
            return

        Dept.objects.create(dept_id=100, parent_id=0, ancestors='0', dept_name='数据管理中心', order_num=0, leader='admin', status='0', create_by='system')
        Dept.objects.create(dept_id=101, parent_id=100, ancestors='0,100', dept_name='技术部', order_num=1, leader='', status='0', create_by='system')
        Dept.objects.create(dept_id=102, parent_id=100, ancestors='0,100', dept_name='数据部', order_num=2, leader='', status='0', create_by='system')
        self.stdout.write(self.style.SUCCESS('部门初始化完成'))

    # ------------------------------------------------------------------ 菜单
    def _init_menus(self, force):
        if force:
            RoleMenu.objects.all().delete()
            Menu.objects.all().delete()

        with open(MENU_DATA_FILE, 'r', encoding='utf-8') as f:
            menu_tree = self._filter_enabled_menu_tree(json.load(f))

        menus = flatten_menu_tree(menu_tree, parent_id=0)
        pending_menu_ids = list(
            Menu.objects.filter(del_flag='0', path__in=DISABLED_MENU_ROOT_PATHS).values_list('menu_id', flat=True)
        )
        stale_menu_ids = set(pending_menu_ids)
        while pending_menu_ids:
            child_ids = list(
                Menu.objects.filter(parent_id__in=pending_menu_ids, del_flag='0').values_list('menu_id', flat=True)
            )
            pending_menu_ids = [item for item in child_ids if item not in stale_menu_ids]
            stale_menu_ids.update(pending_menu_ids)

        if stale_menu_ids:
            RoleMenu.objects.filter(menu_id__in=stale_menu_ids).delete()
            Menu.objects.filter(menu_id__in=stale_menu_ids).update(del_flag='1', update_by='system')

        created_count = 0
        updated_count = 0
        for m in menus:
            menu_defaults = {**m, 'del_flag': '0', 'update_by': 'system'}
            _, created = Menu.objects.update_or_create(
                menu_id=m['menu_id'],
                defaults=menu_defaults,
                create_defaults={**menu_defaults, 'create_by': 'system'},
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'菜单初始化完成：新增 {created_count} 条，更新 {updated_count} 条'
            )
        )

    def _filter_enabled_menu_tree(self, nodes):
        filtered_nodes = []
        for node in nodes:
            if node.get('path') in DISABLED_MENU_ROOT_PATHS:
                continue
            normalized_node = dict(node)
            children = normalized_node.get('children', []) or []
            if children:
                normalized_node['children'] = self._filter_enabled_menu_tree(children)
            filtered_nodes.append(normalized_node)
        return filtered_nodes

    # ---------------------------------------------------------- 数据开发目录
    def _init_datadev_directories(self, force):
        if DataDevDirectory is None:
            self.stdout.write('数据开发模块未启用，跳过默认目录初始化')
            return
        default_directories = [
            {
                'directory_name': 'ODS 贴源层',
                'directory_code': 'ODS',
                'order_num': 1,
                'remark': '默认初始化的数据贴源层目录',
            },
            {
                'directory_name': 'DWD 明细层',
                'directory_code': 'DWD',
                'order_num': 2,
                'remark': '默认初始化的数据明细层目录',
            },
            {
                'directory_name': 'DWS 汇总层',
                'directory_code': 'DWS',
                'order_num': 3,
                'remark': '默认初始化的数据汇总层目录',
            },
            {
                'directory_name': 'ADS 应用层',
                'directory_code': 'ADS',
                'order_num': 4,
                'remark': '默认初始化的数据应用层目录',
            },
        ]

        default_codes = {item['directory_code'] for item in default_directories}
        existing_codes = set(
            DataDevDirectory.objects.filter(directory_code__in=default_codes, del_flag='0')
            .values_list('directory_code', flat=True)
        )

        if existing_codes == default_codes and not force:
            self.stdout.write('数据开发目录已存在，跳过')
            return

        initialized_count = 0
        for item in default_directories:
            defaults = {
                'parent_id': DataDevDirectory.ROOT_PARENT_ID,
                'status': '0',
                'remark': item['remark'],
                'directory_name': item['directory_name'],
                'order_num': item['order_num'],
                'del_flag': '0',
                'create_by': 'system',
                'update_by': 'system',
            }
            DataDevDirectory.objects.update_or_create(
                directory_code=item['directory_code'],
                defaults=defaults,
            )
            initialized_count += 1

        self.stdout.write(self.style.SUCCESS(f'数据开发目录初始化完成，共 {initialized_count} 条'))

    # ------------------------------------------------------------------ 角色
    def _init_roles(self, force):
        if force:
            UserRole.objects.all().delete()
            RoleMenu.objects.all().delete()
            Role.objects.all().delete()

        # 超级管理员角色
        admin_role, _ = Role.objects.update_or_create(
            role_key='admin',
            defaults={
                'role_name': '超级管理员',
                'role_sort': 1,
                'data_scope': '1',
                'status': '0',
                'remark': '超级管理员，拥有所有权限',
                'del_flag': '0',
                'update_by': 'system',
            },
            create_defaults={
                'role_name': '超级管理员',
                'role_sort': 1,
                'data_scope': '1',
                'status': '0',
                'remark': '超级管理员，拥有所有权限',
                'del_flag': '0',
                'create_by': 'system',
                'update_by': 'system',
            },
        )

        # 普通角色
        common_role, _ = Role.objects.update_or_create(
            role_key='common',
            defaults={
                'role_name': '普通角色',
                'role_sort': 2,
                'data_scope': '5',
                'status': '0',
                'remark': '普通角色，拥有数据查询等基本权限',
                'del_flag': '0',
                'update_by': 'system',
            },
            create_defaults={
                'role_name': '普通角色',
                'role_sort': 2,
                'data_scope': '5',
                'status': '0',
                'remark': '普通角色，拥有数据查询等基本权限',
                'del_flag': '0',
                'create_by': 'system',
                'update_by': 'system',
            },
        )

        # 为管理员角色分配所有菜单
        active_menus = list(Menu.objects.filter(del_flag='0'))
        admin_grants = 0
        for menu in active_menus:
            if self._ensure_role_menu(role=admin_role, menu=menu):
                admin_grants += 1

        # 为普通角色分配部分菜单（数据资产、任务运维、数据集成、数据服务的目录/页面 + 查询按钮）
        # 找到业务模块的顶级目录 ID
        biz_paths = {'/datasource', '/data-integration'}
        menu_by_id = {menu.menu_id: menu for menu in active_menus}
        biz_root_ids = {
            menu.menu_id for menu in active_menus
            if menu.parent_id == 0 and menu.path in biz_paths
        }
        # 选取：目录(M)/页面(C) 或 perms 以 :query/:view 结尾的按钮(F)
        common_menu_ids = set()
        for m in active_menus:
            # 属于业务顶级目录本身
            if m.menu_id in biz_root_ids:
                common_menu_ids.add(m.menu_id)
            # 父节点是业务顶级目录（二级菜单）
            elif m.parent_id in biz_root_ids:
                if m.menu_type in ('M', 'C'):
                    common_menu_ids.add(m.menu_id)
            # 父节点的父节点追溯到业务顶级目录（三级按钮）
            else:
                parent = menu_by_id.get(m.parent_id)
                if parent and parent.parent_id in biz_root_ids and m.menu_type == 'F':
                    if m.perms.endswith(':query') or m.perms.endswith(':view'):
                        common_menu_ids.add(m.menu_id)

        common_menus = Menu.objects.filter(menu_id__in=common_menu_ids, del_flag='0')
        common_grants = 0
        for menu in common_menus:
            if self._ensure_role_menu(role=common_role, menu=menu):
                common_grants += 1

        self.stdout.write(self.style.SUCCESS(
            f'角色初始化完成：管理员新增授权 {admin_grants} 条，普通角色新增授权 {common_grants} 条'
        ))

    # ------------------------------------------------------------------ 用户
    def _init_users(self, force, *, admin_password: str, normal_password: str):
        if force:
            UserRole.objects.all().delete()
            User.objects.filter(username__in=['admin', 'user']).delete()

        # 管理员
        admin_user = User.objects.filter(username='admin').first()
        if admin_user is None:
            admin_user = User.objects.create_user(
                username='admin',
                password=admin_password,
                nick_name='管理员',
                sex='0',
                status='0',
                dept_id=100,
                remark='系统管理员',
                is_superuser=True,
                is_staff=True,
            )
            admin_user.create_by = 'system'
            admin_user.save(update_fields=['create_by'])
            self.stdout.write(self.style.SUCCESS('管理员用户 admin 创建成功'))
        else:
            self._restore_builtin_user(
                user=admin_user,
                nick_name='管理员',
                dept_id=100,
                remark='系统管理员',
                is_superuser=True,
                is_staff=True,
            )
            self.stdout.write('管理员用户 admin 已存在，补齐角色关系')

        admin_role = Role.objects.filter(role_key='admin', del_flag='0').first()
        if admin_role:
            self._ensure_user_role(user=admin_user, role=admin_role)

        # 普通用户
        normal_user = User.objects.filter(username='user').first()
        if normal_user is None:
            normal_user = User.objects.create_user(
                username='user',
                password=normal_password,
                nick_name='普通用户',
                sex='0',
                status='0',
                dept_id=101,
                remark='普通用户',
                is_superuser=False,
                is_staff=False,
            )
            normal_user.create_by = 'system'
            normal_user.save(update_fields=['create_by'])
            self.stdout.write(self.style.SUCCESS('普通用户 user 创建成功'))
        else:
            self._restore_builtin_user(
                user=normal_user,
                nick_name='普通用户',
                dept_id=101,
                remark='普通用户',
                is_superuser=False,
                is_staff=False,
            )
            self.stdout.write('普通用户 user 已存在，补齐角色关系')

        common_role = Role.objects.filter(role_key='common', del_flag='0').first()
        if common_role:
            self._ensure_user_role(user=normal_user, role=common_role)

    def _ensure_role_menu(self, *, role, menu):
        relation = RoleMenu.objects.filter(role=role, menu=menu).first()
        if relation is None:
            RoleMenu.objects.create(role=role, menu=menu, create_by='system')
            return True
        if relation.del_flag != '0':
            relation.del_flag = '0'
            relation.update_by = 'system'
            relation.save(update_fields=['del_flag', 'update_by'])
            return True
        return False

    def _ensure_user_role(self, *, user, role):
        relation = UserRole.objects.filter(user=user, role=role).first()
        if relation is None:
            UserRole.objects.create(user=user, role=role, create_by='system')
            return True
        if relation.del_flag != '0':
            relation.del_flag = '0'
            relation.update_by = 'system'
            relation.save(update_fields=['del_flag', 'update_by'])
            return True
        return False

    def _restore_builtin_user(self, *, user, nick_name, dept_id, remark, is_superuser, is_staff):
        update_fields = []
        resolved_dept_id = dept_id if Dept.objects.filter(dept_id=dept_id, del_flag='0').exists() else user.dept_id
        expected_values = {
            'nick_name': nick_name,
            'sex': '0',
            'status': '0',
            'dept_id': resolved_dept_id,
            'remark': remark,
            'is_superuser': is_superuser,
            'is_staff': is_staff,
            'is_active': True,
            'del_flag': '0',
            'update_by': 'system',
        }
        for field_name, expected_value in expected_values.items():
            if getattr(user, field_name) != expected_value:
                setattr(user, field_name, expected_value)
                update_fields.append(field_name)
        if update_fields:
            user.save(update_fields=update_fields)
