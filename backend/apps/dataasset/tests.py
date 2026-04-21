from unittest.mock import patch
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.datasource.models import DataSource

from .models import AssetNamespace, DataAsset, DataAssetColumn, MetaColumn, MetaCollectionTask, MetaTable
from .collectors import MetadataCollectionExecutor, cancel_collection_task, start_collection_task
from .services import collect_table_metadata, sync_standard_asset_from_meta_table
from .views import AssetNamespaceViewSet, DataAssetColumnViewSet, DataAssetViewSet, MetaColumnViewSet, MetaTableViewSet


class DataAssetModelRefactorTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='asset_tester', password='password123')
        self.data_source = DataSource.objects.create(
            name='warehouse',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='demo',
            username='root',
            password='secret',
            params='{}',
            status='0',
        )

    @patch('apps.dbutils.get_table_schema')
    @patch('apps.dbutils.get_table_info')
    def test_collect_table_metadata_should_dual_write_standard_asset_models(self, mock_get_table_info, mock_get_table_schema):
        mock_get_table_info.return_value = {
            'tableName': 'orders',
            'databaseName': 'sales',
            'comment': '订单表',
        }
        mock_get_table_schema.return_value = [
            {
                'order': 1,
                'name': 'id',
                'type': 'bigint',
                'notnull': True,
                'default': None,
                'primary': True,
                'comment': '主键',
            },
            {
                'order': 2,
                'name': 'buyer_name',
                'type': 'varchar',
                'notnull': False,
                'default': '',
                'primary': False,
                'comment': '买家姓名',
            },
        ]

        meta_table = collect_table_metadata({'type': 'mysql'}, self.data_source.id, 'orders', user=self.user)

        namespace = AssetNamespace.objects.get(data_source=self.data_source, catalog_name='sales', schema_name='')
        asset = DataAsset.objects.get(namespace=namespace, object_name='orders')
        columns = list(DataAssetColumn.objects.filter(asset=asset).order_by('ordinal_position'))

        self.assertEqual(meta_table.table_name, 'orders')
        self.assertEqual(namespace.environment, 'default')
        self.assertEqual(asset.legacy_meta_table_id, meta_table.id)
        self.assertEqual(asset.comment, '订单表')
        self.assertEqual(asset.qualified_name, f'{self.data_source.id}:default:sales::table:orders')
        self.assertEqual(len(columns), 2)
        self.assertFalse(columns[0].is_nullable)
        self.assertTrue(columns[1].is_nullable)
        self.assertEqual(columns[0].legacy_meta_column_id, meta_table.columns.order_by('order').first().id)

    @patch('apps.dbutils.get_table_schema')
    @patch('apps.dbutils.get_table_info')
    def test_collect_table_metadata_should_split_presto_catalog_and_schema(self, mock_get_table_info, mock_get_table_schema):
        self.data_source.db_type = 'presto'
        self.data_source.save(update_fields=['db_type'])
        mock_get_table_info.return_value = {
            'tableName': 'orders',
            'databaseName': 'lakehouse.analytics',
            'comment': '订单表',
        }
        mock_get_table_schema.return_value = [
            {
                'order': 1,
                'name': 'id',
                'type': 'bigint',
                'notnull': True,
                'default': None,
                'primary': True,
                'comment': '主键',
            },
        ]

        collect_table_metadata({'type': 'presto'}, self.data_source.id, 'orders', user=self.user)

        namespace = AssetNamespace.objects.get(data_source=self.data_source, catalog_name='lakehouse', schema_name='analytics')
        asset = DataAsset.objects.get(namespace=namespace, object_name='orders')

        self.assertEqual(asset.qualified_name, f'{self.data_source.id}:default:lakehouse:analytics:table:orders')

    @patch('apps.dbutils.get_table_schema')
    @patch('apps.dbutils.get_table_info')
    def test_collect_table_metadata_should_update_columns_in_place(self, mock_get_table_info, mock_get_table_schema):
        mock_get_table_info.return_value = {
            'tableName': 'orders',
            'databaseName': 'sales',
            'comment': '订单表',
        }
        mock_get_table_schema.return_value = [
            {
                'order': 1,
                'name': 'id',
                'type': 'bigint',
                'notnull': True,
                'default': None,
                'primary': True,
                'comment': '主键',
            },
            {
                'order': 2,
                'name': 'buyer_name',
                'type': 'varchar',
                'notnull': False,
                'default': '',
                'primary': False,
                'comment': '买家姓名',
            },
        ]

        collect_table_metadata({'type': 'mysql'}, self.data_source.id, 'orders', user=self.user)
        asset = DataAsset.objects.get(object_name='orders')
        original_column = DataAssetColumn.objects.get(asset=asset, column_name='buyer_name')

        mock_get_table_schema.return_value = [
            {
                'order': 1,
                'name': 'id',
                'type': 'bigint',
                'notnull': True,
                'default': None,
                'primary': True,
                'comment': '主键',
            },
            {
                'order': 2,
                'name': 'buyer_name',
                'type': 'string',
                'notnull': True,
                'default': None,
                'primary': False,
                'comment': '买家姓名更新',
            },
        ]

        collect_table_metadata({'type': 'mysql'}, self.data_source.id, 'orders', user=self.user)

        updated_column = DataAssetColumn.objects.get(asset=asset, column_name='buyer_name')
        self.assertEqual(updated_column.id, original_column.id)
        self.assertEqual(updated_column.data_type, 'string')
        self.assertFalse(updated_column.is_nullable)
        self.assertEqual(updated_column.comment, '买家姓名更新')

    def test_sync_standard_asset_should_update_existing_asset_when_table_identity_changes(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
        )
        sync_standard_asset_from_meta_table(meta_table, user=self.user)

        meta_table.table_name = 'orders_v2'
        meta_table.database = 'sales_dw'
        meta_table.comment = '订单表新版本'
        meta_table.save()
        sync_standard_asset_from_meta_table(meta_table, user=self.user)

        assets = DataAsset.objects.filter(legacy_meta_table_id=meta_table.id)
        self.assertEqual(assets.count(), 1)
        asset = assets.get()
        self.assertEqual(asset.object_name, 'orders_v2')
        self.assertEqual(asset.namespace.display_name, 'sales_dw')
        self.assertEqual(asset.comment, '订单表新版本')

    def test_sync_standard_asset_should_ignore_soft_deleted_meta_columns(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=2,
            name='deleted_col',
            type='varchar',
            comment='已删除字段',
            del_flag='1',
        )

        sync_standard_asset_from_meta_table(meta_table, user=self.user)

        asset = DataAsset.objects.get(object_name='orders')
        self.assertTrue(DataAssetColumn.objects.filter(asset=asset, column_name='id').exists())
        self.assertFalse(DataAssetColumn.objects.filter(asset=asset, column_name='deleted_col').exists())

    @patch('apps.dataasset.collectors.MetadataCollectionExecutor.start', return_value=True)
    def test_start_collection_task_should_split_presto_scope(self, mock_start):
        self.data_source.db_type = 'trino'
        self.data_source.save(update_fields=['db_type'])

        with self.captureOnCommitCallbacks(execute=True):
            task = start_collection_task(self.data_source.id, database_name='lakehouse.analytics', user=self.user)

        self.assertIsNotNone(task)
        self.assertEqual(task.scope_level, 'schema')
        self.assertEqual(task.scope_catalog_name, 'lakehouse')
        self.assertEqual(task.scope_schema_name, 'analytics')
        self.assertEqual(task.scope_asset_name, '')
        mock_start.assert_called_once()

    @patch('apps.dataasset.collectors.MetadataCollectionExecutor.start', return_value=True)
    def test_start_collection_task_should_reject_existing_active_task(self, mock_start):
        MetaCollectionTask.objects.create(
            task_id='existing-task',
            data_source=self.data_source,
            status='running',
        )

        with self.captureOnCommitCallbacks(execute=True):
            task = start_collection_task(self.data_source.id, database_name='sales', user=self.user)

        self.assertIsNone(task)
        mock_start.assert_not_called()

    @patch('apps.dataasset.collectors.MetadataCollectionExecutor.start', side_effect=RuntimeError('cant start thread'))
    def test_start_collection_task_should_mark_failed_when_executor_start_raises(self, mock_start):
        with self.captureOnCommitCallbacks(execute=True):
            task = start_collection_task(self.data_source.id, database_name='sales', user=self.user)

        self.assertIsNotNone(task)
        failed_task = MetaCollectionTask.objects.get(pk=task.pk)
        self.assertEqual(failed_task.status, 'failed')
        self.assertEqual(failed_task.error_message, '采集失败，请检查数据源配置或稍后重试')
        mock_start.assert_called_once()

    def test_cancel_collection_task_should_fallback_to_database_state(self):
        task = MetaCollectionTask.objects.create(
            task_id='pending-task',
            data_source=self.data_source,
            status='pending',
        )

        cancelled = cancel_collection_task(task.task_id)

        task.refresh_from_db()
        self.assertTrue(cancelled)
        self.assertEqual(task.status, 'cancelled')

    @patch('apps.dataasset.collectors.list_tables')
    def test_executor_should_not_restart_cancelled_pending_task(self, mock_list_tables):
        task = MetaCollectionTask.objects.create(
            task_id='cancelled-before-start',
            data_source=self.data_source,
            status='cancelled',
        )
        executor = MetadataCollectionExecutor(task.task_id)
        executor.task = task

        executor._run_collection(self.data_source.id, '', self.user)

        task.refresh_from_db()
        self.assertEqual(task.status, 'cancelled')
        mock_list_tables.assert_not_called()

    @patch('apps.dbutils.get_table_schema')
    @patch('apps.dbutils.get_table_info')
    def test_collect_table_metadata_should_not_delete_existing_columns_when_schema_is_empty(
        self,
        mock_get_table_info,
        mock_get_table_schema,
    ):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
        )
        mock_get_table_info.return_value = {
            'tableName': 'orders',
            'databaseName': 'sales',
            'comment': '订单表',
        }
        mock_get_table_schema.return_value = []

        with self.assertRaisesMessage(ValueError, '字段采集结果为空'):
            collect_table_metadata({'type': 'mysql'}, self.data_source.id, 'orders', user=self.user)

        self.assertEqual(MetaColumn.objects.filter(table=meta_table, del_flag='0').count(), 1)

    def test_meta_table_view_should_read_from_standard_asset_model(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)

        view = MetaTableViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/dataasset/meta-table', {'tableName': 'orders'})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rows'][0]['id'], meta_table.id)
        self.assertEqual(response.data['rows'][0]['tableName'], asset.object_name)
        self.assertEqual(response.data['rows'][0]['databaseName'], asset.namespace.display_name)

    def test_asset_and_compatibility_views_should_preserve_blank_database_name(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='',
            comment='订单表',
            create_by='legacy_creator',
            update_by='legacy_updater',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
            create_by='legacy_creator',
            update_by='legacy_updater',
        )
        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)

        meta_view = MetaTableViewSet.as_view({'get': 'list'})
        meta_request = self.factory.get('/data-api/dataasset/meta-table', {'tableName': 'orders'})
        force_authenticate(meta_request, user=self.user)
        meta_response = meta_view(meta_request)

        column_view = MetaColumnViewSet.as_view({'get': 'list'})
        column_request = self.factory.get('/data-api/dataasset/meta-column', {'tableName': 'orders'})
        force_authenticate(column_request, user=self.user)
        column_response = column_view(column_request)

        asset_view = DataAssetViewSet.as_view({'get': 'list'})
        asset_request = self.factory.get('/data-api/dataasset/asset', {'objectName': 'orders'})
        force_authenticate(asset_request, user=self.user)
        asset_response = asset_view(asset_request)

        asset_column_view = DataAssetColumnViewSet.as_view({'get': 'list'})
        asset_column_request = self.factory.get('/data-api/dataasset/asset-column', {'assetId': asset.id})
        force_authenticate(asset_column_request, user=self.user)
        asset_column_response = asset_column_view(asset_column_request)

        self.assertEqual(meta_response.data['rows'][0]['databaseName'], '')
        self.assertEqual(meta_response.data['rows'][0]['createBy'], 'legacy_creator')
        self.assertEqual(meta_response.data['rows'][0]['updateBy'], 'legacy_updater')
        self.assertEqual(column_response.data['rows'][0]['databaseName'], '')
        self.assertEqual(column_response.data['rows'][0]['createBy'], 'legacy_creator')
        self.assertEqual(column_response.data['rows'][0]['updateBy'], 'legacy_updater')
        self.assertEqual(asset_response.data['rows'][0]['databaseName'], '')
        self.assertEqual(asset_column_response.data['rows'][0]['databaseName'], '')

    def test_meta_table_view_time_filter_should_follow_legacy_meta_table_timestamp(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
        )
        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)
        old_time = timezone.now() - timedelta(days=2)
        new_time = timezone.now()
        MetaTable.objects.filter(pk=meta_table.pk).update(update_time=old_time)
        DataAsset.objects.filter(pk=asset.pk).update(update_time=new_time)

        view = MetaTableViewSet.as_view({'get': 'list'})
        request = self.factory.get(
            '/data-api/dataasset/meta-table',
            {'updateTimeStart': (old_time + timedelta(days=1)).isoformat()},
        )
        force_authenticate(request, user=self.user)
        response = view(request)

        list_request = self.factory.get('/data-api/dataasset/meta-table')
        force_authenticate(list_request, user=self.user)
        list_response = view(list_request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data['rows'][0]['updateTime'], old_time.strftime('%Y-%m-%d %H:%M:%S'))

    def test_asset_and_meta_table_views_should_support_database_name_filter(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        sync_standard_asset_from_meta_table(meta_table, user=self.user)

        asset_view = DataAssetViewSet.as_view({'get': 'list'})
        asset_request = self.factory.get('/data-api/dataasset/asset', {'databaseName': 'sales'})
        force_authenticate(asset_request, user=self.user)
        asset_response = asset_view(asset_request)

        meta_view = MetaTableViewSet.as_view({'get': 'list'})
        meta_request = self.factory.get('/data-api/dataasset/meta-table', {'databaseName': 'sales'})
        force_authenticate(meta_request, user=self.user)
        meta_response = meta_view(meta_request)

        self.assertEqual(asset_response.status_code, 200)
        self.assertEqual(asset_response.data['rows'][0]['databaseName'], 'sales')
        self.assertEqual(meta_response.status_code, 200)
        self.assertEqual(meta_response.data['rows'][0]['databaseName'], 'sales')

    def test_meta_column_view_should_read_from_standard_asset_column_model(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        meta_column = MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='buyer_name',
            type='varchar',
            notnull=False,
            primary=False,
            comment='买家姓名',
        )
        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)

        view = MetaColumnViewSet.as_view({'get': 'list'})
        request = self.factory.get(
            '/data-api/dataasset/meta-column',
            {'tableName': 'orders', 'databaseName': 'sales', 'columnName': 'buyer'},
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rows'][0]['id'], meta_column.id)
        self.assertEqual(response.data['rows'][0]['tableId'], meta_table.id)
        self.assertEqual(response.data['rows'][0]['tableName'], asset.object_name)
        self.assertTrue(response.data['rows'][0]['isNullable'])

    def test_asset_column_view_should_use_legacy_table_id_for_table_id_filter(self):
        namespace = AssetNamespace.objects.create(
            data_source=self.data_source,
            environment='default',
            catalog_name='manual',
            schema_name='',
            namespace_key='1:default:manual:',
            display_name='manual',
        )
        manual_asset = DataAsset.objects.create(
            namespace=namespace,
            asset_type=DataAsset.AssetType.TABLE,
            object_name='manual_orders',
            qualified_name='manual',
            display_name='manual_orders',
        )
        DataAssetColumn.objects.create(
            asset=manual_asset,
            ordinal_position=1,
            column_name='manual_col',
            data_type='varchar',
            is_nullable=True,
        )
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='buyer_name',
            type='varchar',
            notnull=False,
            primary=False,
            comment='买家姓名',
        )
        sync_standard_asset_from_meta_table(meta_table, user=self.user)

        view = DataAssetColumnViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/dataasset/asset-column', {'tableId': meta_table.id})
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['rows']), 1)
        self.assertEqual(response.data['rows'][0]['tableName'], 'orders')

    def test_meta_table_write_should_sync_standard_asset(self):
        create_view = MetaTableViewSet.as_view({'post': 'create'})
        create_request = self.factory.post(
            '/data-api/dataasset/meta-table',
            {
                'dataSourceId': self.data_source.id,
                'tableName': 'orders',
                'databaseName': 'sales',
                'comment': '订单表',
            },
            format='json',
        )
        force_authenticate(create_request, user=self.user)
        create_response = create_view(create_request)

        meta_table = MetaTable.objects.get(table_name='orders')
        asset = DataAsset.objects.get(legacy_meta_table_id=meta_table.id)

        update_view = MetaTableViewSet.as_view({'put': 'update'})
        update_request = self.factory.put(
            f'/data-api/dataasset/meta-table/{meta_table.id}',
            {
                'id': meta_table.id,
                'dataSourceId': self.data_source.id,
                'tableName': 'orders',
                'databaseName': 'sales',
                'comment': '订单表-更新',
            },
            format='json',
        )
        force_authenticate(update_request, user=self.user)
        update_response = update_view(update_request, pk=str(meta_table.id))

        asset.refresh_from_db()
        updated_comment = asset.comment

        delete_view = MetaTableViewSet.as_view({'delete': 'destroy'})
        delete_request = self.factory.delete(f'/data-api/dataasset/meta-table/{meta_table.id}')
        force_authenticate(delete_request, user=self.user)
        delete_response = delete_view(delete_request, pk=str(meta_table.id))

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(updated_comment, '订单表-更新')
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(DataAsset.objects.filter(legacy_meta_table_id=meta_table.id).exists())

    def test_meta_table_update_should_cascade_data_source_to_columns(self):
        second_data_source = DataSource.objects.create(
            name='warehouse_backup',
            db_type='mysql',
            host='127.0.0.2',
            port=3306,
            db_name='demo_backup',
            username='root',
            password='secret',
            params='{}',
            status='0',
        )
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        meta_column = MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='buyer_name',
            type='varchar',
            notnull=False,
            primary=False,
            comment='买家姓名',
        )
        sync_standard_asset_from_meta_table(meta_table, user=self.user)

        update_view = MetaTableViewSet.as_view({'put': 'update'})
        update_request = self.factory.put(
            f'/data-api/dataasset/meta-table/{meta_table.id}',
            {
                'id': meta_table.id,
                'dataSourceId': second_data_source.id,
                'tableName': 'orders',
                'databaseName': 'sales',
                'comment': '订单表',
            },
            format='json',
        )
        force_authenticate(update_request, user=self.user)
        response = update_view(update_request, pk=str(meta_table.id))

        meta_column.refresh_from_db()
        meta_table.refresh_from_db()
        asset = DataAsset.objects.get(legacy_meta_table_id=meta_table.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(meta_column.data_source_id, second_data_source.id)
        self.assertEqual(asset.namespace.data_source_id, second_data_source.id)

    @patch('apps.dataasset.views.sync_standard_asset_from_meta_table', side_effect=RuntimeError('sync failed'))
    def test_meta_table_write_should_roll_back_when_standard_sync_fails(self, mock_sync):
        view = MetaTableViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataasset/meta-table',
            {
                'dataSourceId': self.data_source.id,
                'tableName': 'orders',
                'databaseName': 'sales',
                'comment': '订单表',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 500)
        self.assertFalse(MetaTable.objects.filter(table_name='orders').exists())
        mock_sync.assert_called_once()

    def test_meta_column_write_should_sync_standard_asset_columns(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )

        create_view = MetaColumnViewSet.as_view({'post': 'create'})
        create_request = self.factory.post(
            '/data-api/dataasset/meta-column',
            {
                'tableId': meta_table.id,
                'dataSourceId': self.data_source.id,
                'columnIndex': 1,
                'columnName': 'buyer_name',
                'dataType': 'varchar',
                'isNullable': False,
                'defaultValue': '',
                'isPrimary': False,
                'columnComment': '买家姓名',
            },
            format='json',
        )
        force_authenticate(create_request, user=self.user)
        create_response = create_view(create_request)

        meta_column = MetaColumn.objects.get(table=meta_table, name='buyer_name')
        canonical_column = DataAssetColumn.objects.get(legacy_meta_column_id=meta_column.id)

        update_view = MetaColumnViewSet.as_view({'put': 'update'})
        update_request = self.factory.put(
            f'/data-api/dataasset/meta-column/{meta_column.id}',
            {
                'id': meta_column.id,
                'tableId': meta_table.id,
                'dataSourceId': self.data_source.id,
                'columnIndex': 1,
                'columnName': 'buyer_name',
                'dataType': 'string',
                'isNullable': True,
                'defaultValue': '',
                'isPrimary': False,
                'columnComment': '买家姓名-更新',
            },
            format='json',
        )
        force_authenticate(update_request, user=self.user)
        update_response = update_view(update_request, pk=str(meta_column.id))

        canonical_column.refresh_from_db()
        updated_type = canonical_column.data_type
        updated_nullable = canonical_column.is_nullable
        updated_comment = canonical_column.comment

        delete_view = MetaColumnViewSet.as_view({'delete': 'destroy'})
        delete_request = self.factory.delete(f'/data-api/dataasset/meta-column/{meta_column.id}')
        force_authenticate(delete_request, user=self.user)
        delete_response = delete_view(delete_request, pk=str(meta_column.id))

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(canonical_column.column_name, 'buyer_name')
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(updated_type, 'string')
        self.assertTrue(updated_nullable)
        self.assertEqual(updated_comment, '买家姓名-更新')
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(DataAssetColumn.objects.filter(legacy_meta_column_id=meta_column.id).exists())

    def test_meta_column_write_should_use_table_data_source_id(self):
        second_data_source = DataSource.objects.create(
            name='warehouse_backup',
            db_type='mysql',
            host='127.0.0.2',
            port=3306,
            db_name='demo_backup',
            username='root',
            password='secret',
            params='{}',
            status='0',
        )
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )

        create_view = MetaColumnViewSet.as_view({'post': 'create'})
        create_request = self.factory.post(
            '/data-api/dataasset/meta-column',
            {
                'tableId': meta_table.id,
                'dataSourceId': second_data_source.id,
                'columnIndex': 1,
                'columnName': 'buyer_name',
                'dataType': 'varchar',
                'isNullable': True,
                'defaultValue': '',
                'isPrimary': False,
                'columnComment': '买家姓名',
            },
            format='json',
        )
        force_authenticate(create_request, user=self.user)
        response = create_view(create_request)

        meta_column = MetaColumn.objects.get(table=meta_table, name='buyer_name')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(meta_column.data_source_id, meta_table.data_source_id)

    def test_meta_column_move_should_sync_old_and_new_tables(self):
        source_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        target_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders_archive',
            database='sales',
            comment='订单归档表',
        )
        meta_column = MetaColumn.objects.create(
            data_source=self.data_source,
            table=source_table,
            order=1,
            name='buyer_name',
            type='varchar',
            notnull=False,
            primary=False,
            comment='买家姓名',
        )
        source_asset = sync_standard_asset_from_meta_table(source_table, user=self.user)
        target_asset = sync_standard_asset_from_meta_table(target_table, user=self.user)

        update_view = MetaColumnViewSet.as_view({'put': 'update'})
        update_request = self.factory.put(
            f'/data-api/dataasset/meta-column/{meta_column.id}',
            {
                'id': meta_column.id,
                'tableId': target_table.id,
                'dataSourceId': self.data_source.id,
                'columnIndex': 1,
                'columnName': 'buyer_name',
                'dataType': 'varchar',
                'isNullable': True,
                'defaultValue': '',
                'isPrimary': False,
                'columnComment': '买家姓名',
            },
            format='json',
        )
        force_authenticate(update_request, user=self.user)
        response = update_view(update_request, pk=str(meta_column.id))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DataAssetColumn.objects.filter(asset=source_asset, legacy_meta_column_id=meta_column.id).exists())
        self.assertTrue(DataAssetColumn.objects.filter(asset=target_asset, legacy_meta_column_id=meta_column.id).exists())

    def test_data_asset_view_should_return_columns_in_detail(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
        )
        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)

        list_view = AssetNamespaceViewSet.as_view({'get': 'list'})
        list_request = self.factory.get('/data-api/dataasset/asset-namespace', {'dataSourceId': self.data_source.id})
        force_authenticate(list_request, user=self.user)
        list_response = list_view(list_request)

        detail_view = DataAssetViewSet.as_view({'get': 'retrieve'})
        detail_request = self.factory.get(f'/data-api/dataasset/asset/{asset.id}')
        force_authenticate(detail_request, user=self.user)
        detail_response = detail_view(detail_request, pk=str(asset.id))

        column_view = DataAssetColumnViewSet.as_view({'get': 'list'})
        column_request = self.factory.get('/data-api/dataasset/asset-column', {'assetId': asset.id})
        force_authenticate(column_request, user=self.user)
        column_response = column_view(column_request)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data['rows'][0]['displayName'], 'sales')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['data']['id'], asset.id)
        self.assertEqual(detail_response.data['data']['columns'][0]['columnName'], 'id')
        self.assertEqual(column_response.status_code, 200)
        self.assertEqual(column_response.data['rows'][0]['tableName'], 'orders')

    def test_data_asset_detail_should_hide_deleted_columns_and_keep_column_order(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='orders',
            database='sales',
            comment='订单表',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=2,
            name='buyer_name',
            type='varchar',
            notnull=False,
            primary=False,
            comment='买家姓名',
        )
        MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='id',
            type='bigint',
            notnull=True,
            primary=True,
            comment='主键',
        )
        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)
        DataAssetColumn.objects.filter(asset=asset, column_name='buyer_name').update(del_flag='1')

        detail_view = DataAssetViewSet.as_view({'get': 'retrieve'})
        detail_request = self.factory.get(f'/data-api/dataasset/asset/{asset.id}')
        force_authenticate(detail_request, user=self.user)
        detail_response = detail_view(detail_request, pk=str(asset.id))

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual([column['columnName'] for column in detail_response.data['data']['columns']], ['id'])

    def test_sync_standard_asset_should_copy_business_and_warehouse_metadata_fields(self):
        meta_table = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='dwd_orders',
            database='warehouse',
            comment='订单明细表',
            asset_category='warehouse',
            warehouse_layer='DWD',
            business_domain='交易',
            subject_area='订单域',
            owner='alice',
            steward='bob',
            lifecycle_status='active',
            security_level='sensitive',
            grain='订单明细',
        )
        meta_column = MetaColumn.objects.create(
            data_source=self.data_source,
            table=meta_table,
            order=1,
            name='pay_amount',
            type='decimal(18,2)',
            comment='支付金额',
            business_term='支付金额',
            warehouse_role='measure',
            security_level='restricted',
            standard_code='STD_PAY_AMOUNT',
            metric_unit='元',
        )

        asset = sync_standard_asset_from_meta_table(meta_table, user=self.user)
        column = DataAssetColumn.objects.get(asset=asset, legacy_meta_column_id=meta_column.id)

        self.assertEqual(asset.asset_category, 'warehouse')
        self.assertEqual(asset.warehouse_layer, 'DWD')
        self.assertEqual(asset.business_domain, '交易')
        self.assertEqual(asset.subject_area, '订单域')
        self.assertEqual(asset.owner, 'alice')
        self.assertEqual(asset.steward, 'bob')
        self.assertEqual(asset.lifecycle_status, 'active')
        self.assertEqual(asset.security_level, 'sensitive')
        self.assertEqual(asset.grain, '订单明细')
        self.assertEqual(column.business_term, '支付金额')
        self.assertEqual(column.warehouse_role, 'measure')
        self.assertEqual(column.security_level, 'restricted')
        self.assertEqual(column.standard_code, 'STD_PAY_AMOUNT')
        self.assertEqual(column.metric_unit, '元')

    def test_meta_table_view_should_support_business_and_warehouse_filters(self):
        source_meta = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='crm_customer',
            database='biz',
            comment='客户表',
            asset_category='business',
            business_domain='会员',
            owner='lucy',
        )
        warehouse_meta = MetaTable.objects.create(
            data_source=self.data_source,
            table_name='dws_order_summary',
            database='dw',
            comment='订单汇总表',
            asset_category='warehouse',
            warehouse_layer='DWS',
            business_domain='交易',
            owner='alice',
        )
        sync_standard_asset_from_meta_table(source_meta, user=self.user)
        sync_standard_asset_from_meta_table(warehouse_meta, user=self.user)

        view = MetaTableViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/dataasset/meta-table', {
            'assetCategory': 'warehouse',
            'warehouseLayer': 'DWS',
            'businessDomain': '交易',
            'owner': 'alice',
        })
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['tableName'], 'dws_order_summary')
        self.assertEqual(response.data['rows'][0]['assetCategory'], 'warehouse')
        self.assertEqual(response.data['rows'][0]['warehouseLayer'], 'DWS')
        self.assertEqual(response.data['rows'][0]['businessDomain'], '交易')

