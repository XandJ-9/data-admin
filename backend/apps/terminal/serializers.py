"""
Serializers for Terminal API
"""
from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import TerminalSession, TerminalCommand


class TerminalSessionSerializer(BaseModelSerializer):
    """Serializer for TerminalSession"""
    userName = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TerminalSession
        fields = ['id', 'sessionId', 'status', 'host', 'userName', 'createTime', 'createBy', 'remark']
        extra_kwargs = {
            'sessionId': {'source': 'session_id'},
            'createTime': {'source': 'create_time'},
            'createBy': {'source': 'create_by'},
        }


class TerminalCommandSerializer(BaseModelSerializer):
    """Serializer for TerminalCommand"""
    sessionId = serializers.CharField(source='session.session_id', read_only=True)
    userName = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TerminalCommand
        fields = ['id', 'sessionId', 'command', 'output', 'exitCode', 'executionTime', 'userName', 'createTime']
        extra_kwargs = {
            'sessionId': {'source': 'session.session_id'},
            'exitCode': {'source': 'exit_code'},
            'executionTime': {'source': 'execution_time'},
            'userName': {'source': 'user.username'},
            'createTime': {'source': 'create_time'},
        }
