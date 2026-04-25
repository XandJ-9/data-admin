from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.datasource.models import DataSource, SourceTableSnapshot

from .models import DataIntegrationExecutionLog, DataIntegrationTask
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
        self.source_table = SourceTableSnapshot.objects.create(
            data_source=self.source_datasource,
            database_name='biz',
            table_name='order_info',
            create_by='tester',
        )

    def test_create_task_should_bind_source_table_snapshot(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataintegration/task',
            {
                'taskName': '订单贴源同步',
                'taskCode': 'sync_order_info',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.target_datasource.id,
                'sourceTableId': self.source_table.id,
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
        self.assertEqual(integration_task.source_table_snapshot_id, self.source_table.id)
        self.assertEqual(integration_task.source_table_name, 'order_info')

    def test_validate_task_should_reject_same_datasource(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'validate_task'})
        request = self.factory.post(
            '/data-api/dataintegration/task/validate',
            {
                'taskName': '非法同步任务',
                'taskCode': 'sync_invalid_same_ds',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.source_datasource.id,
                'sourceTableId': self.source_table.id,
                'targetTableName': 'ods_order_info',
                'executorType': 'mock',
                'scheduleType': 'manual',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 400)

    def test_source_tables_should_return_snapshot_options(self):
        view = DataIntegrationTaskViewSet.as_view({'get': 'source_tables'})
        request = self.factory.get('/data-api/dataintegration/task/source-tables', {'sourceDataSourceId': self.source_datasource.id})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['objectName'], 'order_info')

    @patch('apps.executors.mock.time.sleep', return_value=None)
    @patch('apps.executors.mock.random.random', return_value=0.1)
    @patch('apps.executors.mock.random.uniform', return_value=1)
    @patch('apps.executors.mock.random.randint', side_effect=[1200])
    def test_execute_task_should_create_success_log(self, mock_randint, mock_uniform, mock_random, mock_sleep):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_exec',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_table_snapshot=self.source_table,
            source_database_name='biz',
            source_table_name='order_info',
            target_schema_name='ods',
            target_table_name='ods_order_info',
            load_type='full',
            write_mode='overwrite',
            executor_type='mock',
            schedule_type='manual',
            create_by='tester',
        )
        view = DataIntegrationTaskViewSet.as_view({'post': 'execute_task'})
        request = self.factory.post(f'/data-api/dataintegration/task/{integration_task.id}/execute', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        execution_log = DataIntegrationExecutionLog.objects.get(task=integration_task)
        self.assertEqual(execution_log.status, 'success')
        self.assertEqual(execution_log.result_summary['total_rows'], 1200)

    def test_execution_detail_should_return_runtime_payload(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_log_detail',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            target_table_name='ods_order_info',
            create_by='tester',
        )
        execution_log = DataIntegrationExecutionLog.objects.create(
            task=integration_task,
            instance_id='instance-demo',
            status='success',
            runtime_config={'batchSize': 1000},
            result_summary={'total_rows': 200},
            create_by='tester',
        )
        view = IntegrationExecutionLogViewSet.as_view({'get': 'detail'})
        request = self.factory.get(f'/data-api/dataintegration/executionlog/{execution_log.id}/detail')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(execution_log.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['instanceId'], 'instance-demo')
        self.assertEqual(response.data['data']['runtimeConfig']['batchSize'], 1000)

