"""
URL Configuration for Terminal
"""
from rest_framework.routers import DefaultRouter
from .views import TerminalSessionViewSet, TerminalCommandViewSet

router = DefaultRouter(trailing_slash='/?')
router.register(r'session', TerminalSessionViewSet, basename='terminal-session')
router.register(r'command', TerminalCommandViewSet, basename='terminal-command')

urlpatterns = router.urls
