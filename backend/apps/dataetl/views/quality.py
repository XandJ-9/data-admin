from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLQualityRule, ETLQualityResult
from ..serializers import (
    ETLQualityRuleSerializer, ETLQualityRuleCreateSerializer,
    ETLQualityResultSerializer,
)
from ..services import QualityService

_FORBIDDEN = lambda msg: Response({'code': 403, 'msg': msg}, status=status.HTTP_403_FORBIDDEN)


class ETLQualityRuleViewSet(BaseViewSet):
    queryset = ETLQualityRule.objects.all()
    serializer_class = ETLQualityRuleSerializer
    create_serializer_class = ETLQualityRuleCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        p = self.request.query_params
        if p.get('ruleName'):
            queryset = queryset.filter(rule_name__icontains=p['ruleName'])
        if p.get('ruleCode'):
            queryset = queryset.filter(rule_code__icontains=p['ruleCode'])
        if p.get('ruleType'):
            queryset = queryset.filter(rule_type=p['ruleType'])
        if p.get('tableId'):
            queryset = queryset.filter(table_id=p['tableId'])
        if p.get('enabled') is not None:
            queryset = queryset.filter(enabled=p['enabled'].lower() == 'true')
        return queryset

    @action(detail=False, methods=['post'], url_path='test')
    def test_rule(self, request):
        rule_id = request.data.get('ruleId')
        task_id = request.data.get('taskId')
        if not rule_id or not task_id:
            return Response({'code': 400, 'msg': '请提供规则ID和任务ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ..models import ETLTask
            rule = ETLQualityRule.objects.get(id=rule_id)
            task = ETLTask.objects.get(id=task_id)
            passed, result = QualityService()._check_rule(rule, task)
            return self.data({'passed': passed, 'result': result})
        except ETLQualityRule.DoesNotExist:
            return Response({'code': 404, 'msg': '质检规则不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'code': 500, 'msg': f'规则测试失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ETLQualityResultViewSet(BaseViewSet):
    queryset = ETLQualityResult.objects.all()
    serializer_class = ETLQualityResultSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        p = self.request.query_params
        if p.get('taskId'):
            queryset = queryset.filter(task_id=p['taskId'])
        if p.get('executionId'):
            queryset = queryset.filter(execution_id=p['executionId'])
        if p.get('ruleId'):
            queryset = queryset.filter(rule_id=p['ruleId'])
        if p.get('status'):
            queryset = queryset.filter(status=p['status'])
        return queryset

    def create(self, request, *args, **kwargs):
        return _FORBIDDEN('质检结果由系统自动生成，不允许手动创建')

    def update(self, request, *args, **kwargs):
        return _FORBIDDEN('质检结果不允许修改')

    def destroy(self, request, *args, **kwargs):
        return _FORBIDDEN('质检结果不允许删除')
