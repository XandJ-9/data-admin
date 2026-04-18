from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TaskDependencyViewSet, TaskInstanceViewSet, TaskViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'task', TaskViewSet, basename='datatask-task')
router.register(r'task-dependency', TaskDependencyViewSet, basename='datatask-task-dependency')
router.register(r'task-instance', TaskInstanceViewSet, basename='datatask-task-instance')

urlpatterns = [
    path('', include(router.urls)),
]
