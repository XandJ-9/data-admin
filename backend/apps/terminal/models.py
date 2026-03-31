import uuid
from django.db import models
from apps.system.models import BaseModel, User


class TerminalSession(BaseModel):
    """Web Terminal Session Model"""
    session_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4, verbose_name='Session ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    status = models.CharField(
        max_length=1,
        choices=[('0', 'Connected'), ('1', 'Disconnected')],
        default='0',
        verbose_name='Status'
    )
    host = models.CharField(max_length=100, default='localhost', verbose_name='Host')
    remark = models.TextField(blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = 'terminal_session'
        verbose_name = 'Terminal Session'
        verbose_name_plural = 'Terminal Sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['create_time']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class TerminalCommand(BaseModel):
    """Terminal Command History Model"""
    session = models.ForeignKey(TerminalSession, on_delete=models.CASCADE, related_name='commands', verbose_name='Session')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    command = models.TextField(verbose_name='Command')
    output = models.TextField(blank=True, null=True, verbose_name='Output')
    exit_code = models.IntegerField(null=True, blank=True, verbose_name='Exit Code')
    execution_time = models.FloatField(null=True, blank=True, verbose_name='Execution Time (seconds)')

    class Meta:
        db_table = 'terminal_command_history'
        verbose_name = 'Terminal Command'
        verbose_name_plural = 'Terminal Commands'
        indexes = [
            models.Index(fields=['session', 'create_time']),
            models.Index(fields=['user', 'create_time']),
        ]

    def __str__(self):
        return f"{self.session.session_id} - {self.command[:50]}"
