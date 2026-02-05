"""
添加/更新数据服务管理菜单

运行方式:
    python manage.py add_dataservice_menu

支持选项:
    --force    强制更新所有菜单配置（即使已存在也会更新）
"""

from django.core.management.base import BaseCommand
from apps.system.models import Menu
from django.db import transaction


class Command(BaseCommand):
    help = '添加或更新数据服务管理菜单到系统'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='强制更新所有菜单配置，即使已存在也会更新'
        )

    def handle(self, *args, **options):
        force_update = options.get('force', False)

        self.stdout.write('\n' + '='*60)
        if force_update:
            self.stdout.write('[更新] 开始更新数据服务管理菜单（强制模式）')
        else:
            self.stdout.write('[添加] 开始添加数据服务管理菜单')
        self.stdout.write('='*60 + '\n')

        try:
            with transaction.atomic():
                # 1. 创建/更新一级菜单
                self.stdout.write('[步骤 1/3] 处理一级菜单...')
                parent_menu = self.create_parent_menu(force_update)
                action = "创建" if parent_menu.action == 'created' else "更新"
                self.stdout.write(self.style.SUCCESS(f'   {action}成功！菜单ID: {parent_menu.menu_id}\n'))

                # 2. 创建/更新 SQL 查询菜单
                self.stdout.write('[步骤 2/3] 处理 SQL 查询菜单...')
                self.create_query_menu(parent_menu.menu_id, force_update)
                self.stdout.write(self.style.SUCCESS('   [成功] 处理完成\n'))

                # 3. 创建/更新接口管理菜单
                self.stdout.write('[步骤 3/3] 处理接口管理菜单...')
                self.create_interface_menu(parent_menu.menu_id, force_update)
                self.stdout.write(self.style.SUCCESS('   [成功] 处理完成\n'))

                self.stdout.write('='*60)
                if force_update:
                    self.stdout.write(self.style.SUCCESS('[完成] 数据服务管理菜单更新完成！'))
                else:
                    self.stdout.write(self.style.SUCCESS('[完成] 数据服务管理菜单添加完成！'))
                self.stdout.write('='*60)
                self.stdout.write('\n菜单结构：')
                self.stdout.write('  数据服务管理')
                self.stdout.write('  |-- SQL 查询')
                self.stdout.write('  |-- 接口管理')
                self.stdout.write('\n请刷新页面查看菜单！\n')

                # 显示统计信息
                self.show_statistics(parent_menu.menu_id)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[失败] 操作失败: {e}'))
            raise

    def create_parent_menu(self, force_update=False):
        """创建或更新一级菜单"""
        if force_update:
            # 强制更新模式：先查找再更新
            try:
                menu = Menu.objects.get(menu_name='数据服务管理')
                menu.parent_id = 0
                menu.order_num = 6
                menu.path = '/data-service'
                menu.component = ''
                menu.query = ''
                menu.route_name = ''
                menu.is_frame = 1
                menu.is_cache = 0
                menu.menu_type = 'M'
                menu.visible = '0'
                menu.status = '0'
                menu.perms = ''
                menu.icon = 'server'
                menu.update_by = 'admin'
                menu.remark = '数据服务管理模块'
                menu.save()
                menu.action = 'updated'
                self.stdout.write(f'   [提示] 已存在菜单，执行更新\n')
            except Menu.DoesNotExist:
                # 不存在则创建
                menu = Menu.objects.create(
                    menu_name='数据服务管理',
                    parent_id=0,
                    order_num=6,
                    path='/data-service',
                    component='',
                    query='',
                    route_name='',
                    is_frame=1,
                    is_cache=0,
                    menu_type='M',
                    visible='0',
                    status='0',
                    perms='',
                    icon='server',
                    create_by='admin',
                    update_by='admin',
                    remark='数据服务管理模块'
                )
                menu.action = 'created'
                self.stdout.write(f'   [新建] 新建菜单\n')
        else:
            # 标准模式：使用get_or_create
            menu, created = Menu.objects.get_or_create(
                menu_name='数据服务管理',
                defaults={
                    'parent_id': 0,
                    'order_num': 6,
                    'path': '/data-service',
                    'component': '',
                    'query': '',
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'M',
                    'visible': '0',
                    'status': '0',
                    'perms': '',
                    'icon': 'server',
                    'create_by': 'admin',
                    'update_by': 'admin',
                    'remark': '数据服务管理模块'
                }
            )
            menu.action = 'created' if created else 'existed'

        return menu

    def create_query_menu(self, parent_id, force_update=False):
        """创建或更新 SQL 查询菜单"""
        self.create_or_update_menu(
            menu_name='SQL 查询',
            parent_id=parent_id,
            order_num=1,
            path='query',
            component='data/service/query/index',
            route_name='DataServiceQuery',
            icon='code',
            perms='system:dataservice:query',
            remark='SQL 查询页面',
            force_update=force_update
        )

    def create_interface_menu(self, parent_id, force_update=False):
        """创建或更新接口管理菜单"""
        self.create_or_update_menu(
            menu_name='接口管理',
            parent_id=parent_id,
            order_num=2,
            path='interface',
            component='data/service/interface/index',
            route_name='DataServiceInterface',
            icon='guide',
            perms='system:dataservice:interface',
            remark='数据接口管理页面',
            force_update=force_update
        )

    def create_or_update_menu(self, menu_name, parent_id, order_num, path, component,
                            route_name, icon, perms, remark, force_update=False):
        """创建或更新菜单的通用方法"""
        defaults = {
            'parent_id': parent_id,
            'order_num': order_num,
            'path': path,
            'component': component,
            'query': '',
            'route_name': route_name,
            'is_frame': 0,
            'is_cache': 0,
            'menu_type': 'C',
            'visible': '0',
            'status': '0',
            'perms': perms,
            'icon': icon,
            'create_by': 'admin',
            'update_by': 'admin',
            'remark': remark
        }

        if force_update:
            # 强制更新模式：先查找再更新
            try:
                menu = Menu.objects.get(menu_name=menu_name, parent_id=parent_id)
                # 更新所有字段
                for key, value in defaults.items():
                    setattr(menu, key, value)
                menu.save()
                self.stdout.write(f'   [更新] 更新菜单: {menu_name}\n')
            except Menu.DoesNotExist:
                # 不存在则创建
                Menu.objects.create(**defaults)
                self.stdout.write(f'   [新建] 新建菜单: {menu_name}\n')
        else:
            # 标准模式：使用update_or_create
            menu, created = Menu.objects.update_or_create(
                menu_name=menu_name,
                parent_id=parent_id,
                defaults=defaults
            )
            action = '创建' if created else '已存在'
            if action == '已存在':
                self.stdout.write(f'   [跳过] 菜单已存在: {menu_name}\n')
            else:
                self.stdout.write(f'   [新建] 新建菜单: {menu_name}\n')

    def show_statistics(self, parent_menu_id):
        """显示统计信息"""
        try:
            # 查询所有子菜单
            children = Menu.objects.filter(parent_id=parent_menu_id)
            total_count = children.count()

            self.stdout.write('\n' + '-'*60)
            self.stdout.write('[统计] 菜单统计')
            self.stdout.write('-'*60 + '\n')
            self.stdout.write(f'一级菜单ID: {parent_menu_id}')
            self.stdout.write(f'二级菜单数量: {total_count}')
            self.stdout.write('\n子菜单列表:')

            for menu in children.order_by('order_num'):
                status_icon = '[正常]' if menu.status == '0' else '[停用]'
                visible_icon = '[显示]' if menu.visible == '0' else '[隐藏]'
                self.stdout.write(
                    f"  {menu.order_num}. {menu.menu_name} "
                    f"[{menu.menu_type}] {status_icon} {visible_icon}\n"
                )

            self.stdout.write('='*60 + '\n')
        except Exception as e:
            self.stdout.write(f'统计信息获取失败: {e}\n')
