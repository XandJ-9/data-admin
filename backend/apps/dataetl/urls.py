"""
ETL URL Configuration

This module defines URL routes for ETL task management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ETLTaskViewSet,
    ETLFieldMappingViewSet,
    ETLExecutionLogViewSet
)

# Create router
router = DefaultRouter(trailing_slash=False)

# Register ViewSets
router.register(r'tasks', ETLTaskViewSet, basename='etl-task')
router.register(r'field-mappings', ETLFieldMappingViewSet, basename='etl-field-mapping')
router.register(r'execution-logs', ETLExecutionLogViewSet, basename='etl-execution-log')

urlpatterns = [
    path('', include(router.urls)),
]
