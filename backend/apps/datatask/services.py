import logging
import re
import uuid

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import Task, TaskDependency, TaskInstance

logger = logging.getLogger(__name__)


class TaskService:
    """统一任务域服务。"""

    SOURCE_SCHEDULE_TYPE_KEY = '_platformSourceScheduleType'
    SOURCE_CRON_EXPRESSION_KEY = '_platformSourceCronExpression'
    SCRIPT_STATUS_TO_TASK_STATUS = {
        'draft': 'draft',
        'published': 'active',
        'archived': 'archived',
    }
    MODEL_STATUS_TO_TASK_STATUS = {
        'draft': 'draft',
        'deployed': 'active',
    }

    @staticmethod
    def build_task_code(task_type: str, source_module: str, source_record_id: int) -> str:
        normalized_module = source_module.replace('.', '_').replace('-', '_')
        return f'{task_type.lower()}_{normalized_module}_{source_record_id}'

    @classmethod
    def upsert_source_task(
        cls,
        *,
        task_name: str,
        task_type: str,
        source_module: str,
        source_record_id: int,
        status: str = 'active',
        schedule_type: str = 'manual',
        cron_expression: str = '',
        owner: str = '',
        task_config: dict | None = None,
        remark: str = '',
        username: str = '',
    ) -> tuple[Task, bool]:
        task_config = {
            **(task_config or {}),
            cls.SOURCE_SCHEDULE_TYPE_KEY: schedule_type,
            cls.SOURCE_CRON_EXPRESSION_KEY: cron_expression,
        }
        defaults = {
            'task_name': task_name,
            'task_code': cls.build_task_code(task_type, source_module, source_record_id),
            'task_type': task_type,
            'status': status,
            'schedule_type': schedule_type,
            'cron_expression': cron_expression,
            'owner': owner,
            'task_config': task_config,
            'remark': remark,
            'update_by': username,
        }
        with transaction.atomic():
            task = Task.objects.select_for_update().filter(
                source_module=source_module,
                source_record_id=source_record_id,
            ).first()
            created = False

            if task is None:
                try:
                    task = Task.objects.create(
                        source_module=source_module,
                        source_record_id=source_record_id,
                        create_by=username,
                        **defaults,
                    )
                    return task, True
                except IntegrityError:
                    task = Task.objects.select_for_update().get(task_code=defaults['task_code'])

            has_upstream_dependencies = TaskDependency.objects.filter(
                downstream_task_id=task.id,
                del_flag='0',
            ).exists()
            if has_upstream_dependencies:
                defaults['schedule_type'] = 'dependency'
                defaults['cron_expression'] = ''

            changed_fields = []
            if task.del_flag != '0':
                task.del_flag = '0'
                changed_fields.append('del_flag')
            for field_name, field_value in defaults.items():
                if getattr(task, field_name) != field_value:
                    setattr(task, field_name, field_value)
                    changed_fields.append(field_name)

            if changed_fields:
                task.save(update_fields=changed_fields + ['update_time'])
            return task, created

    @staticmethod
    def create_task_instance(
        *,
        task: Task,
        trigger_mode: str,
        runtime_config: dict | None = None,
        triggered_by: str = '',
        executor_type: str = '',
    ) -> TaskInstance:
        return TaskInstance.objects.create(
            task=task,
            instance_id=uuid.uuid4().hex,
            status='pending',
            trigger_mode=trigger_mode,
            scheduled_at=timezone.now(),
            runtime_config=runtime_config or {},
            triggered_by=triggered_by,
            executor_type=executor_type,
        )

    @staticmethod
    def mark_instance_running(instance: TaskInstance, executor_type: str = '') -> TaskInstance:
        instance.status = 'running'
        instance.started_at = timezone.now()
        if executor_type:
            instance.executor_type = executor_type
        instance.save(update_fields=['status', 'started_at', 'executor_type'])
        return instance

    @staticmethod
    def finalize_instance(
        *,
        instance: TaskInstance,
        status: str,
        result_summary: dict | None = None,
        error_message: str = '',
    ) -> TaskInstance:
        finished_at = timezone.now()
        duration_seconds = None
        if instance.started_at is not None:
            duration_seconds = round((finished_at - instance.started_at).total_seconds(), 2)

        with transaction.atomic():
            instance.status = status
            instance.finished_at = finished_at
            instance.duration_seconds = duration_seconds
            instance.result_summary = result_summary or {}
            instance.error_message = error_message
            instance.save(
                update_fields=[
                    'status',
                    'finished_at',
                    'duration_seconds',
                    'result_summary',
                    'error_message',
                ]
            )
            Task.objects.filter(pk=instance.task_id).update(
                last_instance_status=status,
                last_instance_at=finished_at,
                update_time=finished_at,
            )

        logger.info(
            '任务实例已完成: task=%s instance=%s status=%s',
            instance.task.task_code,
            instance.instance_id,
            status,
        )
        return instance

    @staticmethod
    def would_create_cycle(
        upstream_task_id: int,
        downstream_task_id: int,
        *,
        exclude_dependency_id: int | None = None,
    ) -> bool:
        if upstream_task_id == downstream_task_id:
            return True

        queryset = TaskDependency.objects.filter(del_flag='0')
        if exclude_dependency_id is not None:
            queryset = queryset.exclude(pk=exclude_dependency_id)

        adjacency: dict[int, list[int]] = {}
        for source_id, target_id in queryset.values_list('upstream_task_id', 'downstream_task_id'):
            adjacency.setdefault(source_id, []).append(target_id)

        pending = [downstream_task_id]
        visited: set[int] = set()
        while pending:
            current_task_id = pending.pop()
            if current_task_id == upstream_task_id:
                return True
            if current_task_id in visited:
                continue
            visited.add(current_task_id)
            pending.extend(adjacency.get(current_task_id, []))
        return False

    @staticmethod
    def sync_dependency_schedule_type(task_id: int) -> None:
        task = Task.objects.filter(pk=task_id, del_flag='0').first()
        if task is None:
            return

        has_upstream_dependencies = TaskDependency.objects.filter(
            downstream_task_id=task_id,
            del_flag='0',
        ).exists()
        if has_upstream_dependencies and task.schedule_type != 'dependency':
            task_config = dict(task.task_config or {})
            task_config.setdefault(TaskService.SOURCE_SCHEDULE_TYPE_KEY, task.schedule_type)
            task_config.setdefault(TaskService.SOURCE_CRON_EXPRESSION_KEY, task.cron_expression)
            task.task_config = task_config
            task.schedule_type = 'dependency'
            task.cron_expression = ''
            task.save(update_fields=['task_config', 'schedule_type', 'cron_expression', 'update_time'])
            return

        if not has_upstream_dependencies and task.schedule_type == 'dependency':
            restored_schedule_type = task.task_config.get(TaskService.SOURCE_SCHEDULE_TYPE_KEY, 'manual')
            restored_cron_expression = task.task_config.get(TaskService.SOURCE_CRON_EXPRESSION_KEY, '')
            task.schedule_type = restored_schedule_type or 'manual'
            task.cron_expression = restored_cron_expression if task.schedule_type == 'cron' else ''
            task.save(update_fields=['schedule_type', 'cron_expression', 'update_time'])

    @classmethod
    def sync_task_source_snapshot(
        cls,
        task: Task,
        *,
        changed_fields: set[str] | None = None,
        username: str = '',
    ) -> None:
        changed_fields = changed_fields or set()
        if not changed_fields:
            return

        if task.source_module == 'dataintegration.task' and task.source_record_id:
            from apps.dataintegration.models import DataIntegrationTask

            integration_task = DataIntegrationTask.objects.filter(
                pk=task.source_record_id,
                del_flag='0',
            ).first()
            if integration_task is None:
                return

            update_fields: list[str] = []
            if 'status' in changed_fields and integration_task.status != task.status:
                integration_task.status = task.status
                update_fields.append('status')
            if 'owner' in changed_fields and integration_task.owner != task.owner:
                integration_task.owner = task.owner
                update_fields.append('owner')
            if 'remark' in changed_fields and integration_task.remark != task.remark:
                integration_task.remark = task.remark
                update_fields.append('remark')
            if task.schedule_type != 'dependency':
                if 'schedule_type' in changed_fields and integration_task.schedule_type != task.schedule_type:
                    integration_task.schedule_type = task.schedule_type
                    update_fields.append('schedule_type')
                expected_cron_expression = task.cron_expression if task.schedule_type == 'cron' else ''
                if (
                    'cron_expression' in changed_fields
                    and integration_task.cron_expression != expected_cron_expression
                ):
                    integration_task.cron_expression = expected_cron_expression
                    update_fields.append('cron_expression')
            if update_fields:
                integration_task.update_by = username
                integration_task.save(update_fields=update_fields + ['update_by', 'update_time'])
            return

        if task.source_module == 'datadev.script' and task.source_record_id:
            from apps.datadev.models import DataDevScript

            script = DataDevScript.objects.filter(
                pk=task.source_record_id,
                del_flag='0',
            ).first()
            if script is None:
                return

            update_fields = []
            if 'owner' in changed_fields and script.owner != task.owner:
                script.owner = task.owner
                update_fields.append('owner')
            if 'remark' in changed_fields and script.remark != task.remark:
                script.remark = task.remark
                update_fields.append('remark')
            if update_fields:
                script.update_by = username
                script.save(update_fields=update_fields + ['update_by', 'update_time'])

    @classmethod
    def build_integration_task_config(cls, integration_task) -> dict:
        source_asset = integration_task.source_asset
        return {
            'sourceDataSourceId': integration_task.source_datasource_id,
            'targetDataSourceId': integration_task.target_datasource_id,
            'sourceAssetId': integration_task.source_asset_id,
            'sourceTableName': source_asset.object_name if source_asset else '',
            'targetSchemaName': integration_task.target_schema_name,
            'targetTableName': integration_task.target_table_name,
            'loadType': integration_task.load_type,
            'writeMode': integration_task.write_mode,
            'executorType': integration_task.executor_type,
            'scheduleType': integration_task.schedule_type,
            'cronExpression': integration_task.cron_expression,
            'taskConfig': integration_task.task_config,
        }

    @classmethod
    def sync_integration_source_task(cls, integration_task, username: str = '') -> Task:
        task, _ = cls.upsert_source_task(
            task_name=integration_task.task_name,
            task_type='DATA_SYNC',
            source_module='dataintegration.task',
            source_record_id=integration_task.id,
            status=integration_task.status,
            schedule_type='cron' if integration_task.schedule_type == 'cron' else 'manual',
            cron_expression=integration_task.cron_expression,
            owner=integration_task.owner or username,
            task_config=cls.build_integration_task_config(integration_task),
            remark=integration_task.remark,
            username=username,
        )
        return task

    @classmethod
    def build_script_task_config(cls, *, script, version, datasource, sql: str) -> dict:
        return {
            'scriptId': script.id,
            'scriptCode': script.script_code,
            'scriptType': script.script_type,
            'engineType': getattr(script, 'engine_type', ''),
            'directoryId': script.directory_id,
            'datasourceId': datasource.id if datasource else None,
            'datasourceType': datasource.db_type if datasource else '',
            'currentVersionId': version.id if version else None,
            'sqlText': sql,
        }

    @classmethod
    def get_task_governance_defaults(cls, task: Task | None) -> tuple[str, str, str]:
        if task is None:
            return 'active', 'manual', ''
        schedule_type = task.task_config.get(
            cls.SOURCE_SCHEDULE_TYPE_KEY,
            task.schedule_type if task.schedule_type != 'dependency' else 'manual',
        )
        cron_expression = task.task_config.get(
            cls.SOURCE_CRON_EXPRESSION_KEY,
            task.cron_expression,
        )
        return task.status, schedule_type or 'manual', cron_expression or ''

    @classmethod
    def sync_datadev_source_task(cls, script, username: str = '') -> Task | None:
        existing_task = Task.objects.filter(
            source_module='datadev.script',
            source_record_id=script.id,
            del_flag='0',
        ).first()
        if script.script_type != 'sql':
            cls.soft_delete_source_task(
                source_module='datadev.script',
                source_record_id=script.id,
                username=username,
            )
            return None

        current_version = script.versions.filter(is_current=True).first()
        default_status = cls.SCRIPT_STATUS_TO_TASK_STATUS.get(script.status, 'draft')
        preserved_status, preserved_schedule_type, preserved_cron_expression = cls.get_task_governance_defaults(
            existing_task
        )
        task, _ = cls.upsert_source_task(
            task_name=script.script_name,
            task_type='SQL_COMPUTE',
            source_module='datadev.script',
            source_record_id=script.id,
            status=existing_task.status if existing_task else default_status,
            schedule_type=preserved_schedule_type,
            cron_expression=preserved_cron_expression,
            owner=script.owner or username,
            task_config=cls.build_script_task_config(
                script=script,
                version=current_version,
                datasource=script.datasource,
                sql=current_version.content if current_version else '',
            ),
            remark=script.remark or '',
            username=username,
        )
        if existing_task is None and task.status != default_status:
            task.status = default_status
            task.save(update_fields=['status', 'update_time'])
        return task

    @classmethod
    def soft_delete_source_task(
        cls,
        *,
        source_module: str,
        source_record_id: int,
        username: str = '',
    ) -> None:
        platform_task = Task.objects.filter(
            source_module=source_module,
            source_record_id=source_record_id,
            del_flag='0',
        ).first()
        if platform_task is None:
            return

        affected_downstream_ids: set[int] = set()
        with transaction.atomic():
            related_dependencies = TaskDependency.objects.filter(del_flag='0').filter(
                Q(upstream_task=platform_task) | Q(downstream_task=platform_task)
            )
            for dependency in related_dependencies:
                if dependency.upstream_task_id == platform_task.id:
                    affected_downstream_ids.add(dependency.downstream_task_id)
                dependency.del_flag = '1'
                dependency.update_by = username
                dependency.save(update_fields=['del_flag', 'update_by', 'update_time'])

            platform_task.del_flag = '1'
            platform_task.update_by = username
            platform_task.save(update_fields=['del_flag', 'update_by', 'update_time'])

            for downstream_task_id in affected_downstream_ids:
                cls.sync_dependency_schedule_type(downstream_task_id)

    @classmethod
    def execute_integration_task(
        cls,
        integration_task,
        *,
        username: str = '',
        trigger_mode: str = 'manual',
        runtime_config: dict | None = None,
    ) -> dict:
        from apps.executors.base import ExecutorFactory

        platform_task = cls.sync_integration_source_task(integration_task, username=username)
        effective_runtime_config = {
            'integrationTaskId': integration_task.id,
            **(runtime_config or {}),
        }
        task_instance = cls.create_task_instance(
            task=platform_task,
            trigger_mode=trigger_mode,
            runtime_config=effective_runtime_config,
            triggered_by=username or trigger_mode,
            executor_type=integration_task.executor_type,
        )
        cls.mark_instance_running(task_instance, executor_type=integration_task.executor_type)

        try:
            executor = ExecutorFactory.create_executor(
                integration_task.executor_type,
                integration_task,
                config=effective_runtime_config,
            )
            is_valid, validate_message = executor.validate()
            if not is_valid:
                raise ValueError(validate_message)
            result = executor.execute()
        except Exception as exc:
            cls.finalize_instance(
                instance=task_instance,
                status='failed',
                result_summary={'error': str(exc)},
                error_message=str(exc),
            )
            return {
                'ok': False,
                'msg': f'执行失败: {exc}',
                'data': {'executionId': task_instance.instance_id, 'status': 'failed'},
            }

        result_status = result.get('status') or 'success'
        cls.finalize_instance(
            instance=task_instance,
            status=result_status,
            result_summary=result,
            error_message=result.get('error_message') or '',
        )
        if result_status == 'failed':
            return {
                'ok': False,
                'msg': result.get('error_message') or '执行失败',
                'data': {'executionId': task_instance.instance_id, 'status': 'failed'},
            }
        return {
            'ok': True,
            'msg': '执行成功',
            'data': {
                'executionId': task_instance.instance_id,
                'status': result_status,
                'resultSummary': result,
            },
        }

    @classmethod
    def execute_datadev_script(
        cls,
        script,
        *,
        username: str = '',
        runtime_params: dict | None = None,
        trigger_mode: str = 'manual',
        runtime_config: dict | None = None,
    ) -> dict:
        from datetime import timedelta

        from django.utils import timezone

        from apps.datadev.models import DataDevScriptExecution
        from apps.dbutils.factory import get_executor
        from apps.executors.base import ExecutorFactory

        current_version = script.versions.filter(is_current=True).first()
        if not current_version:
            return {'ok': False, 'msg': '脚本没有当前版本', 'data': None}

        sql = current_version.content
        if not sql or not sql.strip():
            return {'ok': False, 'msg': '脚本内容为空', 'data': None}

        ds = script.datasource
        info = None
        runtime_params = runtime_params or {}
        execution_mode = str(runtime_params.get('executionMode') or '').strip().lower()
        modeling_info = None
        configured_engine_type = str(getattr(script, 'engine_type', '') or '').strip().lower()
        if configured_engine_type in ('spark-sql', 'sparksql'):
            configured_engine_type = 'spark'
        elif configured_engine_type in ('hiveserver2', 'hive2'):
            configured_engine_type = 'hive'
        elif configured_engine_type not in ('spark', 'hive', 'mvp'):
            configured_engine_type = 'mvp'
        normalized_executor_type = 'mvp'
        if execution_mode == 'modeling':
            normalized_executor_type = str(runtime_params.get('engine') or 'spark').strip().lower()
            if normalized_executor_type in ('spark-sql', 'sparksql'):
                normalized_executor_type = 'spark'
            if normalized_executor_type not in ('spark', 'hive'):
                return {'ok': False, 'msg': '建模执行仅支持 Spark SQL 或 Hive', 'data': None}
            if not re.search(r'\bcreate\s+table\b', sql, flags=re.IGNORECASE):
                return {'ok': False, 'msg': '建模执行当前仅支持 CREATE TABLE 语句', 'data': None}
            modeling_owner = str(runtime_params.get('owner') or script.owner or username or '').strip()
            target_layer = str(runtime_params.get('targetLayer') or '').strip().upper()
            target_table_name = str(runtime_params.get('targetTableName') or '').strip()
            table_comment = str(runtime_params.get('tableComment') or '').strip()
            if not modeling_owner:
                return {'ok': False, 'msg': '建模执行必须填写负责人', 'data': None}
            if target_layer not in ('ODS', 'DWD', 'DWS', 'ADS'):
                return {'ok': False, 'msg': '建模执行必须选择 ODS/DWD/DWS/ADS 层级', 'data': None}
            if not target_table_name:
                return {'ok': False, 'msg': '建模执行必须填写目标表名', 'data': None}
            if not table_comment:
                return {'ok': False, 'msg': '建模执行必须填写表注释', 'data': None}
            modeling_info = {
                'engine': normalized_executor_type,
                'targetLayer': target_layer,
                'targetTableName': target_table_name,
                'tableComment': table_comment,
                'owner': modeling_owner,
            }
        elif ds is not None:
            info = {
                'type': ds.db_type,
                'host': ds.host,
                'port': ds.port,
                'username': ds.username,
                'password': ds.password,
                'database': ds.db_name,
                'params': ds.params or {},
            }
            normalized_executor_type = str(ds.db_type or '').lower()
            if normalized_executor_type in ('spark-sql', 'sparksql', 'spark'):
                normalized_executor_type = 'spark'
            elif normalized_executor_type in ('hive', 'hiveserver2', 'hive2'):
                normalized_executor_type = 'hive'
        elif script.script_type == 'sql' and configured_engine_type in ('spark', 'hive'):
            normalized_executor_type = configured_engine_type
        elif script.script_type == 'python' or configured_engine_type == 'mvp':
            normalized_executor_type = 'mvp'
        existing_task = Task.objects.filter(
            source_module='datadev.script',
            source_record_id=script.id,
            del_flag='0',
        ).first()
        preserved_status, preserved_schedule_type, preserved_cron_expression = cls.get_task_governance_defaults(
            existing_task
        )
        task, _ = cls.upsert_source_task(
            task_name=script.script_name,
            task_type='SQL_COMPUTE',
            source_module='datadev.script',
            source_record_id=script.id,
            status=preserved_status,
            schedule_type=preserved_schedule_type,
            cron_expression=preserved_cron_expression,
            owner=(modeling_info['owner'] if modeling_info else script.owner or username),
            task_config=cls.build_script_task_config(
                script=script,
                version=current_version,
                datasource=ds,
                sql=sql,
            ),
            remark=script.remark or (existing_task.remark if existing_task else ''),
            username=username,
        )
        task_instance = cls.create_task_instance(
            task=task,
            trigger_mode=trigger_mode,
            runtime_config={
                'scriptVersionId': current_version.id,
                'params': runtime_params,
                **(runtime_config or {}),
            },
            triggered_by=username or trigger_mode,
            executor_type=normalized_executor_type,
        )
        cls.mark_instance_running(task_instance, executor_type=normalized_executor_type)

        start_time = timezone.now()
        start_perf = timezone.now().timestamp()
        executor = None
        status = 'success'
        error_msg = ''
        columns: list[str] = []
        rows: list[dict] = []
        engine_result: dict = {}

        try:
            if normalized_executor_type == 'mvp':
                statement_count = len([segment for segment in sql.split(';') if segment.strip()]) or 1
                columns = ['mode', 'message', 'statementCount']
                rows = [{
                    'mode': 'MVP预演',
                    'message': '当前阶段未绑定执行数据源，本次仅完成脚本登记、版本确认和任务预演',
                    'statementCount': statement_count,
                }]
                engine_result = {
                    'status': 'success',
                    'columns': columns,
                    'rows': rows,
                    'duration_seconds': 0,
                    'design_only': True,
                }
            elif normalized_executor_type in ('spark', 'hive'):
                executor = ExecutorFactory.create_executor(
                    normalized_executor_type,
                    script,
                    config={
                        'engine': normalized_executor_type,
                        'sql': sql,
                        'datasource': ds if modeling_info is None else None,
                        'runtimeParams': runtime_params,
                    },
                )
                is_valid, validate_message = executor.validate()
                if not is_valid:
                    raise ValueError(validate_message)
                engine_result = executor.execute()
                status = engine_result.get('status') or 'success'
                error_msg = engine_result.get('error_message') or ''
                columns = engine_result.get('columns') or []
                raw_rows = engine_result.get('rows') or []
                if raw_rows and isinstance(raw_rows[0], dict):
                    rows = raw_rows
                    if not columns:
                        columns = list(raw_rows[0].keys())
                else:
                    rows = [dict(zip(columns, row)) for row in raw_rows]
            else:
                executor = get_executor(info)
                query_result = executor.execute_query(sql=sql)
                columns = query_result.get('columns', [])
                raw_rows = query_result.get('rows', [])
                rows = [dict(zip(columns, row)) for row in raw_rows]
        except Exception as exc:
            status = 'failed'
            error_msg = str(exc)
            logger.exception('脚本执行失败: script_id=%s, error=%s', script.id, exc)
        finally:
            if executor and hasattr(executor, 'close'):
                try:
                    executor.close()
                except Exception:
                    logger.warning('关闭脚本执行器失败: script_id=%s', script.id, exc_info=True)

        if modeling_info and status == 'success' and not columns and not rows:
            columns = ['mode', 'targetLayer', 'targetTableName', 'tableComment', 'owner']
            rows = [{
                'mode': '建模执行',
                'targetLayer': modeling_info['targetLayer'],
                'targetTableName': modeling_info['targetTableName'],
                'tableComment': modeling_info['tableComment'],
                'owner': modeling_info['owner'],
            }]

        duration = round(timezone.now().timestamp() - start_perf, 2)
        if engine_result.get('duration_seconds') not in (None, ''):
            duration = engine_result['duration_seconds']
        end_time = start_time + timedelta(seconds=duration)
        result_summary = {
            'columns': columns,
            'rows': rows,
            'rowCount': len(rows),
            'error': error_msg,
            'engine': normalized_executor_type,
        }
        if engine_result.get('raw_output'):
            result_summary['rawOutput'] = engine_result['raw_output']
        if engine_result.get('raw_error'):
            result_summary['rawError'] = engine_result['raw_error']
        task_result_summary = {
            'columns': columns,
            'rowCount': len(rows),
            'error': error_msg,
            'engine': normalized_executor_type,
        }
        if modeling_info:
            result_summary['executionMode'] = 'modeling'
            result_summary['modelingInfo'] = modeling_info
            task_result_summary['executionMode'] = 'modeling'
            task_result_summary['modelingInfo'] = modeling_info
        if engine_result.get('design_only'):
            result_summary['designOnly'] = True
            task_result_summary['designOnly'] = True
        cls.finalize_instance(
            instance=task_instance,
            status=status,
            result_summary=task_result_summary,
            error_message=error_msg,
        )

        execution = DataDevScriptExecution.objects.create(
            script=script,
            version=current_version,
            task_instance=task_instance,
            execution_id=task_instance.instance_id,
            status=status,
            executor_type=normalized_executor_type,
            executor_params=runtime_params,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            result_summary=result_summary,
            error_message=error_msg,
            executed_by=username,
        )
        if status == 'failed':
            return {
                'ok': False,
                'msg': f'执行失败: {error_msg}',
                'data': {
                    'executionId': execution.execution_id,
                    'status': 'failed',
                    'rawOutput': result_summary.get('rawOutput', ''),
                    'rawError': result_summary.get('rawError', ''),
                },
            }
        return {
            'ok': True,
            'msg': '执行成功',
            'data': {
                'executionId': execution.execution_id,
                'status': 'success',
                'columns': columns,
                'rows': rows,
                'duration': duration,
                'designOnly': bool(engine_result.get('design_only')),
                'executionMode': 'modeling' if modeling_info else 'standard',
                'modelingInfo': modeling_info,
                'rawOutput': result_summary.get('rawOutput', ''),
                'rawError': result_summary.get('rawError', ''),
            },
        }

    @staticmethod
    def escape_sql_literal(value: str) -> str:
        return str(value or '').replace("'", "''")

    @classmethod
    def build_datamodel_create_sql(cls, model) -> str:
        active_fields = model.model_fields.filter(del_flag='0').order_by('ordinal_position', 'id')
        if not active_fields.exists():
            raise ValueError('模型字段不能为空')
        qualified_table_name = model.table_name
        if getattr(model, 'schema_name', ''):
            qualified_table_name = f"{model.schema_name}.{model.table_name}"
        column_lines = []
        for field in active_fields:
            line = f"  `{field.field_name}` {field.field_type}"
            if not field.is_nullable:
                line += ' NOT NULL'
            line += f" COMMENT '{cls.escape_sql_literal(field.field_comment)}'"
            column_lines.append(line)
        return '\n'.join([
            f"CREATE TABLE IF NOT EXISTS {qualified_table_name} (",
            ',\n'.join(column_lines),
            ')',
            f"COMMENT '{cls.escape_sql_literal(model.table_comment)}'",
        ])

    @classmethod
    def build_datamodel_task_config(cls, model, sql_text: str) -> dict:
        return {
            'modelId': model.id,
            'modelCode': model.model_code,
            'layer': model.layer,
            'tableName': model.table_name,
            'schemaName': model.schema_name,
            'tableComment': model.table_comment,
            'engineType': model.engine_type,
            'fieldCount': model.model_fields.filter(del_flag='0').count(),
            'sqlText': sql_text,
        }

    @classmethod
    def sync_datamodel_source_task(cls, model, username: str = '') -> Task:
        sql_text = cls.build_datamodel_create_sql(model)
        existing_task = Task.objects.filter(
            source_module='datadev.model',
            source_record_id=model.id,
            del_flag='0',
        ).first()
        default_status = cls.MODEL_STATUS_TO_TASK_STATUS.get(model.status, 'draft')
        preserved_status, preserved_schedule_type, preserved_cron_expression = cls.get_task_governance_defaults(existing_task)
        task, _ = cls.upsert_source_task(
            task_name=model.model_name,
            task_type='SQL_COMPUTE',
            source_module='datadev.model',
            source_record_id=model.id,
            status=existing_task.status if existing_task else default_status,
            schedule_type=preserved_schedule_type,
            cron_expression=preserved_cron_expression,
            owner=model.owner or username,
            task_config=cls.build_datamodel_task_config(model, sql_text),
            remark=model.remark or '',
            username=username,
        )
        if existing_task is None and task.status != default_status:
            task.status = default_status
            task.save(update_fields=['status', 'update_time'])
        return task

    @classmethod
    def execute_datamodel_task(
        cls,
        model,
        *,
        username: str = '',
        trigger_mode: str = 'manual',
    ) -> dict:
        from datetime import timedelta

        from django.utils import timezone

        from apps.executors.base import ExecutorFactory

        if not model.owner:
            return {'ok': False, 'msg': '提交建表前必须填写负责人', 'data': None}
        if not model.table_comment:
            return {'ok': False, 'msg': '提交建表前必须填写表注释', 'data': None}
        active_fields = model.model_fields.filter(del_flag='0').order_by('ordinal_position', 'id')
        if not active_fields.exists():
            return {'ok': False, 'msg': '提交建表前至少需要定义一个字段', 'data': None}
        for field in active_fields:
            if not field.field_comment:
                return {'ok': False, 'msg': f'字段 {field.field_name} 缺少字段注释', 'data': None}

        sql_text = cls.build_datamodel_create_sql(model)
        existing_task = Task.objects.filter(
            source_module='datadev.model',
            source_record_id=model.id,
            del_flag='0',
        ).first()
        preserved_status, preserved_schedule_type, preserved_cron_expression = cls.get_task_governance_defaults(existing_task)
        task, _ = cls.upsert_source_task(
            task_name=model.model_name,
            task_type='SQL_COMPUTE',
            source_module='datadev.model',
            source_record_id=model.id,
            status=preserved_status,
            schedule_type=preserved_schedule_type,
            cron_expression=preserved_cron_expression,
            owner=model.owner or username,
            task_config=cls.build_datamodel_task_config(model, sql_text),
            remark=model.remark or (existing_task.remark if existing_task else ''),
            username=username,
        )
        task_instance = cls.create_task_instance(
            task=task,
            trigger_mode=trigger_mode,
            runtime_config={
                'layer': model.layer,
                'tableName': model.table_name,
                'schemaName': model.schema_name,
                'engineType': model.engine_type,
            },
            triggered_by=username or trigger_mode,
            executor_type=model.engine_type,
        )
        cls.mark_instance_running(task_instance, executor_type=model.engine_type)

        start_time = timezone.now()
        start_perf = timezone.now().timestamp()
        executor = ExecutorFactory.create_executor(
            model.engine_type,
            model,
            config={'engine': model.engine_type, 'sql': sql_text},
        )
        status = 'success'
        error_msg = ''
        engine_result = {}
        columns = []
        rows = []
        try:
            is_valid, validate_message = executor.validate()
            if not is_valid:
                raise ValueError(validate_message)
            engine_result = executor.execute()
            status = engine_result.get('status') or 'success'
            error_msg = engine_result.get('error_message') or ''
            columns = engine_result.get('columns') or []
            raw_rows = engine_result.get('rows') or []
            if raw_rows and isinstance(raw_rows[0], dict):
                rows = raw_rows
                if not columns:
                    columns = list(raw_rows[0].keys())
            else:
                rows = [dict(zip(columns, row)) for row in raw_rows]
        except Exception as exc:
            status = 'failed'
            error_msg = str(exc)
            logger.exception('模型建表失败: model_id=%s, error=%s', model.id, exc)
        finally:
            if executor and hasattr(executor, 'close'):
                try:
                    executor.close()
                except Exception:
                    logger.warning('关闭模型执行器失败: model_id=%s', model.id, exc_info=True)

        if status == 'success' and not columns and not rows:
            columns = ['layer', 'tableName', 'engineType', 'owner']
            rows = [{
                'layer': model.layer,
                'tableName': model.table_name,
                'engineType': model.engine_type,
                'owner': model.owner,
            }]

        duration = round(timezone.now().timestamp() - start_perf, 2)
        if engine_result.get('duration_seconds') not in (None, ''):
            duration = engine_result['duration_seconds']
        end_time = start_time + timedelta(seconds=duration)
        result_summary = {
            'columns': columns,
            'rowCount': len(rows),
            'engine': model.engine_type,
            'tableName': model.table_name,
            'layer': model.layer,
            'error': error_msg,
        }
        cls.finalize_instance(
            instance=task_instance,
            status=status,
            result_summary=result_summary,
            error_message=error_msg,
        )
        if status == 'success':
            model.status = 'deployed'
            model.update_by = username
            model.save(update_fields=['status', 'update_by', 'update_time'])
            end_time = end_time
        if status == 'failed':
            return {
                'ok': False,
                'msg': f'提交建表失败: {error_msg}',
                'data': {'taskInstanceId': task_instance.id, 'status': 'failed'},
            }
        return {
            'ok': True,
            'msg': '提交建表成功',
            'data': {
                'taskInstanceId': task_instance.id,
                'executionId': task_instance.instance_id,
                'status': status,
                'columns': columns,
                'rows': rows,
                'duration': duration,
                'generatedSql': sql_text,
                'startedAt': start_time,
                'finishedAt': end_time,
            },
        }

    @classmethod
    def execute_task(
        cls,
        task: Task,
        *,
        username: str = '',
        trigger_mode: str = 'manual',
        runtime_config: dict | None = None,
    ) -> dict:
        if task.source_module == 'dataintegration.task' and task.source_record_id:
            from apps.dataintegration.models import DataIntegrationTask

            integration_task = DataIntegrationTask.objects.filter(
                pk=task.source_record_id,
                del_flag='0',
            ).first()
            if integration_task is None:
                return {'ok': False, 'msg': '来源集成任务不存在或已删除', 'data': None}
            return cls.execute_integration_task(
                integration_task,
                username=username,
                trigger_mode=trigger_mode,
                runtime_config=runtime_config,
            )

        if task.source_module == 'datadev.script' and task.source_record_id:
            from apps.datadev.models import DataDevScript

            script = DataDevScript.objects.select_related('datasource').filter(
                pk=task.source_record_id,
                del_flag='0',
            ).first()
            if script is None:
                return {'ok': False, 'msg': '来源脚本不存在或已删除', 'data': None}
            return cls.execute_datadev_script(
                script,
                username=username,
                trigger_mode=trigger_mode,
                runtime_config=runtime_config,
            )

        return {'ok': False, 'msg': f'暂不支持执行来源模块 {task.source_module or "未知"}', 'data': None}
