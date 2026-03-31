"""
JWT authentication middleware for Django Channels WebSocket connections.
Supports token from query string (?token=...) and Authorization header.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


User = get_user_model()


class JwtAuthMiddleware:
    """Authenticate websocket user from JWT token when present."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        token = self._extract_token(scope)

        if token:
            scope['user'] = await self._get_user_from_token(token)

        return await self.inner(scope, receive, send)

    def _extract_token(self, scope) -> str:
        # Prefer query parameter token for browser websocket clients.
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)

        token = query_params.get('token', [None])[0]
        if token:
            return token

        # Fallback to Authorization header for non-browser clients.
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization', b'').decode('utf-8')
        if auth_header.lower().startswith('bearer '):
            return auth_header[7:].strip()

        return ''

    @database_sync_to_async
    def _get_user_from_token(self, token: str):
        try:
            payload = AccessToken(token)
            user_id = payload.get('user_id')
            if not user_id:
                return AnonymousUser()
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist, ValueError, TypeError):
            return AnonymousUser()
