"""
WebSocket Consumer for Terminal
"""
import asyncio
import subprocess
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TerminalSession, TerminalCommand
from .security import is_command_allowed
from apps.system.models import User

logger = logging.getLogger(__name__)


class TerminalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for terminal functionality.
    Handles command execution and output streaming.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.session = None
        self.process = None
        self.reader = None
        self.writer = None

        # Check permissions
        if not self.user.is_authenticated:
            await self.close(code=4001)
            logger.warning(f"Unauthenticated connection attempt from {self.scope['client']}")
            return

        # Check if user is admin (terminal access control)
        if not await self.check_terminal_permission():
            await self.close(code=4003)
            logger.warning(f"Unauthorized terminal access attempt by {self.user.username}")
            return

        # Get or create session
        if self.session_id:
            self.session = await self.get_session(self.session_id)
            if not self.session:
                await self.close(code=4004)
                return
        else:
            self.session = await self.create_session()

        await self.accept()
        logger.info(f"WebSocket connection established: {self.user.username} (session: {self.session.session_id})")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                self.process.kill()

        if self.session:
            await self.update_session_status(self.session, '1')  # disconnected
            logger.info(f"WebSocket disconnected: {self.user.username} (session: {self.session.session_id})")

    async def receive(self, text_data):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
            return

        command_type = data.get('type')

        if command_type == 'command':
            await self.handle_command(data.get('data', ''))
        elif command_type == 'resize':
            await self.handle_resize(data.get('cols'), data.get('rows'))
        elif command_type == 'ping':
            await self.send_json({'type': 'pong'})
        else:
            await self.send_error(f"Unknown message type: {command_type}")

    async def handle_command(self, command: str):
        """Execute shell command and send output"""
        if not command.strip():
            return

        # Validate command
        is_allowed, reason = is_command_allowed(command)
        if not is_allowed:
            await self.send_error(f"Command denied: {reason}")
            await self.save_command_history(command, "", exit_code=None, blocked=True, reason=reason)
            return

        try:
            import time
            start_time = time.time()

            # Execute command
            if True:  # Windows/Unix compatible approach
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    shell=True,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    'sh', '-c', command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )

            # Read output in chunks
            output_buffer = []
            try:
                while True:
                    line = await asyncio.wait_for(process.stdout.read(1024), timeout=30.0)
                    if not line:
                        break

                    try:
                        text = line.decode('utf-8', errors='replace')
                        output_buffer.append(text)
                        await self.send_json({'type': 'output', 'data': text})
                    except Exception as e:
                        logger.error(f"Error decoding output: {e}")

            except asyncio.TimeoutError:
                process.terminate()
                await self.send_error("Command execution timeout (30s)")

            # Wait for process to complete
            return_code = await process.wait()
            execution_time = time.time() - start_time

            # Send completion signal
            await self.send_json({'type': 'exit', 'code': return_code})

            # Save command history
            output_text = ''.join(output_buffer)
            await self.save_command_history(
                command,
                output_text,
                exit_code=return_code,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            await self.send_error(f"Execution error: {str(e)}")

    async def handle_resize(self, cols: int, rows: int):
        """Handle terminal resize (not implemented yet)"""
        # This would be used if we implement proper PTY support
        pass

    async def send_json(self, content):
        """Send JSON data to client"""
        await self.send(text_data=json.dumps(content))

    async def send_error(self, message: str):
        """Send error message to client"""
        await self.send_json({'type': 'error', 'data': message})

    # Database operations
    @database_sync_to_async
    def check_terminal_permission(self) -> bool:
        """Check if user has permission to access terminal"""
        # For now, only allow admin users
        return self.user.is_superuser or self.user.is_staff

    @database_sync_to_async
    def create_session(self) -> TerminalSession:
        """Create a new terminal session"""
        session = TerminalSession.objects.create(
            user=self.user,
            status='0',  # connected
            host='localhost',
            create_by=self.user.username,
        )
        return session

    @database_sync_to_async
    def get_session(self, session_id: str) -> TerminalSession:
        """Retrieve an existing session"""
        try:
            session = TerminalSession.objects.get(session_id=session_id, user=self.user)
            return session
        except TerminalSession.DoesNotExist:
            return None

    @database_sync_to_async
    def update_session_status(self, session: TerminalSession, status: str):
        """Update session status"""
        session.status = status
        session.update_by = self.user.username
        session.save()

    @database_sync_to_async
    def save_command_history(
        self,
        command: str,
        output: str = "",
        exit_code: int = None,
        execution_time: float = None,
        blocked: bool = False,
        reason: str = ""
    ):
        """Save command execution history"""
        if not self.session:
            return

        # Prefix output with block reason if command was blocked
        if blocked:
            output = f"[BLOCKED] {reason}\n{output}"

        TerminalCommand.objects.create(
            session=self.session,
            user=self.user,
            command=command,
            output=output[:5000],  # Limit output to 5000 chars for storage
            exit_code=exit_code,
            execution_time=execution_time,
            create_by=self.user.username,
        )
