from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.datasource.models import DataSource
from apps.datatask.models import Task, TaskInstance
from .models import DataDevDirectory, DataDevScript
from .models import DataDevScriptExecution, DataDevScriptVersion
from .views import ScriptViewSet
from .views import DataDevDirectoryViewSet


class ScriptVersionLogicTests(TestCase):
    def setUp(self):
        self.script = DataDevScript.objects.create(
            script_name='订单明细开发脚本',
            script_code='order_detail_sql',
            script_type='sql',
        )
        self.viewset = ScriptViewSet()

    def test_save_draft_twice_keeps_single_draft_version(self):
        self.viewset._create_version_snapshot(
            script=self.script,
            content='SELECT 1',
            change_log='初始化草稿',
            is_released=False,
            username='alice',
        )
        self.viewset._create_version_snapshot(
            script=self.script,
            content='SELECT 2',
            change_log='二次保存草稿',
            is_released=False,
            username='bob',
        )

        draft_versions = self.script.versions.filter(is_released=False)
        self.assertEqual(draft_versions.count(), 1)
        draft = draft_versions.first()
        self.assertEqual(draft.content, 'SELECT 2')
        self.assertTrue(draft.is_current)
        self.assertEqual(draft.create_by, 'alice')
        self.assertEqual(self.script.versions.filter(is_current=True).count(), 1)

        self.script.refresh_from_db()
        self.assertEqual(self.script.status, 'draft')

    def test_publish_multiple_times_creates_multiple_released_versions(self):
        self.viewset._create_version_snapshot(
            script=self.script,
            content='SELECT 1',
            change_log='发布v1',
            is_released=True,
            username='tester',
        )
        self.viewset._create_version_snapshot(
            script=self.script,
            content='SELECT 2',
            change_log='发布v2',
            is_released=True,
            username='tester',
        )

        released_versions = self.script.versions.filter(is_released=True).order_by('version_number')
        self.assertEqual(released_versions.count(), 2)
        self.assertEqual(list(released_versions.values_list('version_number', flat=True)), [1, 2])
        self.assertFalse(released_versions.first().is_current)
        self.assertTrue(released_versions.last().is_current)

        self.script.refresh_from_db()
        self.assertEqual(self.script.status, 'published')

    def test_publish_after_draft_keeps_single_draft_and_adds_released(self):
        self.viewset._create_version_snapshot(
            script=self.script,
            content='SELECT 1',
            change_log='保存草稿',
            is_released=False,
            username='tester',
        )
        self.viewset._create_version_snapshot(
            script=self.script,
            content='SELECT 1 /* published */',
            change_log='发布版本',
            is_released=True,
            username='tester',
        )

        self.assertEqual(self.script.versions.filter(is_released=False).count(), 1)
        self.assertEqual(self.script.versions.filter(is_released=True).count(), 1)

        current_version = self.script.versions.get(is_current=True)
        self.assertTrue(current_version.is_released)

        self.script.refresh_from_db()
        self.assertEqual(self.script.status, 'published')


class DataDevDirectoryInitTests(TestCase):
    def test_initdata_creates_default_datadev_directories(self):
        output = StringIO()

        call_command('initdata', force=True, stdout=output)

        directories = DataDevDirectory.objects.filter(del_flag='0').order_by('order_num')
        self.assertEqual(directories.count(), 4)
        self.assertEqual(
            list(directories.values_list('directory_code', flat=True)),
            ['ODS', 'DWD', 'DWS', 'ADS'],
        )
        self.assertEqual(
            list(directories.values_list('directory_name', flat=True)),
            ['ODS 贴源层', 'DWD 明细层', 'DWS 汇总层', 'ADS 应用层'],
        )

    def test_initdata_force_preserves_custom_directory(self):
        DataDevDirectory.objects.create(
            directory_name='自定义主题层',
            directory_code='CUSTOM',
            order_num=99,
            create_by='tester',
        )

        call_command('initdata', force=True, stdout=StringIO())

        self.assertTrue(
            DataDevDirectory.objects.filter(directory_code='CUSTOM', del_flag='0').exists()
        )
        self.assertEqual(DataDevDirectory.objects.filter(del_flag='0').count(), 5)

    def test_directory_save_updates_ancestors_for_child_node(self):
        root = DataDevDirectory.objects.create(
            directory_name='根目录',
            directory_code='ROOT',
            order_num=10,
            create_by='tester',
        )

        child = DataDevDirectory.objects.create(
            directory_name='子目录',
            directory_code='CHILD',
            parent_id=root.directory_id,
            order_num=11,
            create_by='tester',
        )

        self.assertEqual(child.ancestors, f'0,{root.directory_id}')

    def test_directory_cannot_use_nonexistent_parent(self):
        directory = DataDevDirectory(
            directory_name='非法子目录',
            directory_code='INVALID_PARENT',
            parent_id=999999,
            order_num=12,
            create_by='tester',
        )

        with self.assertRaises(ValidationError):
            directory.save()

    def test_directory_cannot_set_self_as_parent(self):
        directory = DataDevDirectory.objects.create(
            directory_name='自引用目录',
            directory_code='SELF_PARENT',
            order_num=13,
            create_by='tester',
        )
        directory.parent_id = directory.directory_id

        with self.assertRaises(ValidationError):
            directory.save()


class DataDevDirectoryViewLogicTests(TestCase):
    def setUp(self):
        self.root = DataDevDirectory.objects.create(
            directory_name='根目录',
            directory_code='ROOT_DIR',
            order_num=1,
            create_by='tester',
        )
        self.child = DataDevDirectory.objects.create(
            directory_name='子目录',
            directory_code='CHILD_DIR',
            parent_id=self.root.directory_id,
            order_num=2,
            create_by='tester',
        )
        self.grandchild = DataDevDirectory.objects.create(
            directory_name='孙目录',
            directory_code='GRANDCHILD_DIR',
            parent_id=self.child.directory_id,
            order_num=3,
            create_by='tester',
        )
        self.viewset = DataDevDirectoryViewSet()

    def test_validate_parent_assignment_rejects_descendant(self):
        with self.assertRaises(DRFValidationError):
            self.viewset._validate_parent_assignment(self.child, self.grandchild.directory_id)

    def test_build_tree_returns_nested_structure(self):
        DataDevScript.objects.create(
            script_name='测试脚本',
            script_code='catalog_script_001',
            script_type='sql',
            directory=self.child,
            create_by='tester',
        )
        tree = self.viewset._build_tree([self.root, self.child, self.grandchild], 0)
        root_node = tree[0]
        child_node = root_node['children'][0]
        self.assertEqual(root_node['directoryName'], '根目录')
        self.assertEqual(child_node['directoryName'], '子目录')
        self.assertEqual(child_node['children'][0]['directoryName'], '孙目录')


class ScriptExecutionTaskIntegrationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='script_runner', password='password123')
        self.datasource = DataSource.objects.create(
            name='测试MySQL',
            db_type='mysql',
            host='127.0.0.1',
            port=3306,
            db_name='demo',
            username='root',
            password='secret',
            create_by='tester',
        )
        self.script = DataDevScript.objects.create(
            script_name='门店营收汇总',
            script_code='store_revenue_summary',
            script_type='sql',
            datasource=self.datasource,
            owner='script_runner',
            create_by='script_runner',
        )
        self.version = DataDevScriptVersion.objects.create(
            script=self.script,
            version_number=1,
            content='SELECT 1 AS order_cnt',
            content_hash='hash',
            is_current=True,
            is_released=False,
            create_by='script_runner',
        )

    @patch('apps.datadev.views.get_executor')
    def test_execute_script_creates_task_and_task_instance(self, mock_get_executor):
        class _MockQueryExecutor:
            def execute_query(self, sql):
                return {'columns': ['order_cnt'], 'rows': [(1,)]}

            def close(self):
                return None

        mock_get_executor.return_value = _MockQueryExecutor()
        view = ScriptViewSet.as_view({'post': 'execute_script'})
        request = self.factory.post(
            f'/data-api/datadev/scripts/{self.script.pk}/execute',
            {'params': {'limit': 100}},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        task = Task.objects.get(source_module='datadev.script', source_record_id=self.script.pk)
        task_instance = TaskInstance.objects.get(task=task)
        execution = DataDevScriptExecution.objects.get(script=self.script)
        self.assertEqual(task.task_type, 'SQL_COMPUTE')
        self.assertEqual(task.task_config['sqlText'], 'SELECT 1 AS order_cnt')
        self.assertNotIn('runtimeParams', task.task_config)
        self.assertEqual(task_instance.status, 'success')
        self.assertEqual(task_instance.runtime_config['params'], {'limit': 100})
        self.assertEqual(execution.task_instance_id, task_instance.id)
        self.assertEqual(execution.execution_id, task_instance.instance_id)
