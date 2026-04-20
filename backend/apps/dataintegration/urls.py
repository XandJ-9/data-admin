from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DataIntegrationTaskViewSet, IntegrationExecutionLogViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'task', DataIntegrationTaskViewSet, basename='dataintegration-task')
router.register(r'executionlog', IntegrationExecutionLogViewSet, basename='dataintegration-executionlog')

urlpatterns = [
    path('', include(router.urls)),
]
