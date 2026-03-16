"""
QualityService - 数据质量服务

提供数据质量检查、质检规则管理等功能
"""

import logging
import time
from typing import List, Dict, Any, Tuple
from django.db import connection
from django.utils import timezone

from ..models import ETLTask, ETLQualityRule, ETLQualityResult, ETLExecutionLog

logger = logging.getLogger(__name__)


class QualityService:
    """
    数据质量服务
    提供数据质量检查、规则验证等功能
    """

    def __init__(self):
        pass

    def run_pre_check(self, task: ETLTask) -> Tuple[bool, List[str]]:
        """
        执行前质检

        在任务执行前进行数据质量检查

        Args:
            task: ETL任务实例

        Returns:
            (是否通过, 错误信息列表)
        """
        quality_rules = task.quality_config

        if not quality_rules:
            # 如果没有配置质检规则，直接通过
            return True, []

        errors = []
        warnings = []

        for rule_config in quality_rules:
            try:
                rule_id = rule_config.get('ruleId')
                if not rule_id:
                    continue

                rule = ETLQualityRule.objects.get(id=rule_id)

                if not rule.enabled:
                    continue

                # 执行质检
                passed, result = self._check_rule(rule, task)

                if not passed:
                    if rule.error_level == 'error':
                        errors.append(f"质检规则失败: {rule.rule_name} - {result.get('message', '')}")
                    else:
                        warnings.append(f"质检规则警告: {rule.rule_name} - {result.get('message', '')}")

                        # 如果配置为警告时停止
                        if rule_config.get('stopOnWarning', False):
                            errors.append(f"质检警告被配置为停止: {rule.rule_name}")

            except ETLQualityRule.DoesNotExist:
                logger.error(f"质检规则不存在: {rule_id}")
                errors.append(f"质检规则不存在: {rule_id}")
            except Exception as e:
                logger.error(f"质检执行失败: {str(e)}", exc_info=True)
                errors.append(f"质检执行失败: {str(e)}")

        return len(errors) == 0, errors + warnings

    def run_post_check(self, task: ETLTask, execution_id: str):
        """
        执行后质检

        在任务执行后进行数据质量检查，并保存质检结果

        Args:
            task: ETL任务实例
            execution_id: 执行ID
        """
        quality_rules = task.quality_config

        if not quality_rules:
            return

        try:
            execution_log = ETLExecutionLog.objects.get(execution_id=execution_id)
        except ETLExecutionLog.DoesNotExist:
            logger.error(f"执行记录不存在: {execution_id}")
            return

        for rule_config in quality_rules:
            try:
                rule_id = rule_config.get('ruleId')
                if not rule_id:
                    continue

                rule = ETLQualityRule.objects.get(id=rule_id)

                if not rule.enabled:
                    continue

                # 执行质检并保存结果
                start_time = time.time()
                passed, result = self._check_rule(rule, task)
                duration = int((time.time() - start_time) * 1000)  # 毫秒

                # 保存质检结果
                self._save_quality_result(
                    rule=rule,
                    task=task,
                    execution_id=execution_id,
                    passed=passed,
                    result=result,
                    duration=duration
                )

                # 如果质检失败且配置为停止，触发告警
                if not passed and rule_config.get('stopOnFailure', False):
                    self._trigger_alert(rule, execution_log, result)

            except Exception as e:
                logger.error(f"执行后质检失败: {str(e)}", exc_info=True)

    def _check_rule(self, rule: ETLQualityRule, task: ETLTask) -> Tuple[bool, Dict[str, Any]]:
        """
        执行单条质检规则

        Args:
            rule: 质检规则实例
            task: ETL任务实例

        Returns:
            (是否通过, 检查结果)
        """
        try:
            if rule.rule_type == 'null_check':
                return self._check_null(rule, task)
            elif rule.rule_type == 'unique_check':
                return self._check_unique(rule, task)
            elif rule.rule_type == 'range_check':
                return self._check_range(rule, task)
            elif rule.rule_type == 'custom_sql':
                return self._check_custom_sql(rule, task)
            else:
                return True, {'message': f'未实现的规则类型: {rule.rule_type}'}

        except Exception as e:
            logger.error(f"质检规则执行失败: {str(e)}", exc_info=True)
            return False, {'message': f'规则执行异常: {str(e)}'}

    def _check_null(self, rule: ETLQualityRule, task: ETLTask) -> Tuple[bool, Dict[str, Any]]:
        """
        空值检查

        检查指定字段是否存在空值
        """
        table_name = rule.table.table_name

        # 使用Django的quote_name防止SQL注入
        from django.db import connection

        # 构建SQL查询 - 使用quote_name防止SQL注入
        quoted_table = connection.ops.quote_name(table_name)

        if rule.field_name:
            quoted_field = connection.ops.quote_name(rule.field_name)
            sql = f"""
                SELECT
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN {quoted_field} IS NULL THEN 1 ELSE 0 END) as null_rows
                FROM {quoted_table}
            """
        else:
            # 检查全表
            sql = f"""
                SELECT
                    COUNT(*) as total_rows,
                    0 as null_rows
                FROM {quoted_table}
            """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()

        total_rows, null_rows = result

        passed = null_rows == 0
        pass_rate = ((total_rows - null_rows) / total_rows * 100) if total_rows > 0 else 100

        return passed, {
            'total_rows': total_rows,
            'error_rows': null_rows,
            'pass_rate': pass_rate,
            'message': f'空值检查: {null_rows}/{total_rows} 行为空' if null_rows > 0 else '无空值'
        }

    def _check_unique(self, rule: ETLQualityRule, task: ETLTask) -> Tuple[bool, Dict[str, Any]]:
        """
        唯一性检查

        检查指定字段是否存在重复值
        """
        table_name = rule.table.table_name

        if not rule.field_name:
            return True, {'message': '未指定检查字段'}

        # 使用Django的quote_name防止SQL注入
        quoted_table = connection.ops.quote_name(table_name)
        quoted_field = connection.ops.quote_name(rule.field_name)

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT {quoted_field}) as unique_rows
                FROM {quoted_table}
            """)
            total_rows, unique_rows = cursor.fetchone()

        duplicate_rows = total_rows - unique_rows
        passed = duplicate_rows == 0
        pass_rate = (unique_rows / total_rows * 100) if total_rows > 0 else 100

        return passed, {
            'total_rows': total_rows,
            'unique_rows': unique_rows,
            'error_rows': duplicate_rows,
            'pass_rate': pass_rate,
            'message': f'唯一性检查: {duplicate_rows} 行重复' if duplicate_rows > 0 else '无重复值'
        }

    def _check_range(self, rule: ETLQualityRule, task: ETLTask) -> Tuple[bool, Dict[str, Any]]:
        """
        范围检查

        检查指定字段的值是否在指定范围内
        """
        table_name = rule.table.table_name

        if not rule.field_name:
            return True, {'message': '未指定检查字段'}

        # 使用Django的quote_name防止SQL注入
        quoted_table = connection.ops.quote_name(table_name)
        quoted_field = connection.ops.quote_name(rule.field_name)

        # 构建SQL查询
        conditions = []
        params = []

        if rule.threshold_min is not None:
            conditions.append(f"{quoted_field} < %s")
            params.append(rule.threshold_min)

        if rule.threshold_max is not None:
            conditions.append(f"{quoted_field} > %s")
            params.append(rule.threshold_max)

        if not conditions:
            return True, {'message': '未配置范围阈值'}

        sql = f"""
            SELECT
                COUNT(*) as total_rows,
                SUM(CASE WHEN {' OR '.join(conditions)} THEN 1 ELSE 0 END) as out_of_range_rows
            FROM {quoted_table}
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()

        total_rows, out_of_range_rows = result

        passed = out_of_range_rows == 0
        pass_rate = ((total_rows - out_of_range_rows) / total_rows * 100) if total_rows > 0 else 100

        return passed, {
            'total_rows': total_rows,
            'error_rows': out_of_range_rows,
            'pass_rate': pass_rate,
            'message': f'范围检查: {out_of_range_rows}/{total_rows} 行超出范围' if out_of_range_rows > 0 else '所有值在范围内'
        }

    def _check_custom_sql(self, rule: ETLQualityRule, task: ETLTask) -> Tuple[bool, Dict[str, Any]]:
        """
        自定义SQL检查

        执行自定义SQL进行质检
        """
        if not rule.sql_expression:
            return False, {'message': '未配置SQL表达式'}

        with connection.cursor() as cursor:
            cursor.execute(rule.sql_expression)
            result = cursor.fetchone()

        if not result or len(result) == 0:
            return False, {'message': 'SQL未返回结果'}

        # 假设SQL返回两个字段：total_rows, error_rows
        total_rows = result[0] if len(result) > 0 else 0
        error_rows = result[1] if len(result) > 1 else 0

        passed = error_rows == 0
        pass_rate = ((total_rows - error_rows) / total_rows * 100) if total_rows > 0 else 100

        return passed, {
            'total_rows': total_rows,
            'error_rows': error_rows,
            'pass_rate': pass_rate,
            'message': f'自定义SQL检查: {error_rows}/{total_rows} 行不符合规则' if error_rows > 0 else '所有行符合规则'
        }

    def _save_quality_result(self, rule: ETLQualityRule, task: ETLTask,
                            execution_id: str, passed: bool, result: Dict[str, Any],
                            duration: int):
        """
        保存质检结果
        """
        status = 'passed' if passed else 'failed'

        ETLQualityResult.objects.create(
            rule=rule,
            task=task,
            execution_id=execution_id,
            status=status,
            total_rows=result.get('total_rows', 0),
            error_rows=result.get('error_rows', 0),
            warning_rows=result.get('warning_rows', 0),
            error_details=[result.get('message', '')],
            pass_rate=result.get('pass_rate', 0),
            check_duration=duration,
        )

        logger.info(f"质检结果已保存: {rule.rule_name} - {status}")

    def _trigger_alert(self, rule: ETLQualityRule, execution: ETLExecutionLog, result: Dict[str, Any]):
        """
        触发质检告警
        """
        # TODO: 实现告警发送逻辑（钉钉、飞书、邮件等）
        logger.warning(f"质检告警触发: {rule.rule_name} - {result.get('message', '')}")

        # 示例：发送钉钉告警
        # from django.conf import settings
        # if hasattr(settings, 'ETL_ALERT_CONFIG'):
        #     dingtalk_webhook = settings.ETL_ALERT_CONFIG.get('dingtalk', {}).get('webhook')
        #     if dingtalk_webhook:
        #         self._send_dingtalk_alert(dingtalk_webhook, rule, execution, result)
