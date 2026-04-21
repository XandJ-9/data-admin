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
from apps.datatask.services import TaskService
from .models import DataDevDirectory, DataDevModel, DataDevModelField, DataDevScript
from .models import DataDevScriptExecution, DataDevScriptVersion
from .views import DataDevDirectoryViewSet, DataModelViewSet, ScriptViewSet


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

        self.assertTrue(DataDevDirectory.objects.filter(directory_code='CUSTOM', del_flag='0').exists())
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
        tree = self.viewset._build_tree([self.root, self.child, self.grandchild], 0)
        root_node = tree[0]
        child_node = root_node['children'][0]
        self.assertEqual(root_node['directoryName'], '根目录')
        self.assertEqual(child_node['directoryName'], '子目录')
        self.assertEqual(child_node['children'][0]['directoryName'], '孙目录')
        self.assertEqual(child_node['scriptCount'], 0)


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
        self.target_model = DataDevModel.objects.create(
            model_name='门店营收汇总模型',
            model_code='dws_store_revenue',
            layer='DWS',
            table_name='dws_store_revenue',
            schema_name='dws',
            table_comment='门店营收汇总模型',
            engine_type='spark',
            owner='model_owner',
            create_by='tester',
            update_by='tester',
        )
        DataDevModelField.objects.create(
            model=self.target_model,
            field_name='store_id',
            field_type='STRING',
            field_comment='门店ID',
            is_nullable=False,
            ordinal_position=1,
            create_by='tester',
            update_by='tester',
        )
        self.script = DataDevScript.objects.create(
            script_name='门店营收汇总',
            script_code='store_revenue_summary',
            script_type='sql',
            script_role='transform',
            engine_type='spark',
            datasource=self.datasource,
            target_model=self.target_model,
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

    @patch('apps.dbutils.factory.get_executor')
    def test_execute_script_without_publish_should_not_create_platform_task(self, mock_get_executor):
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
        self.assertFalse(Task.objects.filter(source_module='datadev.script', source_record_id=self.script.pk, del_flag='0').exists())
        self.assertEqual(TaskInstance.objects.count(), 0)
        execution = DataDevScriptExecution.objects.get(script=self.script)
        self.assertIsNone(execution.task_instance_id)
        self.assertEqual(execution.executor_type, 'mysql')

    def test_execute_script_without_datasource_should_run_in_mvp_mode(self):
        self.script.datasource = None
        self.script.engine_type = 'mvp'
        self.script.save(update_fields=['datasource', 'engine_type'])
        view = ScriptViewSet.as_view({'post': 'execute_script'})
        request = self.factory.post(
            f'/data-api/datadev/scripts/{self.script.pk}/execute',
            {},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(source_module='datadev.script', source_record_id=self.script.pk, del_flag='0').exists())
        execution = DataDevScriptExecution.objects.get(script=self.script)
        self.assertIsNone(execution.task_instance_id)
        self.assertEqual(execution.executor_type, 'mvp')
        self.assertTrue(execution.result_summary['designOnly'])
        self.assertTrue(response.data['data']['designOnly'])

    @patch('apps.executors.base.ExecutorFactory.create_executor')
    def test_execute_sql_script_without_datasource_should_use_script_engine(self, mock_create_executor):
        self.script.datasource = None
        self.script.engine_type = 'spark'
        self.script.save(update_fields=['datasource', 'engine_type'])
        mock_create_executor.return_value = type('SparkExecutorStub', (), {
            'validate': staticmethod(lambda: (True, '')),
            'execute': staticmethod(lambda: {
                'status': 'success',
                'columns': ['order_cnt'],
                'rows': [{'order_cnt': '1'}],
                'duration_seconds': 1,
                'raw_output': 'order_cnt\n1',
            }),
        })()
        view = ScriptViewSet.as_view({'post': 'execute_script'})
        request = self.factory.post(
            f'/data-api/datadev/scripts/{self.script.pk}/execute',
            {},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        execution = DataDevScriptExecution.objects.get(script=self.script)
        self.assertEqual(execution.executor_type, 'spark')
        self.assertFalse(response.data['data']['designOnly'])
        self.assertIsNone(execution.task_instance_id)

    @patch('apps.executors.base.ExecutorFactory.create_executor')
    def test_execute_script_without_datasource_should_support_modeling_execution(self, mock_create_executor):
        self.script.datasource = None
        self.script.save(update_fields=['datasource'])
        self.version.content = "CREATE TABLE dwd_order_summary (order_id STRING) COMMENT '订单汇总'"
        self.version.save(update_fields=['content'])
        mock_create_executor.return_value = type('SparkExecutorStub', (), {
            'validate': staticmethod(lambda: (True, '')),
            'execute': staticmethod(lambda: {
                'status': 'success',
                'columns': [],
                'rows': [],
                'duration_seconds': 1,
                'raw_output': 'OK',
            }),
        })()
        view = ScriptViewSet.as_view({'post': 'execute_script'})
        request = self.factory.post(
            f'/data-api/datadev/scripts/{self.script.pk}/execute',
            {'params': {
                'executionMode': 'modeling',
                'engine': 'spark',
                'targetLayer': 'DWD',
                'targetTableName': 'dwd_order_summary',
                'tableComment': '订单汇总',
                'owner': 'model_owner',
            }},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        execution = DataDevScriptExecution.objects.get(script=self.script)
        self.assertEqual(execution.executor_type, 'spark')
        self.assertEqual(execution.result_summary['executionMode'], 'modeling')
        self.assertEqual(response.data['data']['executionMode'], 'modeling')
        self.assertEqual(response.data['data']['rows'][0]['targetTableName'], 'dwd_order_summary')
        self.assertIsNone(execution.task_instance_id)

    def test_execute_script_modeling_should_require_governance_fields(self):
        self.script.datasource = None
        self.script.save(update_fields=['datasource'])
        self.version.content = 'CREATE TABLE dwd_order_summary (order_id STRING)'
        self.version.save(update_fields=['content'])
        view = ScriptViewSet.as_view({'post': 'execute_script'})
        request = self.factory.post(
            f'/data-api/datadev/scripts/{self.script.pk}/execute',
            {'params': {'executionMode': 'modeling', 'engine': 'spark'}},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertIn('层级', response.data['msg'])

    @patch('apps.executors.base.ExecutorFactory.create_executor')
    def test_execute_script_should_use_spark_executor_for_spark_datasource(self, mock_create_executor):
        self.datasource.db_type = 'spark'
        self.datasource.save(update_fields=['db_type'])
        mock_create_executor.return_value = type('SparkExecutorStub', (), {
            'validate': staticmethod(lambda: (True, '')),
            'execute': staticmethod(lambda: {
                'status': 'success',
                'columns': ['order_cnt'],
                'rows': [{'order_cnt': '1'}],
                'duration_seconds': 2,
                'raw_output': 'order_cnt\n1',
            }),
        })()
        view = ScriptViewSet.as_view({'post': 'execute_script'})
        request = self.factory.post(
            f'/data-api/datadev/scripts/{self.script.pk}/execute',
            {},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        execution = DataDevScriptExecution.objects.get(script=self.script)
        self.assertEqual(execution.executor_type, 'spark')
        self.assertEqual(execution.result_summary['rowCount'], 1)
        self.assertEqual(response.data['data']['rows'], [{'order_cnt': '1'}])
        self.assertIsNone(execution.task_instance_id)

    def test_publish_task_requires_target_model_for_transform_job(self):
        self.script.target_model = None
        self.script.save(update_fields=['target_model'])
        view = ScriptViewSet.as_view({'post': 'publish_task'})
        request = self.factory.post(f'/data-api/datadev/scripts/{self.script.pk}/publish-task', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 400)
        self.assertIn('绑定目标模型', response.data['msg'])

    def test_publish_task_should_create_platform_task(self):
        view = ScriptViewSet.as_view({'post': 'publish_task'})
        request = self.factory.post(f'/data-api/datadev/scripts/{self.script.pk}/publish-task', {}, format='json')
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.script.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)
        task = Task.objects.get(source_module='datadev.script', source_record_id=self.script.pk, del_flag='0')
        self.assertEqual(task.task_config['scriptRole'], 'transform')
        self.assertEqual(task.task_config['targetModelId'], self.target_model.id)
        self.assertEqual(task.task_config['targetLayer'], 'DWS')

    @patch('apps.dbutils.factory.get_executor')
    def test_execute_task_should_use_published_snapshot(self, mock_get_executor):
        captured_sql = {}

        class _MockQueryExecutor:
            def execute_query(self, sql):
                captured_sql['sql'] = sql
                return {'columns': ['order_cnt'], 'rows': [(1,)]}

            def close(self):
                return None

        mock_get_executor.return_value = _MockQueryExecutor()
        task = TaskService.sync_datadev_source_task(self.script, username='script_runner')
        self.script.versions.update(is_current=False)
        version2 = DataDevScriptVersion.objects.create(
            script=self.script,
            version_number=2,
            content='SELECT 2 AS order_cnt',
            content_hash='hash-v2',
            is_current=True,
            is_released=False,
            create_by='script_runner',
        )

        result = TaskService.execute_task(task, username='scheduler', trigger_mode='manual')

        self.assertTrue(result['ok'])
        self.assertEqual(captured_sql['sql'], 'SELECT 1 AS order_cnt')
        task_instance = TaskInstance.objects.get(task=task)
        execution = DataDevScriptExecution.objects.get(task_instance=task_instance)
        self.assertEqual(execution.version_id, self.version.id)
        self.assertNotEqual(execution.version_id, version2.id)


class ScriptTaskLifecycleSyncTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='script_admin', password='password123')
        self.model = DataDevModel.objects.create(
            model_name='生命周期目标模型',
            model_code='dwd_lifecycle_model',
            layer='DWD',
            table_name='dwd_lifecycle_model',
            schema_name='dwd',
            table_comment='生命周期目标模型',
            engine_type='spark',
            owner='model_owner',
            create_by='tester',
            update_by='tester',
        )
        DataDevModelField.objects.create(
            model=self.model,
            field_name='id',
            field_type='STRING',
            field_comment='主键',
            is_nullable=False,
            ordinal_position=1,
            create_by='tester',
            update_by='tester',
        )

    def test_create_publish_and_destroy_script_should_manage_platform_task(self):
        create_view = ScriptViewSet.as_view({'post': 'create'})
        create_request = self.factory.post(
            '/data-api/datadev/scripts',
            {
                'scriptName': '生命周期脚本',
                'scriptCode': 'script_lifecycle_sync',
                'scriptType': 'sql',
                'scriptRole': 'transform',
                'targetModelId': self.model.id,
                'content': 'SELECT 1',
                'remark': '脚本备注',
            },
            format='json',
        )
        force_authenticate(create_request, user=self.user)

        create_response = create_view(create_request)

        self.assertEqual(create_response.status_code, 200)
        script = DataDevScript.objects.get(script_code='script_lifecycle_sync')
        self.assertFalse(Task.objects.filter(source_module='datadev.script', source_record_id=script.id, del_flag='0').exists())

        publish_view = ScriptViewSet.as_view({'post': 'publish_task'})
        publish_request = self.factory.post(f'/data-api/datadev/scripts/{script.id}/publish-task', {}, format='json')
        force_authenticate(publish_request, user=self.user)

        publish_response = publish_view(publish_request, pk=str(script.id))

        self.assertEqual(publish_response.status_code, 200)
        task = Task.objects.get(source_module='datadev.script', source_record_id=script.id, del_flag='0')
        self.assertEqual(task.task_name, '生命周期脚本')
        self.assertEqual(task.remark, '脚本备注')
        self.assertEqual(task.task_config['engineType'], 'spark')

        destroy_view = ScriptViewSet.as_view({'delete': 'destroy'})
        destroy_request = self.factory.delete(f'/data-api/datadev/scripts/{script.id}')
        force_authenticate(destroy_request, user=self.user)

        destroy_response = destroy_view(destroy_request, pk=str(script.id))

        self.assertEqual(destroy_response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.del_flag, '1')


class DataModelViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(username='model_admin', password='password123')
        self.base_payload = {
            'modelName': '订单宽表',
            'modelCode': 'dwd_order_wide',
            'layer': 'DWD',
            'tableName': 'dwd_order_wide',
            'schemaName': 'dwd',
            'tableComment': '订单宽表',
            'engineType': 'spark',
            'owner': 'data_owner',
            'description': '订单主题域宽表',
            'fields': [
                {
                    'fieldName': 'order_id',
                    'fieldType': 'STRING',
                    'fieldComment': '订单ID',
                    'isNullable': False,
                    'ordinalPosition': 1,
                },
                {
                    'fieldName': 'pay_amount',
                    'fieldType': 'DECIMAL(18,2)',
                    'fieldComment': '支付金额',
                    'isNullable': True,
                    'ordinalPosition': 2,
                },
            ],
        }

    def test_create_and_retrieve_model_should_return_generated_sql(self):
        create_view = DataModelViewSet.as_view({'post': 'create'})
        create_request = self.factory.post('/data-api/datadev/models', self.base_payload, format='json')
        force_authenticate(create_request, user=self.user)

        create_response = create_view(create_request)

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.data['code'], 200)
        model_id = create_response.data['data']['modelId']
        model = DataDevModel.objects.get(pk=model_id)
        self.assertEqual(model.owner, 'data_owner')
        self.assertEqual(model.model_fields.filter(del_flag='0').count(), 2)
        task = Task.objects.get(source_module='datadev.model', source_record_id=model.id, del_flag='0')
        self.assertEqual(task.task_config['fieldCount'], 2)
        self.assertEqual(task.task_config['engineType'], 'spark')

        retrieve_view = DataModelViewSet.as_view({'get': 'retrieve'})
        retrieve_request = self.factory.get(f'/data-api/datadev/models/{model.id}')
        force_authenticate(retrieve_request, user=self.user)

        retrieve_response = retrieve_view(retrieve_request, pk=str(model.id))

        self.assertEqual(retrieve_response.status_code, 200)
        self.assertIn('CREATE TABLE IF NOT EXISTS dwd.dwd_order_wide', retrieve_response.data['data']['generatedSql'])
        self.assertIn("COMMENT '订单ID'", retrieve_response.data['data']['generatedSql'])
        self.assertEqual(len(retrieve_response.data['data']['fields']), 2)

    def test_update_model_should_replace_fields_and_sync_task(self):
        model = DataDevModel.objects.create(
            model_name='订单宽表',
            model_code='dwd_order_wide_update',
            layer='DWD',
            table_name='dwd_order_wide',
            schema_name='dwd',
            table_comment='订单宽表',
            engine_type='spark',
            owner='data_owner',
            create_by='model_admin',
            update_by='model_admin',
        )
        DataDevModelField.objects.create(
            model=model,
            field_name='order_id',
            field_type='STRING',
            field_comment='订单ID',
            is_nullable=False,
            ordinal_position=1,
            create_by='model_admin',
            update_by='model_admin',
        )
        TaskService.sync_datamodel_source_task(model, username='model_admin')

        update_payload = {
            **self.base_payload,
            'modelCode': 'dwd_order_wide_update',
            'modelName': '订单宽表（更新）',
            'tableComment': '订单宽表更新版',
            'fields': [
                {
                    'fieldName': 'order_id',
                    'fieldType': 'STRING',
                    'fieldComment': '订单ID',
                    'isNullable': False,
                    'ordinalPosition': 1,
                },
                {
                    'fieldName': 'buyer_id',
                    'fieldType': 'STRING',
                    'fieldComment': '购买用户ID',
                    'isNullable': True,
                    'ordinalPosition': 2,
                },
            ],
        }
        update_view = DataModelViewSet.as_view({'put': 'update'})
        update_request = self.factory.put(f'/data-api/datadev/models/{model.id}', update_payload, format='json')
        force_authenticate(update_request, user=self.user)

        update_response = update_view(update_request, pk=str(model.id))

        self.assertEqual(update_response.status_code, 200)
        model.refresh_from_db()
        self.assertEqual(model.model_name, '订单宽表（更新）')
        self.assertEqual(model.table_comment, '订单宽表更新版')
        self.assertEqual(model.model_fields.filter(del_flag='0').count(), 2)
        self.assertEqual(model.model_fields.filter(del_flag='1').count(), 1)
        self.assertTrue(model.model_fields.filter(field_name='buyer_id', del_flag='0').exists())
        task = Task.objects.get(source_module='datadev.model', source_record_id=model.id, del_flag='0')
        self.assertEqual(task.task_name, '订单宽表（更新）')
        self.assertEqual(task.task_config['fieldCount'], 2)

    @patch('apps.executors.base.ExecutorFactory.create_executor')
    def test_submit_and_destroy_model_should_update_status_and_soft_delete(self, mock_create_executor):
        model = DataDevModel.objects.create(
            model_name='广告汇总表',
            model_code='ads_campaign_summary',
            layer='ADS',
            table_name='ads_campaign_summary',
            schema_name='ads',
            table_comment='广告汇总表',
            engine_type='spark',
            owner='ads_owner',
            create_by='model_admin',
            update_by='model_admin',
        )
        DataDevModelField.objects.create(
            model=model,
            field_name='campaign_id',
            field_type='STRING',
            field_comment='活动ID',
            is_nullable=False,
            ordinal_position=1,
            create_by='model_admin',
            update_by='model_admin',
        )
        mock_create_executor.return_value = type('SparkExecutorStub', (), {
            'validate': staticmethod(lambda: (True, '')),
            'execute': staticmethod(lambda: {
                'status': 'success',
                'columns': [],
                'rows': [],
                'duration_seconds': 1,
                'raw_output': 'OK',
            }),
        })()

        submit_view = DataModelViewSet.as_view({'post': 'submit_model'})
        submit_request = self.factory.post(f'/data-api/datadev/models/{model.id}/submit', {}, format='json')
        force_authenticate(submit_request, user=self.user)

        submit_response = submit_view(submit_request, pk=str(model.id))

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data['code'], 200)
        model.refresh_from_db()
        self.assertEqual(model.status, 'deployed')
        task = Task.objects.get(source_module='datadev.model', source_record_id=model.id, del_flag='0')
        task_instance = TaskInstance.objects.get(task=task)
        self.assertEqual(task_instance.status, 'success')
        self.assertEqual(submit_response.data['data']['rows'][0]['tableName'], 'ads_campaign_summary')

        destroy_view = DataModelViewSet.as_view({'delete': 'destroy'})
        destroy_request = self.factory.delete(f'/data-api/datadev/models/{model.id}')
        force_authenticate(destroy_request, user=self.user)

        destroy_response = destroy_view(destroy_request, pk=str(model.id))

        self.assertEqual(destroy_response.status_code, 200)
        model.refresh_from_db()
        self.assertEqual(model.del_flag, '1')
        self.assertEqual(model.model_fields.filter(del_flag='0').count(), 0)
        task.refresh_from_db()
        self.assertEqual(task.del_flag, '1')
