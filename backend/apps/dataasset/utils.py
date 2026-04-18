def sanitize_collection_error_message(exc):
    error_message = str(exc or '').lower()
    if any(keyword in error_message for keyword in (
        'access denied',
        'authentication failed',
        'password authentication failed',
        'login failed',
        'invalid credentials',
    )):
        return '采集失败：认证失败，请检查数据源账号配置'
    if any(keyword in error_message for keyword in (
        'connection refused',
        'could not connect',
        'timeout',
        'timed out',
        'network is unreachable',
        'name or service not known',
        'temporary failure in name resolution',
    )):
        return '采集失败：无法连接到数据源，请检查网络、主机和端口'
    if any(keyword in error_message for keyword in (
        'unknown database',
        'does not exist',
        'unknown schema',
        'catalog',
        'schema',
    )):
        return '采集失败：数据源库或 schema 配置无效'
    return '采集失败，请检查数据源配置或稍后重试'
