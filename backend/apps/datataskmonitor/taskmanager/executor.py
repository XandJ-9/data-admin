from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import AlertRecord, AlertRule, TaskLog
from .scheduler import calc_next_run_time


class TaskExecutor:
    @staticmethod
    def execute(task, *, actor: str = ''):
        actor = actor or ''
        start_time = timezone.now()

        with transaction.atomic():
            log = TaskLog.objects.create(
                task=task,
                status='running',
                start_time=start_time,
                message='manual start',
                create_by=actor,
                update_by=actor,
            )
            task.status = 'running'
            task.last_run_time = start_time
            task.save(update_fields=['status', 'last_run_time', 'update_time'])

        final_status = 'success'
        message = '暂未接入真实执行器'
        try:
            if task.source_task_id:
                message = f'{message}\nsource_task_id={task.source_task_id}'
        except Exception:
            pass

        end_time = timezone.now()
        with transaction.atomic():
            log.status = final_status
            log.end_time = end_time
            log.message = message
            log.update_by = actor
            log.save(update_fields=['status', 'end_time', 'message', 'update_by', 'update_time'])

            task.status = final_status
            task.next_run_time = None if task.enabled == '1' else calc_next_run_time(task.schedule_type, task.schedule_conf, base_time=end_time)
            task.save(update_fields=['status', 'next_run_time', 'update_time'])

            if final_status == 'failed':
                TaskExecutor._trigger_failure_alert(task, message, actor=actor)

        return log

    @staticmethod
    def _trigger_failure_alert(task, message: str, *, actor: str = ''):
        rules = AlertRule.objects.filter(is_active=True, rule_type='failure').filter(Q(task=task) | Q(task__isnull=True))
        for rule in rules:
            AlertRecord.objects.create(
                rule=rule,
                task_name=task.task_name,
                content=message or '任务失败',
                status='pending',
                create_by=actor,
                update_by=actor,
            )

