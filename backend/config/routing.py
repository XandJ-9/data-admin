"""
WebSocket URL routing configuration for Django Channels
"""
from django.urls import re_path
from apps.terminal.consumers import TerminalConsumer

websocket_urlpatterns = [
    re_path(r'ws/terminal/(?P<session_id>[\w-]*)/?$', TerminalConsumer.as_asgi()),
]
