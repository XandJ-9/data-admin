"""
ETL URL Configuration

This module defines URL routes for ETL task management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ETLTaskViewSet,
    ETLFieldMappingViewSet,
    ETLExecutionLogViewSet,
    ETLWatermarkViewSet,
    ETLTaskTemplateViewSet,
    ETLQualityRuleViewSet,
    ETLQualityResultViewSet,
    ETLExecutionProgressViewSet,
)

# Create router
router = DefaultRouter(trailing_slash=False)

# Register ViewSets
router.register(r'tasks', ETLTaskViewSet, basename='etl-task')
router.register(r'field-mappings', ETLFieldMappingViewSet, basename='etl-field-mapping')
router.register(r'execution-logs', ETLExecutionLogViewSet, basename='etl-execution-log')
router.register(r'watermarks', ETLWatermarkViewSet, basename='etl-watermark')
router.register(r'templates', ETLTaskTemplateViewSet, basename='etl-task-template')
router.register(r'quality-rules', ETLQualityRuleViewSet, basename='etl-quality-rule')
router.register(r'quality-results', ETLQualityResultViewSet, basename='etl-quality-result')
router.register(r'execution-progress', ETLExecutionProgressViewSet, basename='etl-execution-progress')

urlpatterns = [
    path('', include(router.urls)),
]
