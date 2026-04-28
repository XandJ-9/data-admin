from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from apps.datadev.task_source import sync_script_source_task
from apps.datadev.models import DataDevScript, DataDevScriptVersion
from apps.dataintegration.models import DataIntegrationTask
from apps.dataintegration.task_source import sync_source_task
from apps.datasource.models import DataSource
from .source_registry import SourceHandler
from .models import Task, TaskDependency, TaskInstance
from .scheduler import TaskSchedulerService
from .services import TaskService
from .views import TaskDependencyViewSet, TaskInstanceViewSet, TaskViewSet


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

    def test_upsert_source_task_preserves_dependency_schedule(self):
        upstream_task = Task.objects.create(
            task_name='上游同步任务',
            task_code='data_sync_upstream',
            task_type='DATA_SYNC',
            create_by='tester',
        )
        task = Task.objects.create(
            task_name='订单汇总任务',
            task_code='sql_compute_orders_maintained',
            task_type='SQL_COMPUTE',
            schedule_type='dependency',
            task_config={
                TaskService.SOURCE_SCHEDULE_TYPE_KEY: 'cron',
                TaskService.SOURCE_CRON_EXPRESSION_KEY: '0 1 * * *',
            },
            create_by='tester',
            source_module='datadev.script',
            source_record_id=999,
        )
        TaskDependency.objects.create(
            upstream_task=upstream_task,
            downstream_task=task,
            create_by='tester',
        )

        refreshed_task, created = TaskService.upsert_source_task(
            task_name='订单汇总任务',
            task_type='SQL_COMPUTE',
            source_module='datadev.script',
            source_record_id=999,
            schedule_type='cron',
            cron_expression='0 1 * * *',
            owner='tester',
            task_config={'scriptId': 999},
            username='tester',
        )

        self.assertFalse(created)
        self.assertEqual(refreshed_task.schedule_type, 'dependency')
        self.assertEqual(refreshed_task.cron_expression, '')
        self.assertEqual(
            refreshed_task.task_config[TaskService.SOURCE_SCHEDULE_TYPE_KEY],
            'cron',
        )


class TaskViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='task_tester', password='password123')
        self.source_datasource = DataSource.objects.create(
            name='源库',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='source_demo',
            username='root',
            password='secret',
            create_by='tester',
        )
        self.target_datasource = DataSource.objects.create(
            name='目标库',
            db_type='mysql',
            host='127.0.0.1',
            port=3307,
            db_name='target_demo',
            username='root',
            password='secret',
            create_by='tester',
        )
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
        self.integration_task = DataIntegrationTask.objects.create(
            task_name='用户同步任务',
            task_code='sync_user_profile',
            source_datasource=self.source_datasource,
            target_datasource=self.target_datasource,
            target_table_name='ods_user_profile',
            executor_type='mock',
            status='active',
            schedule_type='manual',
            owner='alice',
            remark='集成任务备注',
            create_by='alice',
        )
        self.platform_integration_task = sync_source_task(
            self.integration_task,
            username='alice',
        )
        self.script_datasource = DataSource.objects.create(
            name='开发库',
            db_type='mysql',
            host='127.0.0.1',
            port=3308,
            db_name='dev_demo',
            username='root',
            password='secret',
            create_by='tester',
        )
        self.script = DataDevScript.objects.create(
            script_name='订单汇总脚本',
            script_code='orders_summary_script',
            script_type='sql',
            datasource=self.script_datasource,
            owner='bob',
            create_by='bob',
        )
        self.script_version = DataDevScriptVersion.objects.create(
            script=self.script,
            version_number=1,
            content='SELECT 1 AS order_cnt',
            content_hash='hash',
            is_current=True,
            create_by='bob',
        )
        self.platform_script_task = sync_script_source_task(self.script, username='bob')

    def test_task_list_supports_task_type_filter(self):
        view = TaskViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task', {'taskType': 'SQL_COMPUTE'})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 2)
        self.assertTrue(all(row['taskType'] == 'SQL_COMPUTE' for row in response.data['rows']))

    def test_task_list_supports_task_code_keyword_filter(self):
        view = TaskViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task', {'taskName': 'sql_compute_datadev_script_2'})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['rows'][0]['taskCode'], 'sql_compute_datadev_script_2')

    def test_task_update_should_sync_integration_source_fields(self):
        view = TaskViewSet.as_view({'put': 'update'})
        request = self.factory.put(
            f'/data-api/datatask/task/{self.platform_integration_task.id}',
            {
                'status': 'paused',
                'scheduleType': 'cron',
                'cronExpression': '0 2 * * *',
                'owner': 'platform_owner',
                'remark': '统一任务中心已更新',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.platform_integration_task.id))

        self.assertEqual(response.status_code, 200)
        self.platform_integration_task.refresh_from_db()
        self.integration_task.refresh_from_db()
        self.assertEqual(self.platform_integration_task.status, 'paused')
        self.assertEqual(self.platform_integration_task.schedule_type, 'cron')
        self.assertEqual(self.platform_integration_task.cron_expression, '0 2 * * *')
        self.assertEqual(self.integration_task.status, 'paused')
        self.assertEqual(self.integration_task.schedule_type, 'cron')
        self.assertEqual(self.integration_task.cron_expression, '0 2 * * *')
        self.assertEqual(self.integration_task.owner, 'platform_owner')
        self.assertEqual(self.integration_task.remark, '统一任务中心已更新')

    @patch('apps.executors.base.ExecutorFactory.create_executor')
    def test_task_execute_should_dispatch_to_integration_source(self, mock_create_executor):
        class _MockExecutor:
            def validate(self):
                return True, ''

            def execute(self):
                return {'status': 'success', 'rowCount': 5}

        mock_create_executor.return_value = _MockExecutor()
        view = TaskViewSet.as_view({'post': 'execute_task'})
        request = self.factory.post(
            f'/data-api/datatask/task/{self.platform_integration_task.id}/execute',
            {},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.platform_integration_task.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.platform_integration_task.refresh_from_db()
        self.assertEqual(self.platform_integration_task.last_instance_status, 'success')

    @patch('apps.dbutils.factory.get_executor')
    def test_task_execute_should_dispatch_to_script_source(self, mock_get_executor):
        class _MockQueryExecutor:
            def execute_query(self, sql):
                return {'columns': ['order_cnt'], 'rows': [(1,)]}

            def close(self):
                return None

        mock_get_executor.return_value = _MockQueryExecutor()
        view = TaskViewSet.as_view({'post': 'execute_task'})
        request = self.factory.post(
            f'/data-api/datatask/task/{self.platform_script_task.id}/execute',
            {},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.platform_script_task.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        self.assertTrue(
            TaskInstance.objects.filter(task=self.platform_script_task, status='success').exists()
        )

    def test_task_instances_should_not_normalize_instances_on_detail_route(self):
        custom_task = Task.objects.create(
            task_name='详情归一化任务',
            task_code='custom_task_instances_route',
            task_type='SQL_COMPUTE',
            source_module='fake.module',
            source_record_id=2,
            create_by='tester',
        )
        custom_instance = TaskInstance.objects.create(
            task=custom_task,
            instance_id='custom-route-001',
            status='running',
            trigger_mode='manual',
            scheduled_at=timezone.now(),
        )

        view = TaskViewSet.as_view({'get': 'instances'})
        request = self.factory.get(f'/data-api/datatask/task/{custom_task.id}/instances')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(custom_task.id))

        custom_instance.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data'][0]['status'], 'running')
        self.assertEqual(custom_instance.error_message, '')

class TaskDependencyViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='dag_tester', password='password123')
        self.sync_task = Task.objects.create(
            task_name='订单同步任务',
            task_code='data_sync_orders',
            task_type='DATA_SYNC',
            schedule_type='manual',
            create_by='tester',
        )
        self.compute_task = Task.objects.create(
            task_name='订单汇总任务',
            task_code='sql_compute_orders',
            task_type='SQL_COMPUTE',
            schedule_type='manual',
            create_by='tester',
        )
        self.ads_task = Task.objects.create(
            task_name='订单应用任务',
            task_code='sql_compute_orders_ads',
            task_type='SQL_COMPUTE',
            schedule_type='manual',
            create_by='tester',
        )

    def test_create_dependency_updates_downstream_schedule_type(self):
        view = TaskDependencyViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/datatask/task-dependency',
            {
                'upstreamTaskId': self.sync_task.id,
                'downstreamTaskId': self.compute_task.id,
                'triggerCondition': 'SUCCESS',
                'lagSeconds': 60,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.compute_task.refresh_from_db()
        self.assertEqual(self.compute_task.schedule_type, 'dependency')
        self.assertEqual(TaskDependency.objects.filter(del_flag='0').count(), 1)

    def test_create_dependency_rejects_cycle(self):
        TaskDependency.objects.create(
            upstream_task=self.sync_task,
            downstream_task=self.compute_task,
            create_by='tester',
        )
        TaskDependency.objects.create(
            upstream_task=self.compute_task,
            downstream_task=self.ads_task,
            create_by='tester',
        )

        view = TaskDependencyViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/datatask/task-dependency',
            {
                'upstreamTaskId': self.ads_task.id,
                'downstreamTaskId': self.sync_task.id,
                'triggerCondition': 'SUCCESS',
                'lagSeconds': 0,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertIn('环路', str(response.data.get('msg') or response.data.get('message')))

    def test_delete_last_dependency_restores_manual_schedule(self):
        dependency = TaskDependency.objects.create(
            upstream_task=self.sync_task,
            downstream_task=self.compute_task,
            create_by='tester',
        )
        self.compute_task.schedule_type = 'dependency'
        self.compute_task.save(update_fields=['schedule_type'])

        view = TaskDependencyViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/datatask/task-dependency/{dependency.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(dependency.id))

        self.assertEqual(response.status_code, 200)
        dependency.refresh_from_db()
        self.compute_task.refresh_from_db()
        self.assertEqual(dependency.del_flag, '1')
        self.assertEqual(self.compute_task.schedule_type, 'manual')

    def test_delete_last_dependency_restores_source_cron_schedule(self):
        dependency = TaskDependency.objects.create(
            upstream_task=self.sync_task,
            downstream_task=self.compute_task,
            create_by='tester',
        )
        self.compute_task.schedule_type = 'dependency'
        self.compute_task.task_config = {
            TaskService.SOURCE_SCHEDULE_TYPE_KEY: 'cron',
            TaskService.SOURCE_CRON_EXPRESSION_KEY: '0 2 * * *',
        }
        self.compute_task.save(update_fields=['schedule_type', 'task_config'])

        view = TaskDependencyViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/data-api/datatask/task-dependency/{dependency.id}')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(dependency.id))

        self.assertEqual(response.status_code, 200)
        self.compute_task.refresh_from_db()
        self.assertEqual(self.compute_task.schedule_type, 'cron')
        self.assertEqual(self.compute_task.cron_expression, '0 2 * * *')

    def test_create_dependency_backfills_existing_schedule_metadata(self):
        self.compute_task.schedule_type = 'cron'
        self.compute_task.cron_expression = '0 3 * * *'
        self.compute_task.task_config = {'scriptId': 2}
        self.compute_task.save(update_fields=['schedule_type', 'cron_expression', 'task_config'])

        view = TaskDependencyViewSet.as_view({'post': 'create'})
        request = self.factory.post(
            '/data-api/datatask/task-dependency',
            {
                'upstreamTaskId': self.sync_task.id,
                'downstreamTaskId': self.compute_task.id,
                'triggerCondition': 'SUCCESS',
                'lagSeconds': 0,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.compute_task.refresh_from_db()
        self.assertEqual(
            self.compute_task.task_config[TaskService.SOURCE_SCHEDULE_TYPE_KEY],
            'cron',
        )
        self.assertEqual(
            self.compute_task.task_config[TaskService.SOURCE_CRON_EXPRESSION_KEY],
            '0 3 * * *',
        )



class TaskSchedulerServiceTests(TestCase):
    def test_run_cycle_dispatches_due_cron_task(self):
        now = timezone.now().replace(second=0, microsecond=0)
        task = Task.objects.create(
            task_name='定时同步任务',
            task_code='cron_sync_orders',
            task_type='DATA_SYNC',
            status='active',
            schedule_type='cron',
            cron_expression=f'{now.minute} {now.hour} * * *',
            create_by='tester',
        )

        with patch('apps.datatask.scheduler.TaskService.execute_task', return_value={'ok': True, 'msg': '执行成功', 'data': {'executionId': 'cron-run'}}) as execute_task:
            summary = TaskSchedulerService.run_cycle(now=now)

        execute_task.assert_called_once()
        _, kwargs = execute_task.call_args
        self.assertEqual(kwargs['trigger_mode'], 'schedule')
        self.assertEqual(summary['cron']['dispatchedTaskIds'], [task.id])

    def test_run_cycle_skips_cron_task_when_same_minute_already_dispatched(self):
        now = timezone.now().replace(second=0, microsecond=0)
        task = Task.objects.create(
            task_name='定时同步任务',
            task_code='cron_sync_orders_once',
            task_type='DATA_SYNC',
            status='active',
            schedule_type='cron',
            cron_expression=f'{now.minute} {now.hour} * * *',
            create_by='tester',
        )
        TaskInstance.objects.create(
            task=task,
            instance_id='existing-schedule-instance',
            status='success',
            trigger_mode='schedule',
            scheduled_at=now,
        )

        with patch('apps.datatask.scheduler.TaskService.execute_task') as execute_task:
            summary = TaskSchedulerService.run_cycle(now=now)

        execute_task.assert_not_called()
        self.assertEqual(summary['cron']['skippedTaskIds'], [task.id])

    def test_run_cycle_dispatches_dependency_task_after_all_upstreams_succeed(self):
        now = timezone.now().replace(second=0, microsecond=0)
        upstream_a = Task.objects.create(
            task_name='ODS 订单同步',
            task_code='dep_upstream_a',
            task_type='DATA_SYNC',
            status='active',
            create_by='tester',
        )
        upstream_b = Task.objects.create(
            task_name='ODS 门店同步',
            task_code='dep_upstream_b',
            task_type='DATA_SYNC',
            status='active',
            create_by='tester',
        )
        downstream = Task.objects.create(
            task_name='DWS 汇总任务',
            task_code='dep_downstream',
            task_type='SQL_COMPUTE',
            status='active',
            schedule_type='dependency',
            create_by='tester',
        )
        dep_a = TaskDependency.objects.create(upstream_task=upstream_a, downstream_task=downstream, lag_seconds=0, create_by='tester')
        dep_b = TaskDependency.objects.create(upstream_task=upstream_b, downstream_task=downstream, lag_seconds=0, create_by='tester')
        TaskInstance.objects.create(
            task=upstream_a,
            instance_id='upstream-a-success',
            status='success',
            trigger_mode='manual',
            scheduled_at=now,
            started_at=now,
            finished_at=now,
        )
        TaskInstance.objects.create(
            task=upstream_b,
            instance_id='upstream-b-success',
            status='success',
            trigger_mode='manual',
            scheduled_at=now,
            started_at=now,
            finished_at=now,
        )

        with patch('apps.datatask.scheduler.TaskService.execute_task', return_value={'ok': True, 'msg': '执行成功', 'data': {'executionId': 'dependency-run'}}) as execute_task:
            summary = TaskSchedulerService.run_cycle(now=now)

        execute_task.assert_called_once()
        _, kwargs = execute_task.call_args
        self.assertEqual(kwargs['trigger_mode'], 'dependency')
        self.assertEqual(kwargs['runtime_config']['dependencyUpstreams'][0]['dependencyId'], dep_a.id)
        self.assertEqual(kwargs['runtime_config']['dependencyUpstreams'][1]['dependencyId'], dep_b.id)
        self.assertEqual(summary['dependency']['dispatchedTaskIds'], [downstream.id])

    def test_run_cycle_skips_dependency_task_when_same_fingerprint_exists(self):
        now = timezone.now().replace(second=0, microsecond=0)
        upstream = Task.objects.create(
            task_name='ODS 用户同步',
            task_code='dep_upstream_single',
            task_type='DATA_SYNC',
            status='active',
            create_by='tester',
        )
        downstream = Task.objects.create(
            task_name='ADS 用户指标',
            task_code='dep_downstream_single',
            task_type='SQL_COMPUTE',
            status='active',
            schedule_type='dependency',
            create_by='tester',
        )
        dependency = TaskDependency.objects.create(upstream_task=upstream, downstream_task=downstream, lag_seconds=0, create_by='tester')
        upstream_instance = TaskInstance.objects.create(
            task=upstream,
            instance_id='upstream-single-success',
            status='success',
            trigger_mode='manual',
            scheduled_at=now,
            started_at=now,
            finished_at=now,
        )
        fingerprint = TaskSchedulerService._build_dependency_fingerprint([(dependency, upstream_instance)])
        TaskInstance.objects.create(
            task=downstream,
            instance_id='downstream-existing',
            status='success',
            trigger_mode='dependency',
            scheduled_at=now,
            runtime_config={'dependencyFingerprint': fingerprint},
        )

        with patch('apps.datatask.scheduler.TaskService.execute_task') as execute_task:
            summary = TaskSchedulerService.run_cycle(now=now)

        execute_task.assert_not_called()
        self.assertEqual(summary['dependency']['skippedTaskIds'], [downstream.id])

    def test_run_cycle_should_cleanup_stale_datasource_instances(self):
        stale_task = Task.objects.create(
            task_name='采集 stale 库',
            task_code='cleanup_stale_datasource_collection',
            task_type='ASSET_COLLECTION',
            source_module='datasource.collection',
            source_record_id=88,
            create_by='tester',
        )
        stale_instance = TaskInstance.objects.create(
            task=stale_task,
            instance_id='cleanup-stale-instance',
            status='running',
            trigger_mode='manual',
            runtime_config={
                'collectionScope': 'database',
                'heartbeatAt': (timezone.now() - timedelta(minutes=31)).isoformat(),
            },
            started_at=timezone.now() - timedelta(minutes=31),
        )

        summary = TaskSchedulerService.run_cycle(now=timezone.now())

        stale_instance.refresh_from_db()
        self.assertEqual(stale_instance.status, 'failed')
        self.assertEqual(stale_instance.error_message, '采集执行器已失联，请重新触发')
        self.assertIn('cleanup', summary)
        self.assertEqual(summary['cleanup']['recoveredInstanceIds'], ['cleanup-stale-instance'])


class TaskInstanceViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='instance_tester', password='password123')
        self.task = Task.objects.create(
            task_name='采集 源库 / sales',
            task_code='asset_collection_datasource_collection_8',
            task_type='ASSET_COLLECTION',
            source_module='datasource.collection',
            source_record_id=8,
            create_by='tester',
        )
        self.instance = TaskInstance.objects.create(
            task=self.task,
            instance_id='asset-run-001',
            status='failed',
            trigger_mode='manual',
            runtime_config={
                'dataSourceId': 11,
                'dataSourceName': '源库',
                'collectionScope': 'database',
                'databaseName': 'sales',
            },
            result_summary={'totalTables': 5, 'successfulTables': 3, 'failedTables': 2},
            error_message='orders 表采集失败',
            triggered_by='instance_tester',
            executor_type='asset_collection',
            scheduled_at=timezone.now(),
        )

    def test_task_instance_list_should_include_task_source_fields(self):
        view = TaskInstanceViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task-instance')
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        row = response.data['rows'][0]
        self.assertEqual(row['taskType'], 'ASSET_COLLECTION')
        self.assertEqual(row['sourceModule'], 'datasource.collection')
        self.assertEqual(row['sourceRecordId'], 8)
        self.assertEqual(row['errorMessage'], 'orders 表采集失败')

    def test_task_instance_list_should_not_recover_stale_datasource_collection_instance_on_get(self):
        stale_task = Task.objects.create(
            task_name='采集 源库 / stale',
            task_code='asset_collection_datasource_collection_9',
            task_type='ASSET_COLLECTION',
            source_module='datasource.collection',
            source_record_id=9,
            create_by='tester',
        )
        stale_instance = TaskInstance.objects.create(
            task=stale_task,
            instance_id='asset-run-stale',
            status='running',
            trigger_mode='manual',
            runtime_config={
                'collectionScope': 'database',
                'heartbeatAt': (timezone.now() - timedelta(minutes=31)).isoformat(),
            },
            scheduled_at=timezone.now() - timedelta(minutes=31),
        )

        view = TaskInstanceViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task-instance', {'taskId': stale_task.id})
        force_authenticate(request, user=self.user)

        response = view(request)

        stale_instance.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rows'][0]['status'], 'running')
        self.assertEqual(stale_instance.status, 'running')
        self.assertEqual(stale_instance.error_message, '')

    def test_task_instance_list_should_not_consult_source_handler_for_stale_recovery(self):
        stale_task = Task.objects.create(
            task_name='采集 源库 / stale-registry',
            task_code='asset_collection_datasource_collection_registry',
            task_type='ASSET_COLLECTION',
            source_module='datasource.collection',
            source_record_id=10,
            create_by='tester',
        )
        stale_instance = TaskInstance.objects.create(
            task=stale_task,
            instance_id='asset-run-registry',
            status='running',
            trigger_mode='manual',
            runtime_config={'collectionScope': 'database'},
            scheduled_at=timezone.now() - timedelta(minutes=31),
        )

        view = TaskInstanceViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task-instance', {'taskId': stale_task.id})
        force_authenticate(request, user=self.user)

        response = view(request)

        stale_instance.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rows'][0]['status'], 'running')
        self.assertEqual(stale_instance.status, 'running')
        self.assertEqual(stale_instance.error_message, '')

    def test_task_instance_list_should_not_normalize_non_datasource_instances_via_handler(self):
        custom_task = Task.objects.create(
            task_name='自定义任务',
            task_code='custom_module_task_1',
            task_type='SQL_COMPUTE',
            source_module='fake.module',
            source_record_id=1,
            create_by='tester',
        )
        custom_instance = TaskInstance.objects.create(
            task=custom_task,
            instance_id='custom-run-001',
            status='running',
            trigger_mode='manual',
            scheduled_at=timezone.now(),
        )

        view = TaskInstanceViewSet.as_view({'get': 'list'})
        request = self.factory.get('/data-api/datatask/task-instance', {'taskId': custom_task.id})
        force_authenticate(request, user=self.user)

        response = view(request)

        custom_instance.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rows'][0]['status'], 'running')
        self.assertEqual(custom_instance.error_message, '')
