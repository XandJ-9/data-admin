import logging
import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Task, TaskInstance

logger = logging.getLogger(__name__)


class TaskService:
    """统一任务域服务。"""

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
        schedule_type: str = 'manual',
        owner: str = '',
        task_config: dict | None = None,
        remark: str = '',
        username: str = '',
    ) -> tuple[Task, bool]:
        task_config = task_config or {}
        defaults = {
            'task_name': task_name,
            'task_code': cls.build_task_code(task_type, source_module, source_record_id),
            'task_type': task_type,
            'status': 'active',
            'schedule_type': schedule_type,
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
