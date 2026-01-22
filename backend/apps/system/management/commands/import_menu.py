from django.core.management.base import BaseCommand
from apps.system.models import Menu
from django.utils import timezone
import json
import os


class Command(BaseCommand):
    help = "Import menu data from JSON file for migration: 从JSON文件导入菜单数据用于迁移"

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file',
            type=str,
            help='Input JSON file path',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing menus (default: skip existing)',
        )
        parser.add_argument(
            '--skip-audit',
            action='store_true',
            help='Skip updating audit fields (create_by, update_by, create_time, update_time)',
        )

    def handle(self, *args, **options):
        input_file = options['input_file']
        overwrite = options['overwrite']
        skip_audit = options['skip_audit']

        # Check if file exists
        if not os.path.exists(input_file):
            self.stdout.write(
                self.style.ERROR(f'File not found: {input_file}')
            )
            return

        # Read JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.stdout.write(
                    self.style.ERROR(f'Invalid JSON file: {e}')
                )
                return

        # Validate data structure
        if 'menus' not in data:
            self.stdout.write(
                self.style.ERROR('Invalid menu data format: missing "menus" field')
            )
            return

        menu_list = data['menus']
        now = timezone.now()

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for menu_data in menu_list:
            menu_id = menu_data.get('menu_id')

            try:
                # Check if menu exists
                existing_menu = Menu.objects.filter(menu_id=menu_id).first()

                if existing_menu:
                    if overwrite:
                        # Update existing menu
                        for field, value in menu_data.items():
                            if field == 'menu_id':
                                continue
                            if skip_audit and field in ['create_by', 'update_by', 'create_time', 'update_time']:
                                continue
                            setattr(existing_menu, field, value)

                        if not skip_audit:
                            existing_menu.update_time = now

                        existing_menu.save()
                        updated_count += 1
                    else:
                        skipped_count += 1
                else:
                    # Create new menu
                    create_data = menu_data.copy()

                    if skip_audit:
                        # Set default audit fields
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now

                    Menu.objects.create(**create_data)
                    created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing menu {menu_data.get("menu_name")}: {str(e)}')
                )
                error_count += 1

        # Output summary
        self.stdout.write(self.style.SUCCESS('\nImport Summary:'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'  Errors: {error_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total: {len(menu_list)}'))
