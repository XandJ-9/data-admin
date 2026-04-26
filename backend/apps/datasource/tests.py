from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.common.encrypt import encrypt_password
from apps.dataasset.models import DataAsset, MetaTable
from apps.datatask.models import Task, TaskInstance
from apps.dataintegration.models import DataIntegrationTask

from .collectors import (
    _run_database_asset_sync,
    collect_table_to_asset,
    execute_database_collection_task,
    recover_stale_database_collection_instance,
)
from .models import DataSource, DataSourceCollectionTask
from .task_source import SOURCE_MODULE, ensure_collection_task, sync_source_task
from .views import DataSourceDiscoveryViewSet, DataSourceViewSet, _sanitize_db_error_message


class _FailingExecutor:
    def __init__(self, error):
        self.error = error
        self.closed = False

    def test_connection(self):
        raise self.error

    def close(self):
        self.closed = True


class _PassingExecutor:
    def __init__(self):
        self.closed = False

    def test_connection(self):
        return None

    def close(self):
        self.closed = True


class DataSourceSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')

    def test_sanitize_db_error_message_should_hide_driver_details(self):
        message = _sanitize_db_error_message(RuntimeError("Access denied for user 'root'@'127.0.0.1'"))

        self.assertEqual(message, '连接失败：认证失败，请检查用户名和密码')

    @patch('apps.datasource.views.get_executor')
    def test_test_by_body_should_return_sanitized_error_message(self, mock_get_executor):
        mock_get_executor.return_value = _FailingExecutor(
            RuntimeError("Access denied for user 'root'@'127.0.0.1' (using password: YES)")
        )
        view = DataSourceViewSet.as_view({'post': 'test_by_body'})
        request = self.factory.post(
            '/data-api/datasource/datasource/test',
            {
                'dataSourceName': 'test-source',
                'dbType': 'mysql',
                'host': '127.0.0.1',
                'port': 3306,
                'dbName': 'demo',
                'username': 'root',
                'password': 'secret',
                'params': '{}',
                'status': '0',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['msg'], '连接失败：认证失败，请检查用户名和密码')
        self.assertNotIn('Access denied', response.data['msg'])


class DataSourceConnectivityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')

    def create_datasource(self, **overrides):
        payload = {
            'name': 'demo-source',
            'db_type': 'mysql',
            'host': '127.0.0.1',
            'port': 3306,
            'db_name': 'demo',
            'username': 'root',
            'password': encrypt_password('secret'),
            'params': '{}',
            'status': '0',
        }
        payload.update(overrides)
        return DataSource.objects.create(**payload)

    @patch('apps.datasource.views.get_executor')
    def test_test_by_id_should_persist_connectivity_status(self, mock_get_executor):
        mock_get_executor.return_value = _PassingExecutor()
        datasource = self.create_datasource()
        view = DataSourceViewSet.as_view({'post': 'test_by_id'})
        request = self.factory.post(f'/data-api/datasource/datasource/{datasource.id}/test', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(datasource.id))

        datasource.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(datasource.connectivity_status, 'success')
        self.assertEqual(datasource.connectivity_message, '连接成功')
        self.assertIsNotNone(datasource.connectivity_tested_at)

    def test_update_should_reset_connectivity_status_when_connection_changes(self):
        tested_at = timezone.now()
        datasource = self.create_datasource(
            connectivity_status='success',
            connectivity_message='连接成功',
            connectivity_tested_at=tested_at,
        )
        view = DataSourceViewSet.as_view({'put': 'update'})
        request = self.factory.put(
            f'/data-api/datasource/datasource/{datasource.id}',
            {
                'dataSourceId': datasource.id,
                'dataSourceName': datasource.name,
                'dbType': datasource.db_type,
                'host': '192.168.1.10',
                'port': datasource.port,
                'dbName': datasource.db_name,
                'username': datasource.username,
                'password': '',
                'params': datasource.params,
                'status': datasource.status,
                'remark': datasource.remark,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(datasource.id))

        datasource.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(datasource.host, '192.168.1.10')
        self.assertEqual(datasource.connectivity_status, 'unknown')
        self.assertEqual(datasource.connectivity_message, '')
        self.assertIsNone(datasource.connectivity_tested_at)


class DataSourceDiscoveryTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')
        self.data_source = DataSource.objects.create(
            name='sqlite-demo',
            db_type='sqlite',
            db_name='/tmp/demo.sqlite3',
            status='0',
        )

    @patch('apps.datasource.views.discover_databases')
    def test_databases_should_return_fallback_rows(self, mock_discover_databases):
        mock_discover_databases.return_value = ['/tmp/demo.sqlite3']
        view = DataSourceDiscoveryViewSet.as_view({'post': 'databases'})
        request = self.factory.post('/data-api/datasource/collection/databases', {'dataSourceId': self.data_source.id}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data'], ['/tmp/demo.sqlite3'])

    @patch('apps.datasource.views.discover_tables')
    def test_tables_should_return_normalized_table_rows(self, mock_discover_tables):
        mock_discover_tables.return_value = [
            {
                'tableName': 'orders',
                'databaseName': 'demo',
                'tableType': 'BASE TABLE',
                'tableComment': '订单表',
                'comment': '订单表',
                'createTime': '',
                'updateTime': '',
            }
        ]
        view = DataSourceDiscoveryViewSet.as_view({'post': 'tables'})
        request = self.factory.post(
            '/data-api/datasource/collection/tables',
            {'dataSourceId': self.data_source.id, 'databaseName': 'demo'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['tableComment'], '订单表')
        self.assertEqual(response.data['rows'][0]['tableType'], 'BASE TABLE')

    @patch('apps.datasource.views.ensure_collection_task')
    @patch('apps.datasource.views.sync_source_task')
    @patch('apps.datasource.views.TaskService.execute_task')
    def test_collect_table_should_sync_metadata_and_standard_asset(self, mock_execute_task, mock_sync_source_task, mock_ensure_collection_task):
        mock_ensure_collection_task.return_value = Mock()
        mock_sync_source_task.return_value = Mock()
        mock_execute_task.return_value = {
            'ok': True,
            'msg': '采集成功，已同步到数据资产',
            'data': {
                'tableId': 9,
                'tableName': 'orders',
                'databaseName': 'sales',
                'dataSourceId': self.data_source.id,
                'taskInstanceId': 18,
                'executionId': 'exec_table_001',
                'status': 'success',
            },
        }
        view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_table'})
        request = self.factory.post(
            '/data-api/datasource/collection/collect-table',
            {'dataSourceId': self.data_source.id, 'databaseName': 'sales', 'tableName': 'orders'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['msg'], '采集成功，已同步到数据资产')
        self.assertEqual(response.data['data']['tableId'], 9)
        self.assertEqual(response.data['data']['taskInstanceId'], 18)
        mock_execute_task.assert_called_once()

    @patch(
        'apps.datasource.views.TaskService.execute_task',
        return_value={'ok': False, 'msg': '当前仅支持采集真实数据表，暂不支持对象类型: VIEW', 'data': None},
    )
    @patch('apps.datasource.views.sync_source_task')
    @patch('apps.datasource.views.ensure_collection_task')
    def test_collect_table_should_reject_non_table_objects(self, mock_ensure_collection_task, mock_sync_source_task, mock_execute_task):
        mock_ensure_collection_task.return_value = Mock()
        mock_sync_source_task.return_value = Mock()
        view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_table'})
        request = self.factory.post(
            '/data-api/datasource/collection/collect-table',
            {'dataSourceId': self.data_source.id, 'databaseName': 'demo', 'tableName': 'orders_view', 'tableType': 'TABLE'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['msg'], '当前仅支持采集真实数据表，暂不支持对象类型: VIEW')
        mock_execute_task.assert_called_once()

    @patch(
        'apps.datasource.views.TaskService.execute_task',
        return_value={'ok': False, 'msg': '表 orders 的字段采集结果为空，已中止同步', 'data': None},
    )
    @patch('apps.datasource.views.sync_source_task')
    @patch('apps.datasource.views.ensure_collection_task')
    def test_collect_table_should_preserve_business_validation_message(self, mock_ensure_collection_task, mock_sync_source_task, mock_execute_task):
        mock_ensure_collection_task.return_value = Mock()
        mock_sync_source_task.return_value = Mock()
        view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_table'})
        request = self.factory.post(
            '/data-api/datasource/collection/collect-table',
            {'dataSourceId': self.data_source.id, 'databaseName': 'demo', 'tableName': 'orders', 'tableType': 'TABLE'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['msg'], '表 orders 的字段采集结果为空，已中止同步')
        mock_execute_task.assert_called_once()

    @patch('apps.datasource.views.ensure_collection_task')
    @patch('apps.datasource.views.sync_source_task')
    @patch('apps.datasource.views.TaskService.execute_task')
    def test_collect_database_should_start_async_run(self, mock_execute_task, mock_sync_source_task, mock_ensure_collection_task):
        collection_task = DataSourceCollectionTask.objects.create(
            task_name='采集 sqlite-demo / demo',
            task_code='ds_collect_demo',
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='demo',
            create_by=self.user.username,
            update_by=self.user.username,
        )
        platform_task = Task.objects.create(
            task_name=collection_task.task_name,
            task_code='asset_collection_datasource_collection_1',
            task_type='ASSET_COLLECTION',
            source_module=SOURCE_MODULE,
            source_record_id=collection_task.id,
        )
        task_instance = TaskInstance.objects.create(
            task=platform_task,
            instance_id='run_demo_001',
            status='running',
            trigger_mode='manual',
            runtime_config={
                'dataSourceId': self.data_source.id,
                'dataSourceName': self.data_source.name,
                'collectionScope': 'database',
                'databaseName': 'demo',
                'tableName': '',
            },
            result_summary={
                'totalTables': 0,
                'successfulTables': 0,
                'failedTables': 0,
                'skippedTables': 0,
                'currentTable': '',
            },
            executor_type='asset_collection',
            triggered_by=self.user.username,
        )
        mock_ensure_collection_task.return_value = collection_task
        mock_sync_source_task.return_value = platform_task
        mock_execute_task.return_value = {'ok': True, 'msg': '整库异步采集已启动', 'data': task_instance}
        view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_database'})
        request = self.factory.post(
            '/data-api/datasource/collection/collect-database',
            {'dataSourceId': self.data_source.id, 'databaseName': 'demo'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['msg'], '整库异步采集已启动')
        self.assertEqual(response.data['data']['runId'], 'run_demo_001')
        self.assertEqual(response.data['data']['taskInstanceId'], task_instance.id)
        mock_execute_task.assert_called_once()

    def test_collect_database_run_should_return_run_status(self):
        collection_task = DataSourceCollectionTask.objects.create(
            task_name='采集 sqlite-demo / demo',
            task_code='ds_collect_demo_status',
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='demo',
            create_by=self.user.username,
            update_by=self.user.username,
        )
        platform_task = Task.objects.create(
            task_name=collection_task.task_name,
            task_code='asset_collection_datasource_collection_2',
            task_type='ASSET_COLLECTION',
            source_module=SOURCE_MODULE,
            source_record_id=collection_task.id,
        )
        task_instance = TaskInstance.objects.create(
            task=platform_task,
            instance_id='run_status_001',
            status='running',
            trigger_mode='manual',
            runtime_config={
                'dataSourceId': self.data_source.id,
                'dataSourceName': self.data_source.name,
                'collectionScope': 'database',
                'databaseName': 'demo',
                'tableName': '',
            },
            result_summary={
                'totalTables': 10,
                'successfulTables': 3,
                'failedTables': 1,
                'skippedTables': 2,
                'currentTable': 'orders',
            },
            executor_type='asset_collection',
            triggered_by=self.user.username,
        )
        view = DataSourceDiscoveryViewSet.as_view({'get': 'collect_database_run'})
        request = self.factory.get(f'/data-api/datasource/collection/collect-database/{task_instance.instance_id}')
        force_authenticate(request, user=self.user)

        response = view(request, run_id=task_instance.instance_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['data']['runId'], task_instance.instance_id)
        self.assertEqual(response.data['data']['currentTable'], 'orders')

    def test_recover_stale_database_collection_instance_should_mark_failed(self):
        collection_task = DataSourceCollectionTask.objects.create(
            task_name='采集 sqlite-demo / demo',
            task_code='ds_collect_demo_stale',
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='demo',
            create_by=self.user.username,
            update_by=self.user.username,
        )
        platform_task = Task.objects.create(
            task_name=collection_task.task_name,
            task_code='asset_collection_datasource_collection_3',
            task_type='ASSET_COLLECTION',
            source_module=SOURCE_MODULE,
            source_record_id=collection_task.id,
        )
        stale_heartbeat = (timezone.now() - timezone.timedelta(hours=1)).isoformat()
        task_instance = TaskInstance.objects.create(
            task=platform_task,
            instance_id='run_stale_001',
            status='running',
            trigger_mode='manual',
            runtime_config={
                'dataSourceId': self.data_source.id,
                'dataSourceName': self.data_source.name,
                'collectionScope': 'database',
                'databaseName': 'demo',
                'tableName': '',
                'heartbeatAt': stale_heartbeat,
            },
            result_summary={'totalTables': 0, 'successfulTables': 0, 'failedTables': 0, 'skippedTables': 0},
            executor_type='asset_collection',
            triggered_by=self.user.username,
            started_at=timezone.now() - timezone.timedelta(hours=1),
        )

        task_instance = recover_stale_database_collection_instance(task_instance)

        self.assertEqual(task_instance.status, 'failed')


class DataSourceCollectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='collector', password='password123')
        self.data_source = DataSource.objects.create(
            name='collector-source',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='demo',
            username='root',
            password=encrypt_password('secret'),
            params='{}',
            status='0',
        )

    @patch('apps.datasource.collectors.get_table_info')
    @patch('apps.dbutils.get_table_schema')
    @patch('apps.dbutils.get_table_info')
    def test_collect_table_to_asset_should_sync_metadata_and_standard_asset(
        self,
        mock_dbutils_get_table_info,
        mock_get_table_schema,
        mock_collectors_get_table_info,
    ):
        table_info = {
            'tableName': 'orders',
            'databaseName': 'sales',
            'tableType': 'BASE TABLE',
            'comment': '订单表',
        }
        mock_collectors_get_table_info.return_value = table_info
        mock_dbutils_get_table_info.return_value = table_info
        mock_get_table_schema.return_value = [
            {
                'order': 1,
                'name': 'id',
                'type': 'bigint',
                'notnull': True,
                'default': None,
                'primary': True,
                'comment': '主键',
            }
        ]

        meta_table, normalized_table = collect_table_to_asset(self.data_source, 'sales', 'orders', user=self.user)

        asset = DataAsset.objects.get(legacy_meta_table_id=meta_table.id)
        self.assertEqual(normalized_table['tableType'], 'BASE TABLE')
        self.assertEqual(meta_table.table_name, 'orders')
        self.assertEqual(asset.object_name, 'orders')

    def test_ensure_collection_task_should_preserve_existing_governance_fields(self):
        collection_task = ensure_collection_task(
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='sales',
            username='creator',
        )
        collection_task.owner = '治理负责人'
        collection_task.status = 'paused'
        collection_task.schedule_type = 'cron'
        collection_task.cron_expression = '0 0 * * *'
        collection_task.save()

        refreshed_task = ensure_collection_task(
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='sales',
            username='runner',
        )

        self.assertEqual(refreshed_task.owner, '治理负责人')
        self.assertEqual(refreshed_task.status, 'paused')
        self.assertEqual(refreshed_task.schedule_type, 'cron')
        self.assertEqual(refreshed_task.cron_expression, '0 0 * * *')

    @patch('apps.datasource.collectors.threading.Thread')
    def test_execute_database_collection_task_should_create_running_task_instance_and_start_worker(self, mock_thread):
        mock_worker = Mock()
        mock_thread.return_value = mock_worker
        collection_task = ensure_collection_task(
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='sales',
            username=self.user.username,
        )
        platform_task = sync_source_task(collection_task, username=self.user.username)

        result = execute_database_collection_task(platform_task, collection_task, username=self.user.username)

        task_instance = result['data']
        self.assertEqual(task_instance.status, 'running')
        self.assertEqual(task_instance.runtime_config['databaseName'], 'sales')
        mock_thread.assert_called_once()
        mock_worker.start.assert_called_once()

    def test_execute_database_collection_task_should_reject_duplicate_active_run(self):
        collection_task = ensure_collection_task(
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='sales',
            username=self.user.username,
        )
        platform_task = sync_source_task(collection_task, username=self.user.username)
        TaskInstance.objects.create(
            task=platform_task,
            instance_id='active_run',
            status='running',
            trigger_mode='manual',
        )

        result = execute_database_collection_task(platform_task, collection_task, username=self.user.username)

        self.assertFalse(result['ok'])
        self.assertEqual(result['msg'], '当前数据库已有进行中的整库采集任务')

    @patch('apps.datasource.collectors.collect_table_to_asset')
    @patch('apps.datasource.collectors.discover_tables')
    def test_run_database_asset_sync_should_update_progress(self, mock_discover_tables, mock_collect_table_to_asset):
        mock_discover_tables.return_value = [
            {'tableName': 'orders', 'tableType': 'BASE TABLE'},
            {'tableName': 'orders_view', 'tableType': 'VIEW'},
            {'tableName': 'users', 'tableType': 'TABLE'},
        ]
        collection_task = ensure_collection_task(
            data_source=self.data_source,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='sales',
            username=self.user.username,
        )
        platform_task = sync_source_task(collection_task, username=self.user.username)
        task_instance = TaskInstance.objects.create(
            task=platform_task,
            instance_id='run_worker_001',
            status='running',
            trigger_mode='manual',
            runtime_config={
                'dataSourceId': self.data_source.id,
                'dataSourceName': self.data_source.name,
                'collectionScope': 'database',
                'databaseName': 'sales',
                'tableName': '',
            },
        )

        _run_database_asset_sync(task_instance.id, collection_task.id)

        task_instance.refresh_from_db()
        self.assertEqual(task_instance.status, 'success')
        self.assertEqual(task_instance.result_summary['totalTables'], 2)
        self.assertEqual(task_instance.result_summary['successfulTables'], 2)
        self.assertEqual(task_instance.result_summary['failedTables'], 0)
        self.assertEqual(task_instance.result_summary['skippedTables'], 1)
        self.assertEqual(task_instance.result_summary['currentTable'], '')
        self.assertIsNotNone(task_instance.finished_at)


class DataSourceDeleteTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='password123')
        self.source_datasource = DataSource.objects.create(
            name='业务MySQL',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='biz',
            username='root',
            password=encrypt_password('secret'),
            status='0',
        )
        self.target_datasource = DataSource.objects.create(
            name='数仓MySQL',
            db_type='mysql',
            host='127.0.0.1',
            port=3307,
            db_name='warehouse',
            username='root',
            password=encrypt_password('secret'),
            status='0',
        )

    def test_destroy_should_allow_delete_when_datasource_is_referenced_by_integration_task(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_delete_source',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_table_name='order_info',
            target_table_name='ods_order_info',
            create_by='tester',
        )
        view = DataSourceViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/datasource/datasource/{self.source_datasource.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.source_datasource.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertFalse(DataSource.objects.filter(pk=self.source_datasource.id).exists())
        integration_task.refresh_from_db()
        self.assertIsNone(integration_task.source_datasource_id)

    def test_destroy_should_soft_delete_related_collection_tasks(self):
        collection_task = ensure_collection_task(
            data_source=self.source_datasource,
            collection_scope=DataSourceCollectionTask.CollectionScope.DATABASE,
            database_name='biz',
            username=self.user.username,
        )
        platform_task = sync_source_task(collection_task, username=self.user.username)
        view = DataSourceViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/datasource/datasource/{self.source_datasource.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.source_datasource.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        collection_task.refresh_from_db()
        platform_task.refresh_from_db()
        self.assertEqual(collection_task.del_flag, '1')
        self.assertEqual(platform_task.del_flag, '1')

    def test_destroy_should_allow_batch_delete_when_datasources_are_referenced_by_integration_task(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_batch_delete_source',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_table_name='order_info',
            target_table_name='ods_order_info',
            create_by='tester',
        )
        view = DataSourceViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(
            f'/data-api/datasource/datasource/{self.source_datasource.id},{self.target_datasource.id}'
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=f'{self.source_datasource.id},{self.target_datasource.id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertFalse(DataSource.objects.filter(pk=self.source_datasource.id).exists())
        self.assertFalse(DataSource.objects.filter(pk=self.target_datasource.id).exists())
        integration_task.refresh_from_db()
        self.assertIsNone(integration_task.source_datasource_id)
        self.assertIsNone(integration_task.target_datasource_id)
