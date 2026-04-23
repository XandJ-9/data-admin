def sanitize_db_error_message(exc):
    error_message = str(exc or '').lower()
    if any(
        keyword in error_message
        for keyword in ('access denied', 'authentication failed', 'password authentication failed', 'login failed', 'invalid credentials')
    ):
        return '连接失败：认证失败，请检查用户名和密码'
    if any(
        keyword in error_message
        for keyword in (
            'connection refused',
            'could not connect',
            'timeout',
            'timed out',
            'network is unreachable',
            'name or service not known',
            'temporary failure in name resolution',
        )
    ):
        return '连接失败：无法连接到数据库，请检查主机、端口和网络'
    if any(keyword in error_message for keyword in ('unknown database', 'does not exist', 'unknown schema', 'catalog', 'schema')):
        return '连接失败：数据库配置无效，请检查库名或 schema'
    return '连接失败：请检查连接配置'


def public_error_message(exc):
    raw_message = str(exc or '').strip()
    safe_prefixes = (
        '源端不存在数据表',
        '当前数据源已有进行中的采集任务',
        '不支持的数据库类型',
    )
    if any(raw_message.startswith(prefix) for prefix in safe_prefixes):
        return raw_message
    return sanitize_db_error_message(exc)

