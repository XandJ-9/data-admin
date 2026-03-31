"""
Terminal Security Module - Command Validation & Blacklist
"""

# Commands that are forbidden for security reasons
FORBIDDEN_COMMANDS = {
    # File system destructive commands
    'rm', 'dd', 'shred', 'wipe',

    # Filesystem creation/modification commands
    'mkfs', 'mkfs.ext4', 'mkfs.ntfs', 'mkfs.fat',
    'fdisk', 'parted', 'gdisk', 'fsck', 'fsck.ext4',
    'format', 'diskpart',

    # System state modification
    'shutdown', 'reboot', 'halt', 'poweroff', 'init', 'systemctl',
    'service', 'chkconfig', 'insserv',

    # Process termination
    'kill', 'killall', 'pkill', 'pkill9',

    # Filesystem sync
    'sync', 'fsync',

    # Boot/Recovery
    'grub-install', 'grub2-install', 'bootloader',

    # Network - potentially dangerous
    'iptables', 'firewall-cmd', 'ufw',
    'route', 'ip route', 'ip link',

    # User/Group management
    'useradd', 'userdel', 'usermod', 'groupadd', 'groupdel', 'groupmod',
    'passwd', 'shadow', 'sudoedit',

    # Package management (could break system)
    'apt-get remove', 'apt remove', 'yum remove', 'dnf remove',
    'rpm -e', 'dpkg -r', 'pacman -R',

    # Kernel/Module
    'insmod', 'rmmod', 'modprobe', 'depmod',

    # Dangerous tar/compression (could extract to wrong location)
    'tar -xf /', 'unzip /',
}

# Patterns that indicate operations on critical directories
FORBIDDEN_PATHS = [
    '/etc', '/sys', '/proc', '/boot', '/root',
    '/lib', '/bin', '/sbin', '/usr/bin', '/usr/sbin',
    'C:\\Windows', 'C:\\System32', 'C:\\Program Files',
]


def is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed to execute.

    Args:
        command: The shell command to validate

    Returns:
        tuple: (is_allowed, reason_if_denied)
    """
    if not command or not isinstance(command, str):
        return False, "Invalid command"

    command_lower = command.lower().strip()

    # Check against forbidden commands
    for forbidden in FORBIDDEN_COMMANDS:
        # Match the command at the start (word boundary)
        if command_lower.startswith(forbidden + ' ') or command_lower == forbidden:
            return False, f"Command '{forbidden}' is not allowed for security reasons"

        # Check if it's a pipe/redirect to a forbidden command
        for sep in ['|', '&&', '||', ';']:
            if sep in command:
                parts = command.split(sep)
                for part in parts:
                    part_lower = part.strip().lower()
                    if part_lower.startswith(forbidden + ' ') or part_lower == forbidden:
                        return False, f"Command '{forbidden}' in pipe/sequence is not allowed"

    # Check against critical paths
    for path in FORBIDDEN_PATHS:
        if f' {path}' in command.lower() or f'/{path}' in command.lower():
            # Allow reading/viewing (cat, ls, grep)
            if any(cmd in command.lower() for cmd in ['cat', 'ls', 'lsof', 'grep', 'file', 'head', 'tail', 'less', 'more']):
                continue
            # Disallow modifications
            if any(cmd in command.lower() for cmd in ['rm', 'mv', 'cp', 'mkdir', 'touch', 'chmod', 'chown', 'sed', 'awk']):
                return False, f"Modifications to critical path '{path}' are not allowed"

    return True, ""


def sanitize_command(command: str) -> str:
    """
    Basic command sanitization (remove special shell characters if needed).
    Currently just returns the command as-is after validation.

    Args:
        command: Raw command string

    Returns:
        Sanitized command string
    """
    return command.strip()
