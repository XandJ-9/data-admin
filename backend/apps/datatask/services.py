import logging
import uuid

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import Task, TaskDependency, TaskInstance
from .source_registry import get_source_handler

logger = logging.getLogger(__name__)


class TaskService:
    """统一任务域服务。"""

    SOURCE_SCHEDULE_TYPE_KEY = '_platformSourceScheduleType'
    SOURCE_CRON_EXPRESSION_KEY = '_platformSourceCronExpression'

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
        started_at=None,
        finished_at=None,
        duration_seconds=None,
    ) -> TaskInstance:
        finished_at = finished_at or timezone.now()
        effective_started_at = started_at or instance.started_at
        if duration_seconds is None and effective_started_at is not None:
            duration_seconds = round((finished_at - effective_started_at).total_seconds(), 2)

        with transaction.atomic():
            instance.status = status
            if started_at is not None:
                instance.started_at = started_at
            instance.finished_at = finished_at
            instance.duration_seconds = duration_seconds
            instance.result_summary = result_summary or {}
            instance.error_message = error_message
            instance.save(
                update_fields=[
                    'status',
                    'started_at',
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

        handler = get_source_handler(task.source_module)
        if handler is not None:
            handler.sync_platform_snapshot(task, changed_fields, username)
            return

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
    def execute_task(
        cls,
        task: Task,
        *,
        username: str = '',
        trigger_mode: str = 'manual',
        runtime_config: dict | None = None,
    ) -> dict:
        handler = get_source_handler(task.source_module)
        if handler is not None and task.source_record_id:
            source_record = handler.load_source_record(task.source_record_id)
            if source_record is None:
                return {'ok': False, 'msg': '来源任务不存在或已删除', 'data': None}
            return handler.execute_task(
                task,
                source_record,
                username,
                trigger_mode,
                runtime_config,
            )

        return {'ok': False, 'msg': f'暂不支持执行来源模块 {task.source_module or "未知"}', 'data': None}
