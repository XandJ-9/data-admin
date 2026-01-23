from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DataTaskViewSet,
    TaskLogViewSet,
    AlertRuleViewSet,
    AlertRecordViewSet,
    TaskExecutionViewSet,
    TaskExecutionLogViewSet,
)

router = DefaultRouter()
router.register(r'tasks', DataTaskViewSet)
router.register(r'logs', TaskLogViewSet)
router.register(r'rules', AlertRuleViewSet)
router.register(r'alerts', AlertRecordViewSet)
router.register(r'executions', TaskExecutionViewSet)
router.register(r'execution-logs', TaskExecutionLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
