"""
ETL模块URL配置 - 简化版
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ETLTaskViewSet, ETLExecutionViewSet, ETLTemplateViewSet

router = DefaultRouter()
# 注册ETL任务视图
router.register(r'tasks', ETLTaskViewSet, basename='etl-task')
# 注册ETL执行记录视图
router.register(r'executions', ETLExecutionViewSet, basename='etl-execution')
# 注册ETL模板视图
router.register(r'templates', ETLTemplateViewSet, basename='etl-template')

urlpatterns = [
    path('', include(router.urls)),
]
