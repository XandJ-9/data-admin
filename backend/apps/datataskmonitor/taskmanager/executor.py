from __future__ import annotations

import uuid
import traceback
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import AlertRecord, AlertRule, TaskLog
from .scheduler import calc_next_run_time


class TaskExecutor:
    @staticmethod
    def execute(task, *, actor: str = ''):
        """
        执行任务

        支持两种类型的任务：
        1. ETL任务（dataintegration.IntegrationTask）：使用真实执行器
        2. 其他任务：保留原有逻辑
        """
        actor = actor or ''
        start_time = timezone.now()

        # 检查是否是ETL任务
        if task.source_task_id:
            try:
                from apps.dataetl.models import IntegrationTask, TaskExecutionLog
                from apps.dataetl.executors.factory import get_executor

                # 获取ETL任务
                etl_task = IntegrationTask.objects.get(id=task.source_task_id)

                # 创建ETL执行日志
                execution_log = TaskExecutionLog.objects.create(
                    task=etl_task,
                    execution_id=f"{etl_task.id}_{uuid.uuid4().hex[:12]}",
                    status='running',
                    start_time=start_time,
                    triggered_by='scheduler',
                    create_by=actor,
                    update_by=actor,
                )

                # 更新DataTask状态
                with transaction.atomic():
                    task.status = 'running'
                    task.last_run_time = start_time
                    task.save(update_fields=['status', 'last_run_time', 'update_time'])

                try:
                    # 获取执行器并执行
                    executor = get_executor(etl_task, execution_log)
                    is_valid, error_msg = executor.validate()

                    if not is_valid:
                        raise ValueError(f"任务验证失败: {error_msg}")

                    # 执行任务
                    result = executor.execute()

                    # 更新执行日志
                    executor.update_execution_log(result)

                    # 同步血缘关系
                    if result['status'] == 'success':
                        executor._sync_lineage()
                        # 触发质量检查（待实现）
                        # executor._trigger_quality_check()

                    # 更新DataTask状态
                    end_time = timezone.now()
                    final_status = result['status']
                    message = result.get('error_message', '执行成功')

                    with transaction.atomic():
                        task.status = final_status
                        task.next_run_time = None if task.enabled == '1' else calc_next_run_time(
                            task.schedule_type, task.schedule_conf, base_time=end_time
                        )
                        task.save(update_fields=['status', 'next_run_time', 'update_time'])

                        # 同时更新TaskLog
                        TaskLog.objects.create(
                            task=task,
                            status=final_status,
                            start_time=start_time,
                            end_time=end_time,
                            message=message,
                            create_by=actor,
                            update_by=actor,
                        )

                    if final_status == 'failed':
                        TaskExecutor._trigger_failure_alert(task, message, actor=actor)

                    return execution_log

                except Exception as e:
                    # 异常处理
                    end_time = timezone.now()
                    error_message = str(e)
                    stack_trace = traceback.format_exc()

                    # 更新ETL执行日志
                    execution_log.status = 'failed'
                    execution_log.end_time = end_time
                    execution_log.error_message = error_message
                    execution_log.stack_trace = stack_trace
                    execution_log.save(update_fields=['status', 'end_time', 'error_message', 'stack_trace', 'update_time'])

                    # 更新DataTask状态
                    task.status = 'failed'
                    task.save(update_fields=['status', 'update_time'])

                    # 记录TaskLog
                    TaskLog.objects.create(
                        task=task,
                        status='failed',
                        start_time=start_time,
                        end_time=end_time,
                        message=error_message,
                        create_by=actor,
                        update_by=actor,
                    )

                    TaskExecutor._trigger_failure_alert(task, error_message, actor=actor)

                    return execution_log

            except IntegrationTask.DoesNotExist:
                # ETL任务不存在，降级到原有逻辑
                pass

        # 非ETL任务的兜底逻辑（保留原有代码）
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
        message = '任务执行成功（非ETL任务）'
        try:
            # 这里可以添加其他类型任务的执行逻辑
            pass
        except Exception as e:
            final_status = 'failed'
            message = str(e)

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

