from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ScriptViewSet, ScriptExecutionViewSet, DataDevDirectoryViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'scripts', ScriptViewSet, basename='datadev-script')
router.register(r'executions', ScriptExecutionViewSet, basename='datadev-execution')
router.register(r'directories', DataDevDirectoryViewSet, basename='datadev-directory')

urlpatterns = [
    path('', include(router.urls)),
]
