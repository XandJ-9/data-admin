from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Task
from .services import TaskService
from .views import TaskViewSet


class TaskServiceTests(TestCase):
    def test_upsert_source_task_reuses_existing_task(self):
        task, created = TaskService.upsert_source_task(
            task_name='订单汇总任务',
            task_type='SQL_COMPUTE',
            source_module='datadev.script',
            source_record_id=101,
            owner='alice',
            task_config={'scriptId': 101, 'sqlText': 'SELECT 1'},
            username='alice',
        )

        self.assertTrue(created)
        refreshed_task, refreshed_created = TaskService.upsert_source_task(
            task_name='订单汇总任务-新版',
            task_type='SQL_COMPUTE',
            source_module='datadev.script',
            source_record_id=101,
            owner='bob',
            task_config={'scriptId': 101, 'sqlText': 'SELECT 2'},
            username='bob',
        )

        self.assertFalse(refreshed_created)
        self.assertEqual(task.pk, refreshed_task.pk)
        self.assertEqual(refreshed_task.task_name, '订单汇总任务-新版')
        self.assertEqual(refreshed_task.owner, 'bob')
        self.assertEqual(refreshed_task.task_config['sqlText'], 'SELECT 2')

    def test_finalize_instance_updates_latest_status(self):
        task = Task.objects.create(
            task_name='订单同步任务',
            task_code='data_sync_orders_1',
            task_type='DATA_SYNC',
            create_by='tester',
        )

        instance = TaskService.create_task_instance(
            task=task,
            trigger_mode='manual',
            runtime_config={'batchSize': 1000},
            triggered_by='tester',
        )
        TaskService.mark_instance_running(instance, executor_type='datax')
        TaskService.finalize_instance(
            instance=instance,
            status='success',
            result_summary={'rowCount': 12},
        )

        task.refresh_from_db()
        instance.refresh_from_db()
        self.assertEqual(instance.status, 'success')
        self.assertEqual(instance.result_summary['rowCount'], 12)
        self.assertEqual(task.last_instance_status, 'success')
        self.assertIsNotNone(task.last_instance_at)


class TaskViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='task_tester', password='password123')
        Task.objects.create(
            task_name='订单贴源任务',
            task_code='data_sync_datadev_script_1',
            task_type='DATA_SYNC',
            owner='alice',
            create_by='alice',
        )
        Task.objects.create(
            task_name='订单汇总任务',
            task_code='sql_compute_datadev_script_2',
            task_type='SQL_COMPUTE',
            owner='bob',
            create_by='bob',
        )

    def test_task_list_supports_task_type_filter(self):
        view = TaskViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task', {'taskType': 'SQL_COMPUTE'})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['taskType'], 'SQL_COMPUTE')
