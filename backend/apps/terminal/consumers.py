"""
WebSocket Consumer for Terminal - PTY based
"""
import asyncio
import fcntl
import json
import logging
import os
import pty
import signal
import struct
import termios

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TerminalSession, TerminalCommand
from .security import is_command_allowed

logger = logging.getLogger(__name__)


class TerminalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for terminal functionality using PTY.
    Provides a full interactive shell experience.
    """

    async def connect(self):
        self.user = self.scope['user']
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.session = None
        self.fd = None
        self.pid = None
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
        """Fork a child process with PTY using pty.fork()"""
        pid, fd = pty.fork()

        if pid == 0:
            # Child process - exec shell
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['LANG'] = 'en_US.UTF-8'
            shell = os.environ.get('SHELL', '/bin/zsh')
            os.execvpe(shell, [shell, '--login'], env)
        else:
            # Parent process
            self.fd = fd
            self.pid = pid

            # Set non-blocking
            flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Set default size
            self._set_pty_size(120, 30)

    def _set_pty_size(self, cols, rows):
        if self.fd is not None:
            try:
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            except OSError:
                pass

    async def _read_pty_output(self):
        """Read PTY output using asyncio event loop fd reader"""
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def _on_readable():
            if not future.done():
                future.set_result(True)

        try:
            while True:
                future = loop.create_future()
                loop.add_reader(self.fd, _on_readable)
                try:
                    await future
                finally:
                    loop.remove_reader(self.fd)

                try:
                    data = os.read(self.fd, 4096)
                    if not data:
                        break
                    text = data.decode('utf-8', errors='replace')
                    await self.send_json({'type': 'output', 'data': text})
                except OSError as e:
                    if e.errno == 5:  # EIO - child exited
                        break
                    if e.errno == 11:  # EAGAIN
                        continue
                    break
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"PTY read error: {e}")
        finally:
            exit_code = self._wait_child()
            try:
                await self.send_json({'type': 'exit', 'code': exit_code})
            except Exception:
                pass

    def _wait_child(self):
        """Non-blocking wait for child exit status (used by reader task finally)."""
        if self.pid is None:
            return -1
        try:
            wpid, status = os.waitpid(self.pid, os.WNOHANG)
            if wpid == 0:
                return -1  # Still running
            if os.WIFEXITED(status):
                return os.WEXITSTATUS(status)
            if os.WIFSIGNALED(status):
                return -os.WTERMSIG(status)
            return -1
        except ChildProcessError:
            return -1

    async def disconnect(self, close_code):
        # 1. Stop PTY output reader
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # 2. Close PTY fd — kernel sends SIGHUP to child process group
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None

        # 3. Ensure child process is terminated and reaped
        if self.pid is not None:
            await self._kill_and_reap(self.pid)
            self.pid = None

        # 4. Update session status
        if self.session:
            await self.update_session_status(self.session, '1')
            logger.info(f"PTY session closed: {self.user.username}")

    async def _kill_and_reap(self, pid: int):
        """Terminate child process with escalating signals and reap zombie."""
        for sig, wait_secs in [
            (signal.SIGHUP, 0.5),
            (signal.SIGTERM, 0.5),
            (signal.SIGKILL, 1.0),
        ]:
            # Check if already exited
            if self._try_reap(pid):
                return

            # Send signal
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                self._try_reap(pid)
                return

            # Poll for exit
            intervals = int(wait_secs / 0.05)
            for _ in range(intervals):
                await asyncio.sleep(0.05)
                if self._try_reap(pid):
                    return

        logger.warning(f"Child process {pid} could not be reaped after SIGKILL")

    @staticmethod
    def _try_reap(pid: int) -> bool:
        """Attempt to reap child. Returns True if child is gone."""
        try:
            wpid, _ = os.waitpid(pid, os.WNOHANG)
            return wpid != 0
        except ChildProcessError:
            return True  # Already reaped

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
        if self.fd is None:
            return

        # Track input for command auditing
        for ch in input_data:
            if ch in ('\r', '\n'):
                command = self._input_buffer.strip()
                if command:
                    is_allowed, reason = is_command_allowed(command)
                    if not is_allowed:
                        os.write(self.fd, b'\x15')  # Ctrl+U clears line
                        await self.send_json({
                            'type': 'output',
                            'data': f'\r\n\x1b[1;31m[BLOCKED] {reason}\x1b[0m\r\n'
                        })
                        os.write(self.fd, b'\n')
                        await self.save_command_history(command, "", blocked=True, reason=reason)
                        self._input_buffer = ''
                        return
                    await self.save_command_history(command, "")
                self._input_buffer = ''
            elif ch == '\x7f':
                self._input_buffer = self._input_buffer[:-1] if self._input_buffer else ''
            elif ch == '\x03':
                self._input_buffer = ''
            elif ch >= ' ':
                self._input_buffer += ch

        try:
            os.write(self.fd, input_data.encode('utf-8'))
        except OSError as e:
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
