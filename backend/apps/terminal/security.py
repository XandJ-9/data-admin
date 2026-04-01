"""
Terminal Security Module - Command Validation & Blacklist
Cross-platform: covers Unix/macOS and Windows dangerous commands.
"""
import re

# ── Forbidden commands (Unix / macOS / Linux) ─────────────────────
_FORBIDDEN_UNIX = {
    # Destructive file operations
    'rm', 'dd', 'shred', 'wipe', 'truncate',

    # Filesystem creation / modification
    'mkfs', 'mkfs.ext4', 'mkfs.ntfs', 'mkfs.fat',
    'fdisk', 'parted', 'gdisk', 'fsck', 'fsck.ext4',

    # System state
    'shutdown', 'reboot', 'halt', 'poweroff', 'init', 'systemctl',
    'service', 'chkconfig', 'insserv', 'launchctl',

    # Process termination
    'kill', 'killall', 'pkill',

    # Boot / Recovery
    'grub-install', 'grub2-install',

    # Network - potentially dangerous
    'iptables', 'ip6tables', 'nftables', 'firewall-cmd', 'ufw', 'pfctl',
    'route', 'ip',

    # User / Group management
    'useradd', 'userdel', 'usermod', 'groupadd', 'groupdel', 'groupmod',
    'passwd', 'chpasswd', 'sudoedit', 'visudo', 'dscl',

    # Package management (removal)
    'apt-get', 'apt', 'yum', 'dnf', 'rpm', 'dpkg', 'pacman', 'brew',

    # Kernel
    'insmod', 'rmmod', 'modprobe', 'depmod',

    # Cron / scheduling
    'crontab', 'at', 'atq', 'atrm',

    # Chroot / container escape
    'chroot', 'nsenter', 'unshare',
}

# ── Forbidden commands (Windows) ──────────────────────────────────
_FORBIDDEN_WINDOWS = {
    'format', 'diskpart', 'bcdedit', 'bootrec',
    'shutdown', 'taskkill', 'schtasks', 'sc',
    'reg', 'regedit', 'wmic',
    'net', 'netsh',
    'cipher', 'takeown', 'icacls',
    'del', 'rmdir', 'rd',
}

FORBIDDEN_COMMANDS = _FORBIDDEN_UNIX | _FORBIDDEN_WINDOWS

# Patterns that indicate dangerous shell tricks
_DANGEROUS_PATTERNS = [
    re.compile(r'>\s*/dev/sd[a-z]', re.IGNORECASE),            # write to raw disk
    re.compile(r':\(\)\{\s*:\|:\s*&\s*\};:', re.IGNORECASE),   # fork bomb
    re.compile(r'\bsudo\b', re.IGNORECASE),                     # privilege escalation
    re.compile(r'\bsu\s+-?\s*$', re.IGNORECASE),                # switch user
    re.compile(r'\bchmod\s+[0-7]*777\b', re.IGNORECASE),       # world-writable
    re.compile(r'\bcurl\b.*\|\s*(ba)?sh', re.IGNORECASE),      # pipe to shell
    re.compile(r'\bwget\b.*\|\s*(ba)?sh', re.IGNORECASE),
    re.compile(r'\bmkfifo\b', re.IGNORECASE),                   # named pipe (reverse shell)
    re.compile(r'/dev/tcp/', re.IGNORECASE),                    # bash tcp redirect
    re.compile(r'\bnc\b.*-[elp]', re.IGNORECASE),              # netcat listen
    re.compile(r'\bncat\b.*-[elp]', re.IGNORECASE),
    re.compile(r'\bpython[23]?\s+-c\b', re.IGNORECASE),        # inline code execution
    re.compile(r'\bperl\s+-e\b', re.IGNORECASE),
    re.compile(r'\bruby\s+-e\b', re.IGNORECASE),
]

# Paths that should not be modified
FORBIDDEN_PATHS = [
    '/etc', '/sys', '/proc', '/boot', '/root',
    '/lib', '/bin', '/sbin', '/usr/bin', '/usr/sbin',
    'C:\\Windows', 'C:\\System32', 'C:\\Program Files',
]

# Read-only commands that are always safe on sensitive paths
_READ_ONLY_CMDS = {'cat', 'ls', 'lsof', 'grep', 'file', 'head', 'tail', 'less', 'more', 'wc', 'stat', 'find', 'which', 'type', 'dir'}


def _extract_base_cmd(part: str) -> str:
    """Extract the base command name from a pipeline segment."""
    part = part.strip()
    # Skip env var assignments like FOO=bar cmd
    while '=' in part.split()[0] if part.split() else False:
        part = part.split(maxsplit=1)[1] if ' ' in part else ''
    return part.split()[0].lower() if part.split() else ''


def is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed to execute.

    Returns:
        tuple: (is_allowed, reason_if_denied)
    """
    if not command or not isinstance(command, str):
        return False, "Invalid command"

    command_stripped = command.strip()
    command_lower = command_stripped.lower()

    # Check dangerous patterns
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command_stripped):
            return False, f"Dangerous pattern detected: {pattern.pattern}"

    # Split by shell separators and check each segment
    segments = re.split(r'\s*(?:\|{1,2}|&&|;)\s*', command_stripped)

    for segment in segments:
        base_cmd = _extract_base_cmd(segment)
        if not base_cmd:
            continue

        if base_cmd in FORBIDDEN_COMMANDS:
            return False, f"Command '{base_cmd}' is not allowed for security reasons"

    # Check against critical paths (only block modification)
    for path in FORBIDDEN_PATHS:
        if path.lower() in command_lower:
            if not any(cmd in command_lower for cmd in _READ_ONLY_CMDS):
                return False, f"Operations on critical path '{path}' are not allowed"

    return True, ""


def sanitize_command(command: str) -> str:
    """Basic command sanitization."""
    return command.strip()
