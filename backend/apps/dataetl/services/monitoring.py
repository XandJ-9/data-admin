"""
MonitoringService - ETL监控服务

提供执行监控、统计分析、告警发送等功能
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q, F, Sum
from django.utils import timezone

from ..models import ETLTask, ETLExecutionLog, ETLExecutionProgress

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    ETL监控服务
    提供任务执行监控、统计分析、告警等功能
    """

    def __init__(self):
        pass

    def get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """
        获取执行指标

        Args:
            execution_id: 执行ID

        Returns:
            执行指标字典，包含：
            - status: 执行状态
            - progress: 进度百分比
            - processedRows: 已处理行数
            - totalRows: 总行数
            - speed: 处理速度
            - estimatedRemaining: 预计剩余时间
            - startTime: 开始时间
            - endTime: 结束时间
        """
        try:
            execution = ETLExecutionLog.objects.get(execution_id=execution_id)
        except ETLExecutionLog.DoesNotExist:
            return {
                'error': '执行记录不存在'
            }

        metrics = {
            'status': execution.status,
            'progress': 0,
            'processedRows': 0,
            'totalRows': 0,
            'speed': 0,
            'estimatedRemaining': 0,
            'startTime': execution.start_time,
            'endTime': execution.end_time,
        }

        # 尝试获取进度信息
        try:
            progress = ETLExecutionProgress.objects.get(execution=execution)
            metrics.update({
                'progress': progress.progress_percentage,
                'processedRows': progress.processed_rows,
                'totalRows': progress.total_rows,
                'speed': progress.speed_rows_per_sec,
                'estimatedRemaining': progress.estimated_remaining_seconds,
                'currentStage': progress.current_stage,
                'heartbeat': progress.heartbeat_time,
            })
        except ETLExecutionProgress.DoesNotExist:
            pass

        return metrics

    def get_task_statistics(self, task_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取任务统计信息

        Args:
            task_id: 任务ID
            days: 统计天数

        Returns:
            统计信息字典，包含：
            - totalExecutions: 总执行次数
            - successCount: 成功次数
            - failedCount: 失败次数
            - successRate: 成功率
            - avgDuration: 平均执行时长
            - totalRows: 总处理行数
        """
        try:
            task = ETLTask.objects.get(id=task_id)
        except ETLTask.DoesNotExist:
            return {
                'error': '任务不存在'
            }

        start_date = timezone.now() - timedelta(days=days)

        executions = ETLExecutionLog.objects.filter(
            task=task,
            create_time__gte=start_date,
        )

        total_executions = executions.count()
        success_count = executions.filter(status='success').count()
        failed_count = executions.filter(status='failed').count()

        # 计算平均执行时长
        avg_duration = executions.filter(
            status='success',
            duration_seconds__isnull=False
        ).aggregate(avg=Avg('duration_seconds'))['avg'] or 0

        # 计算成功率
        success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0

        # 统计总处理行数
        total_rows = executions.filter(
            status='success',
            total_rows__isnull=False
        ).aggregate(total=Sum('total_rows'))['total'] or 0

        return {
            'taskId': task_id,
            'taskName': task.task_name,
            'totalExecutions': total_executions,
            'successCount': success_count,
            'failedCount': failed_count,
            'successRate': round(success_rate, 2),
            'avgDuration': round(avg_duration, 2) if avg_duration else 0,
            'totalRows': total_rows,
            'dateRange': {
                'start': start_date,
                'end': timezone.now(),
                'days': days,
            }
        }

    def get_dashboard_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取仪表盘统计信息

        Args:
            days: 统计天数

        Returns:
            仪表盘统计信息
        """
        start_date = timezone.now() - timedelta(days=days)

        executions = ETLExecutionLog.objects.filter(
            create_time__gte=start_date,
        )

        total_executions = executions.count()
        success_executions = executions.filter(status='success').count()
        failed_executions = executions.filter(status='failed').count()
        running_executions = executions.filter(status='running').count()

        # 平均执行时长
        avg_duration = executions.filter(
            status='success',
            duration_seconds__isnull=False
        ).aggregate(avg=Avg('duration_seconds'))['avg'] or 0

        # 总任务数
        total_tasks = ETLTask.objects.count()
        active_tasks = ETLTask.objects.filter(status='0').count()

        # 最近24小时的执行趋势
        last_24h = timezone.now() - timedelta(hours=24)
        last_24h_executions = executions.filter(create_time__gte=last_24h)

        return {
            'overview': {
                'totalExecutions': total_executions,
                'successExecutions': success_executions,
                'failedExecutions': failed_executions,
                'runningExecutions': running_executions,
                'successRate': round(success_executions / total_executions * 100, 2) if total_executions > 0 else 0,
            },
            'tasks': {
                'totalTasks': total_tasks,
                'activeTasks': active_tasks,
                'inactiveTasks': total_tasks - active_tasks,
            },
            'performance': {
                'avgDuration': round(avg_duration, 2) if avg_duration else 0,
            },
            'last24h': {
                'totalExecutions': last_24h_executions.count(),
                'successExecutions': last_24h_executions.filter(status='success').count(),
            },
            'dateRange': {
                'start': start_date,
                'end': timezone.now(),
                'days': days,
            }
        }

    def get_slowest_tasks(self, limit: int = 10, days: int = 7) -> list:
        """
        获取执行最慢的任务列表

        Args:
            limit: 返回数量限制
            days: 统计天数

        Returns:
            任务列表，按平均执行时长降序排列
        """
        start_date = timezone.now() - timedelta(days=days)

        tasks = ETLTask.objects.filter(
            execution_logs__create_time__gte=start_date,
            execution_logs__status='success',
        ).annotate(
            avg_duration=Avg('execution_logs__duration_seconds'),
            execution_count=Count('execution_logs'),
        ).filter(
            avg_duration__isnull=False,
        ).order_by('-avg_duration')[:limit]

        return [
            {
                'taskId': task.id,
                'taskName': task.task_name,
                'taskCode': task.task_code,
                'avgDuration': round(task.avg_duration, 2) if task.avg_duration else 0,
                'executionCount': task.execution_count,
            }
            for task in tasks
        ]

    def get_error_prone_tasks(self, limit: int = 10, days: int = 7) -> list:
        """
        获取最容易失败的任务列表

        Args:
            limit: 返回数量限制
            days: 统计天数

        Returns:
            任务列表，按失败率降序排列
        """
        start_date = timezone.now() - timedelta(days=days)

        tasks = ETLTask.objects.filter(
            execution_logs__create_time__gte=start_date,
        ).annotate(
            total_executions=Count('execution_logs'),
            failed_executions=Count('execution_logs', filter=Q(execution_logs__status='failed')),
        ).filter(
            total_executions__gte=5,  # 至少执行5次
        ).order_by('-failed_executions')[:limit]

        return [
            {
                'taskId': task.id,
                'taskName': task.task_name,
                'taskCode': task.task_code,
                'totalExecutions': task.total_executions,
                'failedExecutions': task.failed_executions,
                'failureRate': round(task.failed_executions / task.total_executions * 100, 2),
            }
            for task in tasks
        ]

    def send_alert(self, execution: ETLExecutionLog, alert_type: str, message: str):
        """
        发送告警

        Args:
            execution: 执行日志实例
            alert_type: 告警类型 (task_failed, quality_failed, timeout等)
            message: 告警消息
        """
        from django.conf import settings

        alert_config = getattr(settings, 'ETL_ALERT_CONFIG', {})

        # 发送钉钉告警
        if alert_config.get('dingtalk', {}).get('enabled'):
            self._send_dingtalk_alert(execution, alert_type, message, alert_config['dingtalk'])

        # 发送邮件告警
        if alert_config.get('email', {}).get('enabled'):
            self._send_email_alert(execution, alert_type, message, alert_config['email'])

        # 发送飞书告警
        if alert_config.get('feishu', {}).get('enabled'):
            self._send_feishu_alert(execution, alert_type, message, alert_config['feishu'])

    def _send_dingtalk_alert(self, execution: ETLExecutionLog, alert_type: str,
                           message: str, config: Dict[str, Any]):
        """
        发送钉钉告警
        """
        import requests
        import json

        webhook = config.get('webhook')
        if not webhook:
            logger.warning("钉钉webhook未配置")
            return

        # 构建告警消息
        text = f"""
        【ETL任务告警】

        任务名称: {execution.task.task_name}
        任务编码: {execution.task.task_code}
        执行ID: {execution.execution_id}
        执行状态: {execution.get_status_display()}
        告警类型: {alert_type}
        告警消息: {message}
        开始时间: {execution.start_time}
        结束时间: {execution.end_time}

        请及时处理！
        """

        data = {
            "msgtype": "text",
            "text": {
                "content": text
            }
        }

        try:
            response = requests.post(webhook, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"钉钉告警发送成功: {execution.execution_id}")
            else:
                logger.error(f"钉钉告警发送失败: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"钉钉告警发送异常: {str(e)}", exc_info=True)

    def _send_email_alert(self, execution: ETLExecutionLog, alert_type: str,
                          message: str, config: Dict[str, Any]):
        """
        发送邮件告警
        """
        from django.core.mail import send_mail

        subject = f"【ETL告警】{execution.task.task_name} - {alert_type}"
        body = f"""
任务名称: {execution.task.task_name}
任务编码: {execution.task.task_code}
执行ID: {execution.execution_id}
执行状态: {execution.get_status_display()}
告警类型: {alert_type}
告警消息: {message}
开始时间: {execution.start_time}
结束时间: {execution.end_time}

请及时处理！
        """

        recipients = config.get('recipients', [])
        if not recipients:
            logger.warning("邮件收件人未配置")
            return

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=config.get('from_email'),
                recipient_list=recipients,
                fail_silently=False,
            )
            logger.info(f"邮件告警发送成功: {execution.execution_id}")
        except Exception as e:
            logger.error(f"邮件告警发送失败: {str(e)}", exc_info=True)

    def _send_feishu_alert(self, execution: ETLExecutionLog, alert_type: str,
                          message: str, config: Dict[str, Any]):
        """
        发送飞书告警
        """
        import requests

        webhook = config.get('webhook')
        if not webhook:
            logger.warning("飞书webhook未配置")
            return

        # 构建飞书消息格式
        data = {
            "msg_type": "text",
            "content": {
                "text": f"""【ETL任务告警】
任务名称: {execution.task.task_name}
任务编码: {execution.task.task_code}
执行ID: {execution.execution_id}
执行状态: {execution.get_status_display()}
告警类型: {alert_type}
告警消息: {message}
开始时间: {execution.start_time}
结束时间: {execution.end_time}

请及时处理！"""
            }
        }

        try:
            response = requests.post(webhook, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"飞书告警发送成功: {execution.execution_id}")
            else:
                logger.error(f"飞书告警发送失败: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"飞书告警发送异常: {str(e)}", exc_info=True)
