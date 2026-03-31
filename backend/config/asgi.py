"""
ASGI config for ruoyi-django project with WebSocket support via Django Channels.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.terminal.auth import JwtAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

# Import routing after Django is set up
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket handler with session auth + JWT auth support
    "websocket": AuthMiddlewareStack(
        JwtAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})

