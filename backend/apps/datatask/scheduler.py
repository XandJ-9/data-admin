from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
import logging

from django.utils import timezone

from .models import Task, TaskDependency, TaskInstance
from .source_registry import get_source_handler
from .services import TaskService

logger = logging.getLogger(__name__)


class CronExpressionMatcher:
    """轻量级 Cron 匹配器。

    用于在调度周期内判断平台任务的 5 段 cron 表达式是否命中当前时间点。
    """

    FIELD_RANGES = (
        (0, 59),
        (0, 23),
        (1, 31),
        (1, 12),
        (0, 7),
    )

    @classmethod
    def matches(cls, expression: str, moment) -> bool:
        fields = str(expression or '').strip().split()
        if len(fields) != 5:
            return False
        values = (
            moment.minute,
            moment.hour,
            moment.day,
            moment.month,
            moment.isoweekday() % 7,
        )
        return all(
            cls._field_matches(field, value, minimum, maximum)
            for field, value, (minimum, maximum) in zip(fields, values, cls.FIELD_RANGES)
        )

    @classmethod
    def _field_matches(cls, field: str, value: int, minimum: int, maximum: int) -> bool:
        for token in field.split(','):
            token = token.strip()
            if not token:
                continue
            if cls._token_matches(token, value, minimum, maximum):
                return True
        return False

    @classmethod
    def _token_matches(cls, token: str, value: int, minimum: int, maximum: int) -> bool:
        if token == '*':
            return True
        step = 1
        base = token
        if '/' in token:
            base, step_text = token.split('/', 1)
            step = int(step_text)
            if step <= 0:
                return False
        if base == '*':
            return (value - minimum) % step == 0
        if '-' in base:
            start_text, end_text = base.split('-', 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                return False
            return start <= value <= end and (value - start) % step == 0
        exact = int(base)
        if not minimum <= exact <= maximum:
            return False
        return value == exact


class TaskSchedulerService:
    """平台任务调度服务。

    负责扫描到期的 cron 任务和满足条件的依赖任务，并通过 TaskService 触发实际执行。
    """

    DEFAULT_TRIGGER_USER = 'scheduler'

    @classmethod
    def run_cycle(cls, *, now=None, username: str = DEFAULT_TRIGGER_USER) -> dict:
        current_time = (now or timezone.now()).replace(second=0, microsecond=0)
        cleanup_result = cls.cleanup_stale_instances()
        cron_result = cls.dispatch_due_cron_tasks(now=current_time, username=username)
        dependency_result = cls.dispatch_due_dependency_tasks(now=current_time, username=username)
        return {
            'runAt': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'cleanup': cleanup_result,
            'cron': cron_result,
            'dependency': dependency_result,
        }

    @classmethod
    def cleanup_stale_instances(cls) -> dict:
        recovered_instance_ids: list[str] = []
        errors = []
        source_modules = Task.objects.filter(del_flag='0').exclude(source_module='').values_list('source_module', flat=True).distinct()
        for source_module in source_modules:
            handler = get_source_handler(source_module)
            cleanup_stale_instances = getattr(handler, 'cleanup_stale_instances', None) if handler else None
            if cleanup_stale_instances is None:
                continue
            try:
                recovered_instance_ids.extend(cleanup_stale_instances())
            except Exception as exc:
                logger.exception('清理来源模块陈旧实例失败: source_module=%s, error=%s', source_module, exc)
                errors.append({'sourceModule': source_module, 'message': str(exc)})
        return {
            'recoveredInstanceIds': recovered_instance_ids,
            'errors': errors,
        }

    @classmethod
    def dispatch_due_cron_tasks(cls, *, now, username: str) -> dict:
        window_end = now + timedelta(minutes=1)
        dispatched_task_ids = []
        skipped_task_ids = []
        errors = []
        tasks = Task.objects.filter(
            del_flag='0',
            status='active',
            schedule_type='cron',
        ).exclude(cron_expression='').order_by('id')
        for task in tasks:
            if not CronExpressionMatcher.matches(task.cron_expression, now):
                continue
            if cls._has_live_instance(task.id):
                skipped_task_ids.append(task.id)
                continue
            if TaskInstance.objects.filter(
                task_id=task.id,
                trigger_mode='schedule',
                scheduled_at__gte=now,
                scheduled_at__lt=window_end,
            ).exists():
                skipped_task_ids.append(task.id)
                continue
            result = TaskService.execute_task(
                task,
                username=username,
                trigger_mode='schedule',
                runtime_config={'scheduleTick': now.strftime('%Y-%m-%d %H:%M:%S')},
            )
            if result.get('data') is not None:
                dispatched_task_ids.append(task.id)
            elif not result.get('ok'):
                errors.append({'taskId': task.id, 'message': result.get('msg') or '调度失败'})
        return {
            'dispatchedTaskIds': dispatched_task_ids,
            'skippedTaskIds': skipped_task_ids,
            'errors': errors,
        }

    @classmethod
    def dispatch_due_dependency_tasks(cls, *, now, username: str) -> dict:
        dependencies = TaskDependency.objects.select_related('upstream_task', 'downstream_task').filter(
            del_flag='0',
            downstream_task__del_flag='0',
            downstream_task__status='active',
            downstream_task__schedule_type='dependency',
        ).order_by('downstream_task_id', 'id')
        grouped_dependencies: dict[int, list[TaskDependency]] = defaultdict(list)
        for dependency in dependencies:
            grouped_dependencies[dependency.downstream_task_id].append(dependency)

        dispatched_task_ids = []
        skipped_task_ids = []
        errors = []
        for downstream_task_id, downstream_dependencies in grouped_dependencies.items():
            downstream_task = downstream_dependencies[0].downstream_task
            if cls._has_live_instance(downstream_task_id):
                skipped_task_ids.append(downstream_task_id)
                continue
            upstream_instances = []
            is_due = True
            for dependency in downstream_dependencies:
                latest_success_instance = TaskInstance.objects.filter(
                    task_id=dependency.upstream_task_id,
                    status='success',
                ).order_by('-finished_at', '-create_time', '-id').first()
                if latest_success_instance is None:
                    is_due = False
                    break
                finished_at = latest_success_instance.finished_at or latest_success_instance.create_time
                if finished_at is None or finished_at + timedelta(seconds=dependency.lag_seconds) > now:
                    is_due = False
                    break
                upstream_instances.append((dependency, latest_success_instance))
            if not is_due:
                continue
            dependency_fingerprint = cls._build_dependency_fingerprint(upstream_instances)
            existing_instances = TaskInstance.objects.filter(
                task_id=downstream_task_id,
                trigger_mode='dependency',
            ).only('runtime_config')
            if any((instance.runtime_config or {}).get('dependencyFingerprint') == dependency_fingerprint for instance in existing_instances):
                skipped_task_ids.append(downstream_task_id)
                continue
            runtime_config = {
                'dependencyFingerprint': dependency_fingerprint,
                'dependencyUpstreams': [
                    {
                        'dependencyId': dependency.id,
                        'upstreamTaskId': dependency.upstream_task_id,
                        'upstreamInstanceId': instance.instance_id,
                        'lagSeconds': dependency.lag_seconds,
                    }
                    for dependency, instance in upstream_instances
                ],
            }
            result = TaskService.execute_task(
                downstream_task,
                username=username,
                trigger_mode='dependency',
                runtime_config=runtime_config,
            )
            if result.get('data') is not None:
                dispatched_task_ids.append(downstream_task_id)
            elif not result.get('ok'):
                errors.append({'taskId': downstream_task_id, 'message': result.get('msg') or '依赖触发失败'})
        return {
            'dispatchedTaskIds': dispatched_task_ids,
            'skippedTaskIds': skipped_task_ids,
            'errors': errors,
        }

    @staticmethod
    def _has_live_instance(task_id: int) -> bool:
        return TaskInstance.objects.filter(
            task_id=task_id,
            status__in=['pending', 'running'],
        ).exists()

    @staticmethod
    def _build_dependency_fingerprint(upstream_instances: list[tuple[TaskDependency, TaskInstance]]) -> str:
        parts = []
        for dependency, instance in sorted(upstream_instances, key=lambda item: item[0].id):
            parts.append(f'{dependency.id}:{instance.instance_id}')
        return '|'.join(parts)
