"""
初始化菜单、角色、用户数据的管理命令。
用法: python manage.py initdata
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.models import Menu, Role, RoleMenu, User, UserRole, Dept

# 菜单数据 JSON 文件路径（与本脚本同目录）
MENU_DATA_FILE = Path(__file__).resolve().parent / 'menu_data.json'


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

        if force:
            self.stdout.write(self.style.WARNING('强制模式：将清除已有菜单、角色数据后重建'))

        with transaction.atomic():
            self._init_dept(force)
            self._init_menus(force)
            self._init_roles(force)
            self._init_users(force)

        self.stdout.write(self.style.SUCCESS('初始化完成！'))
        self.stdout.write(f'  管理员账号: admin / admin123')
        self.stdout.write(f'  普通用户: user / user123')

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

        if Menu.objects.filter(del_flag='0').exists():
            self.stdout.write('菜单数据已存在，跳过')
            return

        with open(MENU_DATA_FILE, 'r', encoding='utf-8') as f:
            menu_tree = json.load(f)

        menus = self._flatten_menu_tree(menu_tree, parent_id=0)
        for m in menus:
            Menu.objects.create(**m, create_by='system')

        self.stdout.write(self.style.SUCCESS(f'菜单初始化完成，共 {len(menus)} 条'))

    def _flatten_menu_tree(self, nodes, parent_id=0):
        """
        递归展开树形菜单 JSON 为扁平列表。
        自动生成 menu_id：顶级节点 = orderNum，子节点 = parent_id * 100 + orderNum。
        """
        result = []
        for node in nodes:
            children = node.pop('children', None) or []
            order_num = node.get('orderNum', 0)
            menu_id = order_num if parent_id == 0 else parent_id * 100 + order_num
            menu = {
                'menu_id': menu_id,
                'parent_id': parent_id,
                'menu_name': node['menuName'],
                'order_num': order_num,
                'path': node.get('path', ''),
                'component': node.get('component', ''),
                'route_name': node.get('routeName', ''),
                'menu_type': node.get('menuType', 'M'),
                'visible': node.get('visible', '0'),
                'status': node.get('status', '0'),
                'perms': node.get('perms', ''),
                'icon': node.get('icon', ''),
            }
            result.append(menu)
            if children:
                result.extend(self._flatten_menu_tree(children, parent_id=menu_id))
        return result

    # ------------------------------------------------------------------ 角色
    def _init_roles(self, force):
        if force:
            UserRole.objects.all().delete()
            RoleMenu.objects.all().delete()
            Role.objects.all().delete()

        if Role.objects.filter(del_flag='0').exists():
            self.stdout.write('角色数据已存在，跳过')
            return

        # 超级管理员角色
        admin_role = Role.objects.create(
            role_id=1,
            role_name='超级管理员',
            role_key='admin',
            role_sort=1,
            data_scope='1',
            status='0',
            remark='超级管理员，拥有所有权限',
            create_by='system',
        )

        # 普通角色
        common_role = Role.objects.create(
            role_id=2,
            role_name='普通角色',
            role_key='common',
            role_sort=2,
            data_scope='5',
            status='0',
            remark='普通角色，拥有数据查询等基本权限',
            create_by='system',
        )

        # 为管理员角色分配所有菜单
        all_menus = Menu.objects.filter(del_flag='0')
        RoleMenu.objects.bulk_create([
            RoleMenu(role=admin_role, menu=m, create_by='system') for m in all_menus
        ])

        # 为普通角色分配部分菜单（数据资产、数据服务、数据ETL 的目录/页面 + 查询按钮）
        # 找到业务模块的顶级目录 ID
        biz_paths = {'/data-asset', '/data-etl', '/data-service'}
        biz_root_ids = set(
            Menu.objects.filter(path__in=biz_paths, parent_id=0, del_flag='0')
            .values_list('menu_id', flat=True)
        )
        # 选取：目录(M)/页面(C) 或 perms 以 :query/:view 结尾的按钮(F)
        common_menu_ids = set()
        for m in Menu.objects.filter(del_flag='0'):
            # 属于业务顶级目录本身
            if m.menu_id in biz_root_ids:
                common_menu_ids.add(m.menu_id)
            # 父节点是业务顶级目录（二级菜单）
            elif m.parent_id in biz_root_ids:
                if m.menu_type in ('M', 'C'):
                    common_menu_ids.add(m.menu_id)
            # 父节点的父节点追溯到业务顶级目录（三级按钮）
            else:
                parent = Menu.objects.filter(menu_id=m.parent_id, del_flag='0').first()
                if parent and parent.parent_id in biz_root_ids and m.menu_type == 'F':
                    if m.perms.endswith(':query') or m.perms.endswith(':view'):
                        common_menu_ids.add(m.menu_id)

        common_menus = Menu.objects.filter(menu_id__in=common_menu_ids, del_flag='0')
        RoleMenu.objects.bulk_create([
            RoleMenu(role=common_role, menu=m, create_by='system') for m in common_menus
        ])

        self.stdout.write(self.style.SUCCESS(
            f'角色初始化完成：管理员（{all_menus.count()}个菜单），普通角色（{common_menus.count()}个菜单）'
        ))

    # ------------------------------------------------------------------ 用户
    def _init_users(self, force):
        if force:
            UserRole.objects.all().delete()
            User.objects.filter(username__in=['admin', 'user']).delete()

        # 管理员
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                password='admin123',
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

            admin_role = Role.objects.filter(role_key='admin', del_flag='0').first()
            if admin_role:
                UserRole.objects.create(user=admin_user, role=admin_role, create_by='system')
            self.stdout.write(self.style.SUCCESS('管理员用户 admin 创建成功'))
        else:
            self.stdout.write('管理员用户 admin 已存在，跳过')

        # 普通用户
        if not User.objects.filter(username='user').exists():
            normal_user = User.objects.create_user(
                username='user',
                password='user123',
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

            common_role = Role.objects.filter(role_key='common', del_flag='0').first()
            if common_role:
                UserRole.objects.create(user=normal_user, role=common_role, create_by='system')
            self.stdout.write(self.style.SUCCESS('普通用户 user 创建成功'))
        else:
            self.stdout.write('普通用户 user 已存在，跳过')
