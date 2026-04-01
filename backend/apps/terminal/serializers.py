"""
Serializers for Terminal API
"""
from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import TerminalSession, TerminalCommand


class TerminalSessionSerializer(BaseModelSerializer):
    """Serializer for TerminalSession"""
    userName = serializers.CharField(source='user.username', read_only=True)
    commandCount = serializers.IntegerField(source='command_count', read_only=True, default=0)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = TerminalSession
        fields = ['id', 'sessionId', 'status', 'host', 'userName',
                  'commandCount', 'duration', 'createTime', 'updateTime', 'createBy', 'remark']
        extra_kwargs = {
            'sessionId': {'source': 'session_id'},
            'createTime': {'source': 'create_time'},
            'updateTime': {'source': 'update_time'},
            'createBy': {'source': 'create_by'},
        }

    def get_duration(self, obj):
        if obj.create_time and obj.update_time:
            delta = obj.update_time - obj.create_time
            return int(delta.total_seconds())
        return None


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
