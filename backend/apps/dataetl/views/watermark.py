from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLWatermark
from ..serializers import ETLWatermarkSerializer

_FORBIDDEN = lambda msg: Response({'code': 403, 'msg': msg}, status=status.HTTP_403_FORBIDDEN)


class ETLWatermarkViewSet(BaseViewSet):
    queryset = ETLWatermark.objects.all()
    serializer_class = ETLWatermarkSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        task_id = self.request.query_params.get('taskId')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset

    def create(self, request, *args, **kwargs):
        return _FORBIDDEN('水印由系统自动管理，不允许手动创建')

    def update(self, request, *args, **kwargs):
        return _FORBIDDEN('水印由系统自动管理，不允许手动修改')

    def destroy(self, request, *args, **kwargs):
        return _FORBIDDEN('水印不允许删除')

    @action(detail=False, methods=['get'], url_path='by-task')
    def get_watermark_by_task(self, request):
        task_id = request.query_params.get('taskId')
        if not task_id:
            return Response({'code': 400, 'msg': '请提供任务ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            watermark = ETLWatermark.objects.filter(task_id=task_id).order_by('-update_time').first()
            if watermark:
                return self.data(ETLWatermarkSerializer(watermark).data)
            return self.data({'watermarkValue': None, 'message': '该任务暂无水印记录'})
        except Exception as e:
            return Response({'code': 500, 'msg': f'获取水印失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
