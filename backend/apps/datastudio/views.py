from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.common.pagination import StandardPagination
from .models import DataStudioTask
from .serializers import DataStudioTaskSerializer

from apps.system.views import BaseViewSet

class DataStudioTaskViewSet(BaseViewSet):
    queryset = DataStudioTask.objects.all()
    serializer_class = DataStudioTaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        task_type = self.request.query_params.get('type')
        status = self.request.query_params.get('status')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if task_type:
            queryset = queryset.filter(type=task_type)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-create_time')
