from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLTaskTemplate
from ..serializers import ETLTaskSerializer, ETLTaskTemplateSerializer, ETLTaskTemplateCreateSerializer
from ..services import TaskService


class ETLTaskTemplateViewSet(BaseViewSet):
    queryset = ETLTaskTemplate.objects.all()
    serializer_class = ETLTaskTemplateSerializer
    create_serializer_class = ETLTaskTemplateCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        p = self.request.query_params
        if p.get('templateName'):
            queryset = queryset.filter(template_name__icontains=p['templateName'])
        if p.get('templateCode'):
            queryset = queryset.filter(template_code__icontains=p['templateCode'])
        if p.get('taskType'):
            queryset = queryset.filter(task_type=p['taskType'])
        if p.get('category'):
            queryset = queryset.filter(category__icontains=p['category'])
        if p.get('isSystem') is not None:
            queryset = queryset.filter(is_system=p['isSystem'].lower() == 'true')
        return queryset

    @action(detail=False, methods=['get'], url_path='system')
    def list_system_templates(self, request):
        return self.data(ETLTaskTemplateSerializer(self.get_queryset().filter(is_system=True), many=True).data)

    @action(detail=False, methods=['get'], url_path='user')
    def list_user_templates(self, request):
        return self.data(ETLTaskTemplateSerializer(self.get_queryset().filter(is_system=False), many=True).data)

    @action(detail=False, methods=['post'], url_path='create-task')
    def create_task_from_template(self, request):
        template_id = request.data.get('templateId')
        if not template_id:
            return Response({'code': 400, 'msg': '请提供模板ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = TaskService.create_task_from_template(template_id, request.data.get('params', {}))
            return self.data(ETLTaskSerializer(task).data)
        except Exception as e:
            return Response({'code': 500, 'msg': f'创建任务失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='increment-usage')
    def increment_usage(self, request, pk=None):
        template = self.get_object()
        template.usage_count += 1
        template.save(update_fields=['usage_count'])
        return self.data({'message': '使用次数已更新', 'usageCount': template.usage_count})
