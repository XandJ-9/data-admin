"""
REST API Views for Terminal
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.system.common import audit_log
from .models import TerminalSession, TerminalCommand
from .serializers import TerminalSessionSerializer, TerminalCommandSerializer


class TerminalSessionViewSet(BaseViewSet):
    """ViewSet for Terminal Sessions"""
    queryset = TerminalSession.objects.all()
    serializer_class = TerminalSessionSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    required_roles = None  # Allow all authenticated users, check in consumer

    def get_queryset(self):
        """Filter sessions for current user"""
        qs = super().get_queryset()
        # Show own sessions + admin can see all
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    @audit_log
    def create(self, request, *args, **kwargs):
        """Create new terminal session"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """Set user when creating session"""
        serializer.save(
            user=self.request.user,
            create_by=self.request.user.username
        )

    @action(detail=True, methods=['get'])
    def commands(self, request, pk=None):
        """Get command history for a session"""
        session = self.get_object()
        commands = session.commands.all().order_by('create_time')

        # Pagination
        page = self.paginate_queryset(commands)
        if page is not None:
            serializer = TerminalCommandSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TerminalCommandSerializer(commands, many=True)
        return Response({'code': 200, 'rows': serializer.data, 'total': commands.count()})

    @audit_log
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a terminal session"""
        session = self.get_object()
        session.status = '1'  # Disconnected
        session.update_by = request.user.username
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active sessions"""
        sessions = self.get_queryset().filter(status='0').order_by('-create_time')
        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(sessions, many=True)
        return Response({'code': 200, 'rows': serializer.data, 'total': sessions.count()})


class TerminalCommandViewSet(BaseViewSet):
    """ViewSet for Terminal Commands"""
    queryset = TerminalCommand.objects.all()
    serializer_class = TerminalCommandSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]

    def get_queryset(self):
        """Filter commands for current user"""
        qs = super().get_queryset()
        # Show own commands + admin can see all
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent commands for current user"""
        commands = self.get_queryset().order_by('-create_time')[:50]
        serializer = self.get_serializer(commands, many=True)
        return Response({'code': 200, 'rows': serializer.data})

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search commands by keyword"""
        keyword = request.data.get('keyword', '')
        commands = self.get_queryset().filter(command__icontains=keyword).order_by('-create_time')

        page = self.paginate_queryset(commands)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(commands, many=True)
        return Response({'code': 200, 'rows': serializer.data, 'total': commands.count()})
