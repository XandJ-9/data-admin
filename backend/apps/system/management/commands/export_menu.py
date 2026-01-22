from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from apps.system.models import Menu
import json
from datetime import datetime


class Command(BaseCommand):
    help = "Export menu data to JSON file for migration: 导出菜单数据到JSON文件用于迁移"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='menu_data.json',
            help='Output JSON file path (default: menu_data.json)',
        )
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='JSON indentation (default: 2)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        indent = options['indent']

        # Query all menu records (excluding deleted ones)
        menus = Menu.objects.filter(del_flag='0').order_by('menu_id')

        # Build menu data list
        menu_data = []
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
                'create_by': menu.create_by,
                'update_by': menu.update_by,
                'create_time': menu.create_time.isoformat() if menu.create_time else None,
                'update_time': menu.update_time.isoformat() if menu.update_time else None,
            }
            menu_data.append(menu_dict)

        # Prepare export data structure
        export_data = {
            'version': '1.0',
            'export_time': datetime.now().isoformat(),
            'total_count': len(menu_data),
            'menus': menu_data,
        }

        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=indent, cls=DjangoJSONEncoder)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {len(menu_data)} menu records to {output_file}')
        )
