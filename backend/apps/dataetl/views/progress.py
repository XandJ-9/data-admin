from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.views.core import BaseViewSet

from ..models import ETLExecutionProgress
from ..serializers import ETLExecutionProgressSerializer

_FORBIDDEN = lambda msg: Response({'code': 403, 'msg': msg}, status=status.HTTP_403_FORBIDDEN)


class ETLExecutionProgressViewSet(BaseViewSet):
    queryset = ETLExecutionProgress.objects.all()
    serializer_class = ETLExecutionProgressSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        execution_id = self.request.query_params.get('executionId')
        if execution_id:
            queryset = queryset.filter(execution__execution_id=execution_id)
        return queryset

    def create(self, request, *args, **kwargs):
        return _FORBIDDEN('执行进度由系统自动管理')

    def update(self, request, *args, **kwargs):
        return _FORBIDDEN('执行进度由系统自动管理')

    def destroy(self, request, *args, **kwargs):
        return _FORBIDDEN('执行进度不允许删除')

    @action(detail=False, methods=['get'], url_path='by-execution')
    def get_by_execution(self, request):
        execution_id = request.query_params.get('executionId')
        if not execution_id:
            return Response({'code': 400, 'msg': '请提供执行ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            progress = ETLExecutionProgress.objects.filter(
                execution__execution_id=execution_id
            ).first()
            if progress:
                return self.data(ETLExecutionProgressSerializer(progress).data)
            return self.data({'message': '暂无进度信息'})
        except Exception as e:
            return Response({'code': 500, 'msg': f'获取进度失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
