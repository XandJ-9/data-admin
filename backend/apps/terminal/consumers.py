"""
WebSocket Consumer for Terminal - Cross-platform PTY process support.
Supports Windows (pywinpty), macOS, and Linux (ptyprocess).
"""
import asyncio
import json
import logging
import os
import signal
import time

if os.name == 'nt':
    try:
        import winpty as pty_backend
    except ImportError as exc:
        raise ImportError(
            "pywinpty is required on Windows. Install it with: uv pip install pywinpty\n"
        ) from exc
else:
    try:
        import ptyprocess as pty_backend
    except ImportError as exc:
        raise ImportError(
            "ptyprocess is required on macOS/Linux. Install it with: uv pip install ptyprocess\n"
        ) from exc

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TerminalSession, TerminalCommand
from .security import is_command_allowed

logger = logging.getLogger(__name__)

# Configurable limits
HEARTBEAT_INTERVAL = 30        # seconds between pings
HEARTBEAT_TIMEOUT = 90         # close if no pong/input for this many seconds
SESSION_MAX_IDLE = 1800        # auto-close after 30 min idle (no input)

# Safe environment keys to pass through to the PTY process
_SAFE_ENV_KEYS = {
    'PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'LC_ALL', 'LC_CTYPE',
    'TERM', 'COLORTERM', 'EDITOR', 'VISUAL', 'TMPDIR', 'TZ',
    'HOSTNAME', 'LOGNAME', 'MAIL', 'PWD',
    # Windows
    'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP',
    'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMFILES',
    'PROGRAMFILES(X86)', 'COMMONPROGRAMFILES', 'HOMEDRIVE', 'HOMEPATH',
}


def _build_safe_env() -> dict:
    """Build a sanitised environment dict for the PTY child process."""
    env = {k: v for k, v in os.environ.items() if k in _SAFE_ENV_KEYS}
    env.setdefault('TERM', 'xterm-256color')
    env.setdefault('COLORTERM', 'truecolor')
    if os.name != 'nt':
        env.setdefault('LANG', 'en_US.UTF-8')
    return env


class TerminalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for terminal functionality using platform PTY backend.
    Provides a full interactive shell experience with cross-platform support.
    """

    async def connect(self):
        self.user = self.scope['user']
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.session = None
        self.process = None
        self._reader_task = None
        self._heartbeat_task = None
        self._input_buffer = ''
        self._last_activity = time.monotonic()

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
            self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop())
        except Exception as e:
            logger.error(f"Failed to spawn shell: {e}")
            await self.send_json({'type': 'error', 'data': f'Failed to start shell: {e}'})
            await self.close()
            return

        logger.info(f"PTY session started: {self.user.username} (session: {self.session.session_id})")

    # ── Shell Management ──────────────────────────────────────────────

    def _spawn_shell(self):
        """Spawn a shell process using platform PTY backend."""
        if os.name == 'nt':
            shell_cmd = ['cmd.exe']
        else:
            shell = os.environ.get('SHELL', '/bin/bash')
            shell_cmd = [shell, '--login']

        try:
            self.process = pty_backend.PtyProcess.spawn(
                shell_cmd,
                dimensions=(30, 120),
                env=_build_safe_env(),
            )
            logger.info(f"Spawned shell: {shell_cmd} with pid={self.process.pid}")
        except Exception as e:
            logger.error(f"Failed to spawn shell process: {e}")
            raise

    def _set_pty_size(self, cols, rows):
        """Set the terminal window size."""
        if self.process is not None and self.process.isalive():
            try:
                self.process.setwinsize(rows, cols)
            except Exception as e:
                logger.warning(f"Failed to set window size: {e}")

    # ── PTY I/O ───────────────────────────────────────────────────────

    async def _read_pty_output(self):
        """Continuously read PTY output and forward to WebSocket client."""
        try:
            if os.name == 'nt':
                await self._read_pty_loop_windows()
            else:
                await self._read_pty_loop_unix()
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"PTY read error: {e}")
        finally:
            try:
                if self.process and not self.process.isalive():
                    exit_code = self.process.exitstatus if self.process.exitstatus is not None else -1
                    await self.send_json({'type': 'exit', 'code': exit_code})
            except Exception:
                pass

    async def _read_pty_loop_unix(self):
        """Read PTY via asyncio fd monitoring — no threads, no data race."""
        fd = self.process.fd
        loop = asyncio.get_running_loop()

        while True:
            future = loop.create_future()
            loop.add_reader(fd, lambda f=future: f.done() or f.set_result(None))
            try:
                await future
            finally:
                loop.remove_reader(fd)

            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break

            text = data.decode('utf-8', errors='replace')
            await self.send_json({'type': 'output', 'data': text})

        if self.process and not self.process.isalive():
            logger.info(f"Shell process exited with code: {self.process.exitstatus}")

    async def _read_pty_loop_windows(self):
        """Read PTY via thread — pywinpty blocks in read(), offloaded to thread."""
        while True:
            if not self.process.isalive():
                # Drain remaining output
                try:
                    remaining = self.process.read(4096)
                    if remaining:
                        await self.send_json({'type': 'output', 'data': remaining})
                except Exception:
                    pass
                logger.info(f"Shell process exited with code: {self.process.exitstatus}")
                break
            try:
                data = await asyncio.to_thread(self.process.read, 4096)
                if data:
                    await self.send_json({'type': 'output', 'data': data})
            except EOFError:
                break
            except Exception as e:
                logger.debug(f"PTY read exception: {e}")
                await asyncio.sleep(0.05)

    # ── Heartbeat & Idle Timeout ──────────────────────────────────────

    async def _heartbeat_loop(self):
        """Server-side heartbeat: send ping and auto-close on idle timeout."""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                idle = time.monotonic() - self._last_activity
                if idle > SESSION_MAX_IDLE:
                    logger.info(f"Session idle timeout ({idle:.0f}s), closing")
                    await self.send_json({
                        'type': 'output',
                        'data': '\r\n\x1b[33m[Session timed out due to inactivity]\x1b[0m\r\n',
                    })
                    await self.close()
                    return
                if idle > HEARTBEAT_TIMEOUT:
                    logger.info(f"Heartbeat timeout ({idle:.0f}s), closing")
                    await self.close()
                    return
                await self.send_json({'type': 'ping'})
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    # ── Connection Lifecycle ──────────────────────────────────────────

    async def disconnect(self, close_code):
        for task in (self._reader_task, self._heartbeat_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        if self.process is not None:
            await self._terminate_process()
            self.process = None

        if self.session:
            await self.update_session_status(self.session, '1')
            logger.info(f"PTY session closed: {self.user.username}")

    async def _terminate_process(self):
        """Terminate the shell process cleanly."""
        if self.process is None:
            return
        try:
            if self.process.isalive():
                self.process.terminate()
                for _ in range(20):
                    await asyncio.sleep(0.05)
                    if not self.process.isalive():
                        break
                if self.process.isalive():
                    logger.warning("Process did not terminate gracefully, forcing kill")
                    self._force_kill_process()
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error terminating process: {e}")

    def _force_kill_process(self):
        """Force kill process with best-effort cross-platform signal handling."""
        if os.name == 'nt':
            self.process.kill()
            return
        kill_signal = getattr(signal, 'SIGKILL', None)
        if kill_signal is not None:
            self.process.kill(kill_signal)
        else:
            self.process.terminate()

    # ── Message Handling ──────────────────────────────────────────────

    async def receive(self, text_data):
        self._last_activity = time.monotonic()

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
            cols = min(max(int(data.get('cols', 120)), 10), 500)
            rows = min(max(int(data.get('rows', 30)), 2), 200)
            self._set_pty_size(cols, rows)
        elif msg_type in ('ping', 'pong'):
            if msg_type == 'ping':
                await self.send_json({'type': 'pong'})
        else:
            await self.send_error(f"Unknown message type: {msg_type}")

    async def _handle_input(self, input_data: str):
        if self.process is None or not self.process.isalive():
            return

        for ch in input_data:
            if ch in ('\r', '\n'):
                command = self._input_buffer.strip()
                if command:
                    is_allowed, reason = is_command_allowed(command)
                    if not is_allowed:
                        await self.send_json({
                            'type': 'output',
                            'data': f'\r\n\x1b[1;31m[BLOCKED] {reason}\x1b[0m\r\n',
                        })
                        await self.save_command_history(command, blocked=True, reason=reason)
                        self._input_buffer = ''
                        return
                    await self.save_command_history(command)
                self._input_buffer = ''
            elif ch == '\x7f':
                self._input_buffer = self._input_buffer[:-1] if self._input_buffer else ''
            elif ch == '\x03':
                self._input_buffer = ''
            elif ch >= ' ':
                self._input_buffer += ch

        try:
            if os.name != 'nt' and isinstance(input_data, str):
                input_data = input_data.encode('utf-8')
            self.process.write(input_data)
        except Exception as e:
            logger.error(f"PTY write error: {e}")

    # ── Helpers ───────────────────────────────────────────────────────

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
    def save_command_history(self, command: str,
                             blocked: bool = False, reason: str = ""):
        if not self.session:
            return
        output = f"[BLOCKED] {reason}" if blocked else ""
        TerminalCommand.objects.create(
            session=self.session, user=self.user,
            command=command, output=output,
            create_by=self.user.username,
        )
