from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from apps.system.models import Menu, Role, RoleMenu, Dept, DictType, DictData
from django.contrib.auth import get_user_model
import json
from datetime import datetime


User = get_user_model()


class Command(BaseCommand):
    help = "Export system data (menus, roles, depts, dicts) to JSON for migration: 导出系统数据(菜单、角色、部门、字典)到JSON用于迁移"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='system_data.json',
            help='Output JSON file path (default: system_data.json)',
        )
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='JSON indentation (default: 2)',
        )
        parser.add_argument(
            '--include',
            type=str,
            default='menus,roles,depts,dicts',
            help='Comma-separated data types to export (default: menus,roles,depts,dicts)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        indent = options['indent']
        include_types = set(options['include'].split(','))

        export_data = {
            'version': '1.0',
            'export_time': datetime.now().isoformat(),
            'data_types': list(include_types),
        }

        # Export menus
        if 'menus' in include_types:
            self.stdout.write('Exporting menus...')
            menus = Menu.objects.filter(del_flag='0').order_by('menu_id')
            menu_list = []
            for menu in menus:
                menu_dict = {
                    'menu_id': menu.menu_id,
                    'parent_id': menu.parent_id,
                    'menu_name': menu.menu_name,
                    'order_num': menu.order_num,
                    'path': menu.path,
                    'component': menu.component,
                    'route_name': menu.route_name,
                    'query': menu.query,
                    'is_frame': menu.is_frame,
                    'is_cache': menu.is_cache,
                    'menu_type': menu.menu_type,
                    'visible': menu.visible,
                    'status': menu.status,
                    'perms': menu.perms,
                    'icon': menu.icon,
                    'remark': menu.remark,
                }
                menu_list.append(menu_dict)
            export_data['menus'] = menu_list
            export_data['menu_count'] = len(menu_list)

        # Export roles
        if 'roles' in include_types:
            self.stdout.write('Exporting roles...')
            roles = Role.objects.filter(del_flag='0').order_by('role_id')
            role_list = []
            for role in roles:
                role_dict = {
                    'role_id': role.role_id,
                    'role_name': role.role_name,
                    'role_key': role.role_key,
                    'role_sort': role.role_sort,
                    'data_scope': role.data_scope,
                    'menu_check_strictly': role.menu_check_strictly,
                    'dept_check_strictly': role.dept_check_strictly,
                    'status': role.status,
                    'remark': role.remark,
                }
                role_list.append(role_dict)
            export_data['roles'] = role_list
            export_data['role_count'] = len(role_list)

        # Export role-menu associations
        if 'roles' in include_types:
            self.stdout.write('Exporting role-menu associations...')
            role_menus = RoleMenu.objects.filter(del_flag='0')
            role_menu_list = []
            for rm in role_menus:
                rm_dict = {
                    'role_id': rm.role_id,
                    'menu_id': rm.menu_id,
                }
                role_menu_list.append(rm_dict)
            export_data['role_menus'] = role_menu_list
            export_data['role_menu_count'] = len(role_menu_list)

        # Export departments
        if 'depts' in include_types:
            self.stdout.write('Exporting departments...')
            depts = Dept.objects.filter(del_flag='0').order_by('dept_id')
            dept_list = []
            for dept in depts:
                dept_dict = {
                    'dept_id': dept.dept_id,
                    'parent_id': dept.parent_id,
                    'ancestors': dept.ancestors,
                    'dept_name': dept.dept_name,
                    'order_num': dept.order_num,
                    'leader': dept.leader,
                    'phone': dept.phone,
                    'email': dept.email,
                    'status': dept.status,
                }
                dept_list.append(dept_dict)
            export_data['departments'] = dept_list
            export_data['department_count'] = len(dept_list)

        # Export dictionary types
        if 'dicts' in include_types:
            self.stdout.write('Exporting dictionary types...')
            dict_types = DictType.objects.filter(del_flag='0').order_by('dict_id')
            dict_type_list = []
            for dt in dict_types:
                dt_dict = {
                    'dict_id': dt.dict_id,
                    'dict_name': dt.dict_name,
                    'dict_type': dt.dict_type,
                    'status': dt.status,
                    'remark': dt.remark,
                }
                dict_type_list.append(dt_dict)
            export_data['dict_types'] = dict_type_list
            export_data['dict_type_count'] = len(dict_type_list)

        # Export dictionary data
        if 'dicts' in include_types:
            self.stdout.write('Exporting dictionary data...')
            dict_data = DictData.objects.filter(del_flag='0').order_by('dict_code')
            dict_data_list = []
            for dd in dict_data:
                dd_dict = {
                    'dict_code': dd.dict_code,
                    'dict_sort': dd.dict_sort,
                    'dict_label': dd.dict_label,
                    'dict_value': dd.dict_value,
                    'dict_type': dd.dict_type,
                    'css_class': dd.css_class,
                    'list_class': dd.list_class,
                    'status': dd.status,
                    'remark': dd.remark,
                }
                dict_data_list.append(dd_dict)
            export_data['dict_data'] = dict_data_list
            export_data['dict_data_count'] = len(dict_data_list)

        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=indent, cls=DjangoJSONEncoder)

        # Print summary
        self.stdout.write(self.style.SUCCESS(f'\nExport Summary:'))
        if 'menus' in include_types:
            self.stdout.write(f'  Menus: {export_data.get("menu_count", 0)}')
        if 'roles' in include_types:
            self.stdout.write(f'  Roles: {export_data.get("role_count", 0)}')
            self.stdout.write(f'  Role-Menus: {export_data.get("role_menu_count", 0)}')
        if 'depts' in include_types:
            self.stdout.write(f'  Departments: {export_data.get("department_count", 0)}')
        if 'dicts' in include_types:
            self.stdout.write(f'  Dict Types: {export_data.get("dict_type_count", 0)}')
            self.stdout.write(f'  Dict Data: {export_data.get("dict_data_count", 0)}')
        self.stdout.write(self.style.SUCCESS(f'Successfully exported to {output_file}'))
