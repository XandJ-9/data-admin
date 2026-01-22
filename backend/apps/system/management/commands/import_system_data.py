from django.core.management.base import BaseCommand
from apps.system.models import Menu, Role, RoleMenu, Dept, DictType, DictData
from django.utils import timezone
from django.db import transaction
import json
import os


class Command(BaseCommand):
    help = "Import system data from JSON for migration: 从JSON导入系统数据用于迁移"

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file',
            type=str,
            help='Input JSON file path',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing records (default: skip existing)',
        )
        parser.add_argument(
            '--skip-audit',
            action='store_true',
            help='Reset audit fields to system defaults',
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

        now = timezone.now()
        summary = {}

        # Import menus
        if 'menus' in data:
            self.stdout.write('\nImporting menus...')
            summary['menus'] = self._import_menus(data['menus'], overwrite, skip_audit, now)

        # Import roles
        if 'roles' in data:
            self.stdout.write('\nImporting roles...')
            summary['roles'] = self._import_roles(data['roles'], overwrite, skip_audit, now)

        # Import role-menu associations
        if 'role_menus' in data:
            self.stdout.write('\nImporting role-menu associations...')
            summary['role_menus'] = self._import_role_menus(data['role_menus'], overwrite, skip_audit, now)

        # Import departments
        if 'departments' in data:
            self.stdout.write('\nImporting departments...')
            summary['departments'] = self._import_departments(data['departments'], overwrite, skip_audit, now)

        # Import dictionary types
        if 'dict_types' in data:
            self.stdout.write('\nImporting dictionary types...')
            summary['dict_types'] = self._import_dict_types(data['dict_types'], overwrite, skip_audit, now)

        # Import dictionary data
        if 'dict_data' in data:
            self.stdout.write('\nImporting dictionary data...')
            summary['dict_data'] = self._import_dict_data(data['dict_data'], overwrite, skip_audit, now)

        # Print final summary
        self.stdout.write(self.style.SUCCESS('\n=== Import Summary ==='))
        for key, stats in summary.items():
            self.stdout.write(f'{key}:')
            self.stdout.write(f'  Created: {stats["created"]}')
            self.stdout.write(f'  Updated: {stats["updated"]}')
            self.stdout.write(f'  Skipped: {stats["skipped"]}')
            if stats['errors'] > 0:
                self.stdout.write(self.style.ERROR(f'  Errors: {stats["errors"]}'))

    def _import_menus(self, menu_list, overwrite, skip_audit, now):
        created = updated = skipped = errors = 0

        for menu_data in menu_list:
            menu_id = menu_data.get('menu_id')
            try:
                existing = Menu.objects.filter(menu_id=menu_id).first()

                if existing:
                    if overwrite:
                        for field, value in menu_data.items():
                            if field == 'menu_id':
                                continue
                            setattr(existing, field, value)
                        if not skip_audit:
                            existing.update_time = now
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    create_data = menu_data.copy()
                    if skip_audit:
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now
                    Menu.objects.create(**create_data)
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing menu {menu_data.get("menu_name")}: {str(e)}'))
                errors += 1

        return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}

    def _import_roles(self, role_list, overwrite, skip_audit, now):
        created = updated = skipped = errors = 0

        for role_data in role_list:
            role_id = role_data.get('role_id')
            try:
                existing = Role.objects.filter(role_id=role_id).first()

                if existing:
                    if overwrite:
                        for field, value in role_data.items():
                            if field == 'role_id':
                                continue
                            setattr(existing, field, value)
                        if not skip_audit:
                            existing.update_time = now
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    create_data = role_data.copy()
                    if skip_audit:
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now
                    Role.objects.create(**create_data)
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing role {role_data.get("role_name")}: {str(e)}'))
                errors += 1

        return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}

    def _import_role_menus(self, rm_list, overwrite, skip_audit, now):
        created = skipped = errors = 0

        for rm_data in rm_list:
            role_id = rm_data.get('role_id')
            menu_id = rm_data.get('menu_id')
            try:
                existing = RoleMenu.objects.filter(role_id=role_id, menu_id=menu_id).first()

                if existing:
                    skipped += 1
                else:
                    create_data = {
                        'role_id': role_id,
                        'menu_id': menu_id,
                    }
                    if skip_audit:
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now
                    RoleMenu.objects.create(**create_data)
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing role-menu ({role_id}, {menu_id}): {str(e)}'))
                errors += 1

        return {'created': created, 'updated': 0, 'skipped': skipped, 'errors': errors}

    def _import_departments(self, dept_list, overwrite, skip_audit, now):
        created = updated = skipped = errors = 0

        for dept_data in dept_list:
            dept_id = dept_data.get('dept_id')
            try:
                existing = Dept.objects.filter(dept_id=dept_id).first()

                if existing:
                    if overwrite:
                        for field, value in dept_data.items():
                            if field == 'dept_id':
                                continue
                            setattr(existing, field, value)
                        if not skip_audit:
                            existing.update_time = now
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    create_data = dept_data.copy()
                    if skip_audit:
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now
                    Dept.objects.create(**create_data)
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing dept {dept_data.get("dept_name")}: {str(e)}'))
                errors += 1

        return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}

    def _import_dict_types(self, dt_list, overwrite, skip_audit, now):
        created = updated = skipped = errors = 0

        for dt_data in dt_list:
            dict_id = dt_data.get('dict_id')
            try:
                existing = DictType.objects.filter(dict_id=dict_id).first()

                if existing:
                    if overwrite:
                        for field, value in dt_data.items():
                            if field == 'dict_id':
                                continue
                            setattr(existing, field, value)
                        if not skip_audit:
                            existing.update_time = now
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    create_data = dt_data.copy()
                    if skip_audit:
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now
                    DictType.objects.create(**create_data)
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing dict type {dt_data.get("dict_name")}: {str(e)}'))
                errors += 1

        return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}

    def _import_dict_data(self, dd_list, overwrite, skip_audit, now):
        created = updated = skipped = errors = 0

        for dd_data in dd_list:
            dict_code = dd_data.get('dict_code')
            try:
                existing = DictData.objects.filter(dict_code=dict_code).first()

                if existing:
                    if overwrite:
                        for field, value in dd_data.items():
                            if field == 'dict_code':
                                continue
                            setattr(existing, field, value)
                        if not skip_audit:
                            existing.update_time = now
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    create_data = dd_data.copy()
                    if skip_audit:
                        create_data['create_by'] = 'system'
                        create_data['update_by'] = 'system'
                        create_data['create_time'] = now
                        create_data['update_time'] = now
                    DictData.objects.create(**create_data)
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing dict data {dd_data.get("dict_label")}: {str(e)}'))
                errors += 1

        return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}
