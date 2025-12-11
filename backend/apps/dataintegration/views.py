from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission

from .models import IntegrationTask
from .serializers import (
    IntegrationTaskSerializer,
    IntegrationTaskQuerySerializer,
    IntegrationTaskCreateSerializer,
    IntegrationTaskUpdateSerializer,
)


class IntegrationTaskViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = IntegrationTask.objects.filter(del_flag='0').order_by('-update_time')
    serializer_class = IntegrationTaskSerializer
    update_body_serializer_class = IntegrationTaskUpdateSerializer
    update_body_id_field = 'taskId'

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        name = params.get('taskName') or params.get('name')
        if name:
            qs = qs.filter(name__icontains=name)
        t = params.get('taskType') or params.get('type')
        if t:
            qs = qs.filter(type=t)
        status = params.get('status')
        if status in ('0', '1'):
            qs = qs.filter(status=status)
        return qs

    def list(self, request, *args, **kwargs):
        q = IntegrationTaskQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return self.error('查询参数错误')
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        ser = IntegrationTaskCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        return self.data(ser.data)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        ser = IntegrationTaskUpdateSerializer(instance=obj, data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_update(ser)
        return self.data(ser.data)
