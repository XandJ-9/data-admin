from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationTaskViewSet,
    TaskExecutionLogViewSet,
    DataLineageViewSet,
    IntegrationTaskVersionViewSet
)

router = DefaultRouter(trailing_slash=False)
router.register(r'task', IntegrationTaskViewSet, basename='dataetl-task')
router.register(r'executionlog', TaskExecutionLogViewSet, basename='dataetl-executionlog')
router.register(r'lineage', DataLineageViewSet, basename='dataetl-lineage')
router.register(r'version', IntegrationTaskVersionViewSet, basename='dataetl-version')

urlpatterns = [
    path('', include(router.urls)),
]

