from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.dataasset.models import AssetNamespace, DataAsset
from apps.datasource.models import DataSource
from apps.datatask.models import Task, TaskDependency, TaskInstance

from .models import DataIntegrationTask
from .views import DataIntegrationTaskViewSet, IntegrationExecutionLogViewSet


class DataIntegrationTaskViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='integration_tester', password='password123')
        self.source_datasource = DataSource.objects.create(
            name='业务MySQL',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='biz',
            username='root',
            password='secret',
            create_by='tester',
        )
        self.target_datasource = DataSource.objects.create(
            name='数仓MySQL',
            db_type='mysql',
            host='127.0.0.1',
            port=3307,
            db_name='warehouse',
            username='root',
            password='secret',
            create_by='tester',
        )
        namespace = AssetNamespace.objects.create(
            data_source=self.source_datasource,
            environment='prod',
            catalog_name='',
            schema_name='biz',
            namespace_key='1:prod::biz',
            display_name='biz',
            create_by='tester',
        )
        self.asset = DataAsset.objects.create(
            namespace=namespace,
            asset_type='table',
            object_name='order_info',
            qualified_name='biz.order_info',
            display_name='order_info',
            create_by='tester',
        )

    def test_create_task_should_sync_platform_task(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataintegration/task',
            {
                'taskName': '订单贴源同步',
                'taskCode': 'sync_order_info',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.target_datasource.id,
                'sourceAssetId': self.asset.id,
                'targetSchemaName': 'ods',
                'targetTableName': 'ods_order_info',
                'loadType': 'full',
                'writeMode': 'overwrite',
                'executorType': 'mock',
                'scheduleType': 'manual',
                'taskConfig': {'batchSize': 1000},
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        integration_task = DataIntegrationTask.objects.get(task_code='sync_order_info')
        self.assertEqual(response.data['data']['taskId'], integration_task.id)
        task = Task.objects.get(source_module='dataintegration.task', source_record_id=integration_task.id)
        self.assertEqual(task.task_type, 'DATA_SYNC')
        self.assertEqual(task.task_config['targetTableName'], 'ods_order_info')
        self.assertEqual(task.task_config['sourceTableName'], 'order_info')

    def test_create_task_should_reject_same_datasource(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataintegration/task',
            {
                'taskName': '非法同步任务',
                'taskCode': 'sync_invalid_same_ds',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.source_datasource.id,
                'sourceAssetId': self.asset.id,
                'targetTableName': 'ods_order_info',
                'executorType': 'mock',
                'scheduleType': 'manual',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)

    def test_create_task_should_sync_cron_expression_to_platform_task(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataintegration/task',
            {
                'taskName': '订单定时同步',
                'taskCode': 'sync_order_info_cron',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.target_datasource.id,
                'sourceAssetId': self.asset.id,
                'targetSchemaName': 'ods',
                'targetTableName': 'ods_order_info',
                'loadType': 'full',
                'writeMode': 'overwrite',
                'executorType': 'mock',
                'scheduleType': 'cron',
                'cronExpression': '0 1 * * *',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        integration_task = DataIntegrationTask.objects.get(task_code='sync_order_info_cron')
        task = Task.objects.get(source_module='dataintegration.task', source_record_id=integration_task.id)
        self.assertEqual(task.schedule_type, 'cron')
        self.assertEqual(task.cron_expression, '0 1 * * *')

    @patch('apps.dataintegration.views.DataIntegrationTaskViewSet._sync_platform_task', side_effect=RuntimeError('sync failed'))
    def test_create_task_should_rollback_when_platform_sync_fails(self, mock_sync_platform_task):
        view = DataIntegrationTaskViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataintegration/task',
            {
                'taskName': '事务回滚任务',
                'taskCode': 'sync_should_rollback',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.target_datasource.id,
                'sourceAssetId': self.asset.id,
                'targetSchemaName': 'ods',
                'targetTableName': 'ods_should_rollback',
                'loadType': 'full',
                'writeMode': 'overwrite',
                'executorType': 'mock',
                'scheduleType': 'manual',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 500)
        self.assertFalse(DataIntegrationTask.objects.filter(task_code='sync_should_rollback').exists())
        self.assertFalse(Task.objects.filter(source_module='dataintegration.task', source_record_id__isnull=False).exists())

    def test_destroy_task_should_soft_delete_dependencies_and_restore_downstream_schedule(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_destroy',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_asset=self.asset,
            target_schema_name='ods',
            target_table_name='ods_order_info',
            executor_type='mock',
            create_by='tester',
        )
        upstream_task = Task.objects.create(
            task_name='订单贴源同步',
            task_code='data_sync_destroy_source',
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            create_by='tester',
        )
        downstream_task = Task.objects.create(
            task_name='订单汇总任务',
            task_code='sql_compute_destroy_target',
            task_type='SQL_COMPUTE',
            schedule_type='dependency',
            create_by='tester',
        )
        dependency = TaskDependency.objects.create(
            upstream_task=upstream_task,
            downstream_task=downstream_task,
            create_by='tester',
        )
        view = DataIntegrationTaskViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/dataintegration/task/{integration_task.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        dependency.refresh_from_db()
        downstream_task.refresh_from_db()
        upstream_task.refresh_from_db()
        self.assertEqual(dependency.del_flag, '1')
        self.assertEqual(upstream_task.del_flag, '1')
        self.assertEqual(downstream_task.schedule_type, 'manual')

    @patch('apps.executors.mock.time.sleep', return_value=None)
    @patch('apps.executors.mock.random.random', return_value=0.1)
    @patch('apps.executors.mock.random.uniform', return_value=1)
    @patch('apps.executors.mock.random.randint', side_effect=[1200])
    def test_execute_task_should_create_success_instance(self, mock_randint, mock_uniform, mock_random, mock_sleep):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_exec',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_asset=self.asset,
            target_schema_name='ods',
            target_table_name='ods_order_info',
            load_type='full',
            write_mode='overwrite',
            executor_type='mock',
            schedule_type='manual',
            create_by='tester',
        )
        Task.objects.create(
            task_name='订单贴源同步',
            task_code='data_sync_dataintegration_task_1',
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            create_by='tester',
        )
        view = DataIntegrationTaskViewSet.as_view({'post': 'execute_task'})
        request = self.factory.post(f'/data-api/dataintegration/task/{integration_task.id}/execute', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        platform_task = Task.objects.get(source_module='dataintegration.task', source_record_id=integration_task.id)
        task_instance = TaskInstance.objects.get(task=platform_task)
        self.assertEqual(task_instance.status, 'success')
        self.assertEqual(task_instance.result_summary['total_rows'], 1200)

    @patch('apps.dataintegration.views.ExecutorFactory.create_executor', side_effect=RuntimeError('mock unavailable'))
    def test_execute_task_should_finalize_failed_instance_when_executor_errors(self, mock_create_executor):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_executor_fail',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_asset=self.asset,
            target_schema_name='ods',
            target_table_name='ods_order_info',
            load_type='full',
            write_mode='overwrite',
            executor_type='mock',
            schedule_type='manual',
            create_by='tester',
        )
        Task.objects.create(
            task_name='订单贴源同步',
            task_code='data_sync_dataintegration_task_executor_fail',
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            create_by='tester',
        )
        view = DataIntegrationTaskViewSet.as_view({'post': 'execute_task'})
        request = self.factory.post(f'/data-api/dataintegration/task/{integration_task.id}/execute', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        platform_task = Task.objects.get(source_module='dataintegration.task', source_record_id=integration_task.id)
        task_instance = TaskInstance.objects.get(task=platform_task)
        self.assertEqual(task_instance.status, 'failed')
        self.assertEqual(task_instance.error_message, 'mock unavailable')
        self.assertEqual(response.data['code'], 400)

    def test_execution_log_detail_should_return_instance(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_log',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_asset=self.asset,
            target_schema_name='ods',
            target_table_name='ods_order_info',
            executor_type='mock',
            create_by='tester',
        )
        platform_task = Task.objects.create(
            task_name='订单贴源同步',
            task_code='data_sync_dataintegration_task_log',
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            create_by='tester',
        )
        task_instance = TaskInstance.objects.create(
            task=platform_task,
            instance_id='integration-log-1',
            status='success',
            trigger_mode='manual',
            result_summary={'rowCount': 10},
            triggered_by='integration_tester',
        )
        view = IntegrationExecutionLogViewSet.as_view({'get': 'execution_detail'})
        request = self.factory.get(f'/data-api/dataintegration/executionlog/{task_instance.id}/detail')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(task_instance.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['integrationTaskId'], integration_task.id)
