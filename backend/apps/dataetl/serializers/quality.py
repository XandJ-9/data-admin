from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from ..models import ETLQualityRule, ETLQualityResult


class ETLQualityRuleSerializer(BaseModelSerializer):
    ruleId = serializers.IntegerField(source='id', read_only=True)
    ruleName = serializers.CharField(source='rule_name')
    ruleCode = serializers.CharField(source='rule_code')
    ruleType = serializers.CharField(source='rule_type')
    tableId = serializers.IntegerField(source='table_id')
    tableName = serializers.CharField(source='table.table_name', read_only=True, required=False)
    fieldName = serializers.CharField(source='field_name', required=False, allow_blank=True, allow_null=True)
    ruleConfig = serializers.JSONField(source='rule_config')
    sqlExpression = serializers.CharField(source='sql_expression', required=False, allow_blank=True, allow_null=True)
    thresholdMin = serializers.FloatField(source='threshold_min', required=False, allow_null=True)
    thresholdMax = serializers.FloatField(source='threshold_max', required=False, allow_null=True)
    errorLevel = serializers.CharField(source='error_level')
    enabled = serializers.BooleanField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ETLQualityRule
        fields = [
            'ruleId', 'ruleName', 'ruleCode', 'ruleType', 'tableId', 'tableName',
            'fieldName', 'ruleConfig', 'sqlExpression', 'thresholdMin', 'thresholdMax',
            'errorLevel', 'enabled', 'description',
        ]


class ETLQualityRuleQuerySerializer(serializers.Serializer):
    ruleName = serializers.CharField(required=False, allow_blank=True)
    ruleCode = serializers.CharField(required=False, allow_blank=True)
    ruleType = serializers.CharField(required=False, allow_blank=True)
    tableId = serializers.IntegerField(required=False)
    enabled = serializers.BooleanField(required=False)


class ETLQualityRuleCreateSerializer(ETLQualityRuleSerializer):
    ruleName = serializers.CharField(source='rule_name', required=True)


# ==================== ETLQualityResult Serializers ====================

class ETLQualityResultSerializer(serializers.ModelSerializer):
    resultId = serializers.IntegerField(source='id', read_only=True)
    ruleId = serializers.IntegerField(source='rule_id')
    ruleName = serializers.CharField(source='rule.rule_name', read_only=True, required=False)
    taskId = serializers.IntegerField(source='task_id')
    taskName = serializers.CharField(source='task.task_name', read_only=True, required=False)
    executionId = serializers.CharField(source='execution_id')
    checkTime = serializers.DateTimeField(source='check_time', read_only=True)
    status = serializers.CharField()
    totalRows = serializers.IntegerField(source='total_rows')
    errorRows = serializers.IntegerField(source='error_rows')
    warningRows = serializers.IntegerField(source='warning_rows')
    errorDetails = serializers.JSONField(source='error_details')
    passRate = serializers.FloatField(source='pass_rate')
    checkDuration = serializers.IntegerField(source='check_duration', allow_null=True, required=False)

    class Meta:
        model = ETLQualityResult
        fields = [
            'resultId', 'ruleId', 'ruleName', 'taskId', 'taskName', 'executionId',
            'checkTime', 'status', 'totalRows', 'errorRows', 'warningRows',
            'errorDetails', 'passRate', 'checkDuration',
        ]


class ETLQualityResultQuerySerializer(serializers.Serializer):
    taskId = serializers.IntegerField(required=False)
    executionId = serializers.CharField(required=False, allow_blank=True)
    ruleId = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
