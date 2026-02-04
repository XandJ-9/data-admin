"""
从旧应用迁移数据到 dataasset 应用

迁移顺序：
1. DataSource（sys_datasource → dataasset_datasource）
2. MetaTable（datameta_table → dataasset_meta_table）
3. MetaColumn（datameta_column → dataasset_meta_column）
4. MetaCollectionTask（datameta_collection_task → dataasset_collection_task）

运行方式：
    python manage.py migrate_from_legacy
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = '从旧应用迁移数据到 dataasset 应用'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='试运行模式，不实际执行迁移',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  试运行模式 - 不会实际修改数据'))

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📦 开始数据迁移：datasource + datameta → dataasset')
        self.stdout.write('=' * 60 + '\n')

        try:
            with transaction.atomic():
                # 1. 迁移 DataSource
                self.stdout.write('🔄 步骤 1/4: 迁移 DataSource...')
                ds_count = self.migrate_datasource(dry_run)
                self.stdout.write(self.style.SUCCESS(f'   ✓ 完成！迁移 {ds_count} 条记录\n'))

                # 2. 迁移 MetaTable
                self.stdout.write('🔄 步骤 2/4: 迁移 MetaTable...')
                table_count = self.migrate_meta_table(dry_run)
                self.stdout.write(self.style.SUCCESS(f'   ✓ 完成！迁移 {table_count} 条记录\n'))

                # 3. 迁移 MetaColumn
                self.stdout.write('🔄 步骤 3/4: 迁移 MetaColumn...')
                column_count = self.migrate_meta_column(dry_run)
                self.stdout.write(self.style.SUCCESS(f'   ✓ 完成！迁移 {column_count} 条记录\n'))

                # 4. 迁移 MetaCollectionTask
                self.stdout.write('🔄 步骤 4/4: 迁移 MetaCollectionTask...')
                task_count = self.migrate_collection_task(dry_run)
                self.stdout.write(self.style.SUCCESS(f'   ✓ 完成！迁移 {task_count} 条记录\n'))

                self.stdout.write('=' * 60)
                self.stdout.write(self.style.SUCCESS('✅ 数据迁移完成！'))
                self.stdout.write('=' * 60)
                self.stdout.write(f'\n总计迁移记录数：')
                self.stdout.write(f'  - DataSource: {ds_count}')
                self.stdout.write(f'  - MetaTable: {table_count}')
                self.stdout.write(f'  - MetaColumn: {column_count}')
                self.stdout.write(f'  - MetaCollectionTask: {task_count}')
                self.stdout.write(f'  - 总计: {ds_count + table_count + column_count + task_count}')

                if dry_run:
                    self.stdout.write(self.style.WARNING('\n⚠️  这是试运行，数据未被实际修改'))
                    # 事务会自动回滚
                    raise transaction.TransactionManagementError("Dry run - rolling back")

        except Exception as e:
            if dry_run and "Dry run" in str(e):
                self.stdout.write(self.style.SUCCESS('\n✓ 试运行完成，事务已回滚'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ 迁移失败: {e}'))
                raise

    def migrate_datasource(self, dry_run):
        """迁移 DataSource"""
        try:
            from apps.datasource.models import DataSource as OldDataSource
            from apps.dataasset.models import DataSource as NewDataSource
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  无法导入旧模型: {e}'))
            return 0

        old_count = OldDataSource.objects.count()
        if old_count == 0:
            self.stdout.write('   ℹ️  旧数据表为空，跳过')
            return 0

        # 检查新表是否已有数据
        new_count = NewDataSource.objects.count()
        if new_count > 0:
            self.stdout.write(self.style.WARNING(f'   ⚠️  新表已有 {new_count} 条记录，将清空后重新迁移'))
            if not dry_run:
                NewDataSource.objects.all().delete()

        migrated = 0
        for old_obj in OldDataSource.objects.all():
            if not dry_run:
                NewDataSource.objects.create(
                    id=old_obj.id,  # 保持 ID 一致
                    name=old_obj.name,
                    db_type=old_obj.db_type,
                    host=old_obj.host,
                    port=old_obj.port,
                    db_name=old_obj.db_name,
                    username=old_obj.username,
                    password=old_obj.password,
                    params=old_obj.params,
                    status=old_obj.status,
                    remark=old_obj.remark,
                    del_flag=old_obj.del_flag,
                    create_by=old_obj.create_by,
                    update_by=old_obj.update_by,
                    create_time=old_obj.create_time,
                    update_time=old_obj.update_time,
                )
            migrated += 1

        return migrated

    def migrate_meta_table(self, dry_run):
        """迁移 MetaTable"""
        try:
            from apps.datameta.models import MetaTable as OldMetaTable
            from apps.dataasset.models import MetaTable as NewMetaTable
            from apps.dataasset.models import DataSource
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  无法导入旧模型: {e}'))
            return 0

        old_count = OldMetaTable.objects.count()
        if old_count == 0:
            self.stdout.write('   ℹ️  旧数据表为空，跳过')
            return 0

        # 检查新表是否已有数据
        new_count = NewMetaTable.objects.count()
        if new_count > 0:
            self.stdout.write(self.style.WARNING(f'   ⚠️  新表已有 {new_count} 条记录，将清空后重新迁移'))
            if not dry_run:
                NewMetaTable.objects.all().delete()

        migrated = 0
        for old_obj in OldMetaTable.objects.all():
            # 映射 data_source 外键
            try:
                data_source = DataSource.objects.get(id=old_obj.data_source_id)
            except DataSource.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'   ⚠️  无法找到 DataSource ID={old_obj.data_source_id}，跳过'))
                continue

            if not dry_run:
                NewMetaTable.objects.create(
                    id=old_obj.id,
                    data_source=data_source,
                    table_name=old_obj.table_name,
                    comment=old_obj.comment,
                    database=old_obj.database,
                    del_flag=old_obj.del_flag,
                    create_by=old_obj.create_by,
                    update_by=old_obj.update_by,
                    create_time=old_obj.create_time,
                    update_time=old_obj.update_time,
                )
            migrated += 1

        return migrated

    def migrate_meta_column(self, dry_run):
        """迁移 MetaColumn"""
        try:
            from apps.datameta.models import MetaColumn as OldMetaColumn
            from apps.dataasset.models import MetaColumn as NewMetaColumn
            from apps.dataasset.models import MetaTable
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  无法导入旧模型: {e}'))
            return 0

        old_count = OldMetaColumn.objects.count()
        if old_count == 0:
            self.stdout.write('   ℹ️  旧数据表为空，跳过')
            return 0

        # 检查新表是否已有数据
        new_count = NewMetaColumn.objects.count()
        if new_count > 0:
            self.stdout.write(self.style.WARNING(f'   ⚠️  新表已有 {new_count} 条记录，将清空后重新迁移'))
            if not dry_run:
                NewMetaColumn.objects.all().delete()

        migrated = 0
        for old_obj in OldMetaColumn.objects.all():
            # 映射外键
            try:
                table = MetaTable.objects.get(id=old_obj.table_id)
            except MetaTable.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'   ⚠️  无法找到 MetaTable ID={old_obj.table_id}，跳过'))
                continue

            try:
                data_source = table.data_source
            except Exception:
                self.stdout.write(self.style.WARNING(f'   ⚠️  无法获取 data_source，跳过'))
                continue

            if not dry_run:
                NewMetaColumn.objects.create(
                    id=old_obj.id,
                    data_source=data_source,
                    table=table,
                    order=old_obj.order,
                    name=old_obj.name,
                    type=old_obj.type,
                    notnull=old_obj.notnull,
                    default=old_obj.default,
                    primary=old_obj.primary,
                    comment=old_obj.comment,
                    del_flag=old_obj.del_flag,
                    create_by=old_obj.create_by,
                    update_by=old_obj.update_by,
                    create_time=old_obj.create_time,
                    update_time=old_obj.update_time,
                )
            migrated += 1

        return migrated

    def migrate_collection_task(self, dry_run):
        """迁移 MetaCollectionTask"""
        try:
            from apps.datameta.models import MetaCollectionTask as OldMetaCollectionTask
            from apps.dataasset.models import MetaCollectionTask as NewMetaCollectionTask
            from apps.dataasset.models import DataSource
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  无法导入旧模型: {e}'))
            return 0

        old_count = OldMetaCollectionTask.objects.count()
        if old_count == 0:
            self.stdout.write('   ℹ️  旧数据表为空，跳过')
            return 0

        # 检查新表是否已有数据
        new_count = NewMetaCollectionTask.objects.count()
        if new_count > 0:
            self.stdout.write(self.style.WARNING(f'   ⚠️  新表已有 {new_count} 条记录，将清空后重新迁移'))
            if not dry_run:
                NewMetaCollectionTask.objects.all().delete()

        migrated = 0
        for old_obj in OldMetaCollectionTask.objects.all():
            # 映射 data_source 外键
            try:
                data_source = DataSource.objects.get(id=old_obj.data_source_id)
            except DataSource.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'   ⚠️  无法找到 DataSource ID={old_obj.data_source_id}，跳过'))
                continue

            if not dry_run:
                NewMetaCollectionTask.objects.create(
                    id=old_obj.id,
                    task_id=old_obj.task_id,
                    data_source=data_source,
                    status=old_obj.status,
                    progress=old_obj.progress,
                    current_table=old_obj.current_table,
                    total_tables=old_obj.total_tables,
                    collected_tables=old_obj.collected_tables,
                    failed_tables=old_obj.failed_tables,
                    database_name=old_obj.database_name,
                    error_message=old_obj.error_message,
                    started_at=old_obj.started_at,
                    completed_at=old_obj.completed_at,
                    thread_id=old_obj.thread_id,
                    del_flag=old_obj.del_flag,
                    create_by=old_obj.create_by,
                    update_by=old_obj.update_by,
                    create_time=old_obj.create_time,
                    update_time=old_obj.update_time,
                )
            migrated += 1

        return migrated
