"""
WebSocket Consumer for Terminal - Cross-platform PTY using pywinpty
"""
import asyncio
import json
import logging
import os

try:
    import winpty as pywinpty
except ImportError:
    raise ImportError(
        "pywinpty is required. Install it with: uv pip install pywinpty\n"
    )

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TerminalSession, TerminalCommand
from .security import is_command_allowed

logger = logging.getLogger(__name__)


class TerminalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for terminal functionality using pywinpty.
    Provides a full interactive shell experience with cross-platform support.
    """

    async def connect(self):
        self.user = self.scope['user']
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.session = None
        self.process = None
        self._reader_task = None
        self._input_buffer = ''

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        if not await self.check_terminal_permission():
            await self.close(code=4003)
            return

        if self.session_id:
            self.session = await self.get_session(self.session_id)
            if not self.session:
                await self.close(code=4004)
                return
        else:
            self.session = await self.create_session()

        await self.accept()

        try:
            self._spawn_shell()
            self._reader_task = asyncio.ensure_future(self._read_pty_output())
        except Exception as e:
            logger.error(f"Failed to spawn shell: {e}")
            await self.send_json({'type': 'error', 'data': f'Failed to start shell: {e}'})
            await self.close()
            return

        logger.info(f"PTY session started: {self.user.username} (session: {self.session.session_id})")

    def _spawn_shell(self):
        """Spawn a shell process using pywinpty"""
        # Determine shell command based on platform
        if os.name == 'nt':  # Windows
            shell_cmd = ['cmd.exe']
        else:  # Unix/Linux/macOS
            shell = os.environ.get('SHELL', '/bin/bash')
            shell_cmd = [shell, '--login']

        try:
            # Create pseudo-terminal process
            self.process = pywinpty.PtyProcess.spawn(
                shell_cmd,
                dimensions=(30, 120),  # rows, cols
                env=os.environ.copy()
            )
            logger.info(f"Spawned shell: {shell_cmd} with pid={self.process.pid}")
        except Exception as e:
            logger.error(f"Failed to spawn shell process: {e}")
            raise

    def _set_pty_size(self, cols, rows):
        """Set the terminal window size"""
        if self.process is not None and self.process.isalive():
            try:
                self.process.setwinsize(rows, cols)
            except Exception as e:
                logger.warning(f"Failed to set window size: {e}")

    async def _read_pty_output(self):
        """Read PTY output using asyncio with timeout"""
        try:
            while True:
                # Check if process is still alive
                if not self.process.isalive():
                    exit_code = self.process.exitstatus
                    logger.info(f"Shell process exited with code: {exit_code}")
                    try:
                        await self.send_json({'type': 'exit', 'code': exit_code})
                    except Exception:
                        pass
                    break

                try:
                    # Try to read data with a small timeout
                    data = await asyncio.to_thread(self.process.read, timeout=50)
                    if data:
                        await self.send_json({'type': 'output', 'data': data})
                except Exception:
                    # No data available, continue
                    await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"PTY read error: {e}")
        finally:
            # Ensure exit message is sent
            try:
                if self.process and not self.process.isalive():
                    exit_code = self.process.exitstatus if self.process.exitstatus is not None else -1
                    await self.send_json({'type': 'exit', 'code': exit_code})
            except Exception:
                pass

    async def disconnect(self, close_code):
        # 1. Stop PTY output reader
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # 2. Terminate shell process
        if self.process is not None:
            await self._terminate_process()
            self.process = None

        # 3. Update session status
        if self.session:
            await self.update_session_status(self.session, '1')
            logger.info(f"PTY session closed: {self.user.username}")

    async def _terminate_process(self):
        """Terminate the shell process cleanly"""
        if self.process is None:
            return

        try:
            if self.process.isalive():
                # Try graceful termination first
                self.process.terminate()

                # Wait a bit for cleanup
                for _ in range(20):  # Up to 1 second
                    await asyncio.sleep(0.05)
                    if not self.process.isalive():
                        break

                # Force kill if still alive
                if self.process.isalive():
                    logger.warning("Process did not terminate gracefully, forcing kill")
                    self.process.kill()
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error terminating process: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
            return

        msg_type = data.get('type')

        if msg_type == 'input':
            await self._handle_input(data.get('data', ''))
        elif msg_type == 'command':
            await self._handle_input(data.get('data', '') + '\r')
        elif msg_type == 'resize':
            self._set_pty_size(data.get('cols', 120), data.get('rows', 30))
        elif msg_type == 'ping':
            await self.send_json({'type': 'pong'})
        else:
            await self.send_error(f"Unknown message type: {msg_type}")

    async def _handle_input(self, input_data: str):
        if self.process is None or not self.process.isalive():
            return

        # Track input for command auditing
        for ch in input_data:
            if ch in ('\r', '\n'):
                command = self._input_buffer.strip()
                if command:
                    is_allowed, reason = is_command_allowed(command)
                    if not is_allowed:
                        # Clear line visually
                        await self.send_json({
                            'type': 'output',
                            'data': '\r\n\x1b[1;31m[BLOCKED] {reason}\x1b[0m\r\n'
                        })
                        await self.save_command_history(command, "", blocked=True, reason=reason)
                        self._input_buffer = ''
                        return
                    await self.save_command_history(command, "")
                self._input_buffer = ''
            elif ch == '\x7f':  # Backspace
                self._input_buffer = self._input_buffer[:-1] if self._input_buffer else ''
            elif ch == '\x03':  # Ctrl+C
                self._input_buffer = ''
            elif ch >= ' ':
                self._input_buffer += ch

        try:
            self.process.write(input_data)
        except Exception as e:
            logger.error(f"PTY write error: {e}")

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))

    async def send_error(self, message: str):
        await self.send_json({'type': 'error', 'data': message})

    @database_sync_to_async
    def check_terminal_permission(self) -> bool:
        return self.user.is_superuser or self.user.is_staff

    @database_sync_to_async
    def create_session(self) -> TerminalSession:
        return TerminalSession.objects.create(
            user=self.user, status='0', host='localhost',
            create_by=self.user.username,
        )

    @database_sync_to_async
    def get_session(self, session_id: str) -> TerminalSession:
        try:
            return TerminalSession.objects.get(session_id=session_id, user=self.user)
        except TerminalSession.DoesNotExist:
            return None

    @database_sync_to_async
    def update_session_status(self, session: TerminalSession, status: str):
        session.status = status
        session.update_by = self.user.username
        session.save()

    @database_sync_to_async
    def save_command_history(self, command: str, output: str = "",
                             blocked: bool = False, reason: str = ""):
        if not self.session:
            return
        if blocked:
            output = f"[BLOCKED] {reason}"
        TerminalCommand.objects.create(
            session=self.session, user=self.user,
            command=command, output=output[:5000],
            create_by=self.user.username,
        )
