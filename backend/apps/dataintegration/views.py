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
        if not ser.is_valid():
            # 统一返回首个错误
            try:
                first_err = next(iter(ser.errors.values()))[0]
                return self.error(str(first_err))
            except Exception:
                return self.error('参数错误')
        data = ser.validated_data
        model = IntegrationTask(
            name=data['taskName'],
            type=data['taskType'],
            schedule=data.get('schedule') or {},
            detail=data.get('detail') or {},
            status=data.get('status', '0'),
            remark=data.get('remark', ''),
        )
        try:
            model.save()
            out = self.get_serializer(model).data
            return self.data(out)
        except Exception as e:
            return self.error(str(e))

    def update(self, request, *args, **kwargs):
        ser = IntegrationTaskUpdateSerializer(data=request.data)
        if not ser.is_valid():
            try:
                first_err = next(iter(ser.errors.values()))[0]
                return self.error(str(first_err))
            except Exception:
                return self.error('参数错误')
        data = ser.validated_data
        pk = kwargs.get('pk') or data.get('taskId')
        try:
            obj = IntegrationTask.objects.get(pk=pk, del_flag='0')
        except IntegrationTask.DoesNotExist:
            return self.not_found('任务不存在')
        obj.name = data['taskName']
        obj.type = data['taskType']
        obj.schedule = data.get('schedule') or {}
        obj.detail = data.get('detail') or {}
        obj.status = data.get('status', '0')
        obj.remark = data.get('remark', '')
        try:
            obj.save()
            out = self.get_serializer(obj).data
            return self.data(out)
        except Exception as e:
            return self.error(str(e))
