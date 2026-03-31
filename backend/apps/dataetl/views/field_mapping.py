from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLFieldMapping
from ..serializers import (
    ETLFieldMappingSerializer, ETLFieldMappingCreateSerializer, ETLFieldMappingUpdateSerializer,
)
from ..services import TaskService


class ETLFieldMappingViewSet(BaseViewSet):
    queryset = ETLFieldMapping.objects.all()
    serializer_class = ETLFieldMappingSerializer
    create_serializer_class = ETLFieldMappingCreateSerializer
    update_serializer_class = ETLFieldMappingUpdateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        p = self.request.query_params
        if p.get('taskId'):
            queryset = queryset.filter(task_id=p['taskId'])
        if p.get('sourceFieldName'):
            queryset = queryset.filter(source_field_name__icontains=p['sourceFieldName'])
        if p.get('targetFieldName'):
            queryset = queryset.filter(target_field_name__icontains=p['targetFieldName'])
        return queryset

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_create(self, request):
        mappings_data = request.data.get('mappings', [])
        if not mappings_data:
            return Response({'code': 400, 'msg': '请提供映射数据'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task_id = mappings_data[0].get('taskId') if mappings_data else None
            if not task_id:
                raise ValueError('缺少taskId')
            count = TaskService.create_field_mapping_batch(task_id, mappings_data)
            mappings = ETLFieldMapping.objects.filter(task_id=task_id)
            return self.data({
                'message': f'成功创建 {count} 个字段映射',
                'data': ETLFieldMappingSerializer(mappings, many=True).data,
            })
        except Exception as e:
            return Response({'code': 500, 'msg': f'批量创建失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
