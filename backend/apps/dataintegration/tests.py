from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.datatask.models import Task, TaskInstance
from apps.datasource.models import DataSource

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
    def test_create_task_should_persist_source_table_name(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/dataintegration/task',
            {
                'taskName': '订单贴源同步',
                'taskCode': 'sync_order_info',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.target_datasource.id,
                'sourceDatabaseName': 'biz',
                'sourceTableName': 'order_info',
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
        platform_task = Task.objects.get(source_module='dataintegration.task', source_record_id=integration_task.id, del_flag='0')
        self.assertEqual(response.data['data']['taskId'], integration_task.id)
        self.assertEqual(integration_task.source_database_name, 'biz')
        self.assertEqual(integration_task.source_table_name, 'order_info')
        self.assertEqual(platform_task.task_type, 'DATA_SYNC')

    def test_validate_task_should_reject_same_datasource(self):
        view = DataIntegrationTaskViewSet.as_view({'post': 'validate_task'})
        request = self.factory.post(
            '/data-api/dataintegration/task/validate',
            {
                'taskName': '非法同步任务',
                'taskCode': 'sync_invalid_same_ds',
                'sourceDataSourceId': self.source_datasource.id,
                'targetDataSourceId': self.source_datasource.id,
                'sourceTableName': 'order_info',
                'targetTableName': 'ods_order_info',
                'executorType': 'mock',
                'scheduleType': 'manual',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 400)

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
        task_instance = TaskInstance.objects.get(task__source_module='dataintegration.task', task__source_record_id=integration_task.id)
        self.assertEqual(task_instance.status, 'success')
        self.assertEqual(task_instance.result_summary['total_rows'], 1200)
        self.assertEqual(response.data['data']['taskInstanceId'], task_instance.id)

    @patch('apps.executors.base.ExecutorFactory.create_executor')
    def test_execute_task_should_return_failure_payload_with_200(self, mock_create_executor):
        class _MockExecutor:
            def validate(self):
                return True, ''

            def execute(self):
                return {'status': 'failed', 'error_message': '模拟执行失败'}

        mock_create_executor.return_value = _MockExecutor()
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_exec_fail',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
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
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['data']['status'], 'failed')

    def test_execution_detail_should_return_runtime_payload(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_log_detail',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            target_table_name='ods_order_info',
            create_by='tester',
        )
        platform_task = Task.objects.create(
            task_name='订单贴源同步',
            task_code='data_sync_dataintegration_task_1',
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            create_by='tester',
        )
        task_instance = TaskInstance.objects.create(
            task=platform_task,
            instance_id='instance-demo',
            status='success',
            runtime_config={'batchSize': 1000},
            result_summary={'total_rows': 200},
            triggered_by='tester',
        )
        view = IntegrationExecutionLogViewSet.as_view({'get': 'execution_detail'})
        request = self.factory.get(f'/data-api/dataintegration/executionlog/{task_instance.id}/detail')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(task_instance.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['instanceId'], 'instance-demo')
        self.assertEqual(response.data['data']['runtimeConfig']['batchSize'], 1000)

    def test_executions_should_not_create_platform_task_on_read(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_read_only',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            target_table_name='ods_order_info',
            create_by='tester',
        )
        view = DataIntegrationTaskViewSet.as_view({'get': 'executions'})
        request = self.factory.get(f'/data-api/dataintegration/task/{integration_task.id}/executions')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        self.assertFalse(Task.objects.filter(source_module='dataintegration.task', source_record_id=integration_task.id).exists())

    def test_delete_task_should_soft_delete_platform_task(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_delete',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            target_table_name='ods_order_info',
            create_by='tester',
        )
        platform_task = Task.objects.create(
            task_name='订单贴源同步',
            task_code='data_sync_dataintegration_task_delete',
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            create_by='tester',
        )
        view = DataIntegrationTaskViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/dataintegration/task/{integration_task.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        integration_task.refresh_from_db()
        platform_task.refresh_from_db()
        self.assertEqual(integration_task.del_flag, '1')
        self.assertEqual(platform_task.del_flag, '1')

    def test_delete_source_datasource_should_unbind_integration_task(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_source_deleted',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_table_name='order_info',
            target_table_name='ods_order_info',
            create_by='tester',
        )

        self.source_datasource.delete()

        integration_task.refresh_from_db()
        self.assertIsNone(integration_task.source_datasource_id)
        self.assertEqual(integration_task.target_datasource_id, self.target_datasource.id)

    def test_execute_task_should_fail_when_source_datasource_deleted(self):
        integration_task = DataIntegrationTask.objects.create(
            task_name='订单贴源同步',
            task_code='sync_order_info_missing_source',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            source_table_name='order_info',
            target_table_name='ods_order_info',
            executor_type='mock',
            schedule_type='manual',
            create_by='tester',
        )
        self.source_datasource.delete()
        view = DataIntegrationTaskViewSet.as_view({'post': 'execute_task'})
        request = self.factory.post(f'/data-api/dataintegration/task/{integration_task.id}/execute', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(integration_task.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['msg'], '源数据源已删除或未配置，请重新绑定后再执行')
