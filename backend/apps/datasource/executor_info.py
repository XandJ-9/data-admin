import json

from apps.common.encrypt import decrypt_password

from .models import DataSource


def parse_connection_params(raw_params):
    if not raw_params:
        return {}
    if isinstance(raw_params, dict):
        return raw_params
    try:
        return json.loads(raw_params)
    except (TypeError, json.JSONDecodeError):
        return {}


def _resolve_database_name(data_source, params, database_name=''):
    override_name = str(database_name or '').strip()
    if data_source.db_type == 'sqlite':
        return data_source.db_name
    if not override_name:
        return data_source.db_name
    if data_source.db_type in ('presto', 'trino') and '.' not in override_name:
        base_database = str(data_source.db_name or '')
        if '.' in base_database:
            catalog = base_database.split('.', 1)[0]
            return f'{catalog}.{override_name}'
        catalog = str(params.get('catalog') or '').strip()
        if catalog:
            return f'{catalog}.{override_name}'
    return override_name


def build_executor_info(data_source: DataSource, database_name=''):
    params = parse_connection_params(data_source.params)
    return {
        'type': data_source.db_type,
        'host': data_source.host,
        'port': int(data_source.port or 0),
        'username': data_source.username,
        'password': decrypt_password(data_source.password),
        'database': _resolve_database_name(data_source, params, database_name),
        'params': params,
    }


def build_executor_info_from_payload(validated_data, password='', database_name=''):
    params = parse_connection_params(validated_data.get('params'))
    db_type = validated_data.get('db_type', '')
    raw_database = str(validated_data.get('db_name', '')).strip()
    override_name = str(database_name or '').strip()
    if db_type == 'sqlite':
        resolved_database = raw_database
    elif db_type in ('presto', 'trino') and override_name and '.' not in override_name and '.' in raw_database:
        catalog = raw_database.split('.', 1)[0]
        resolved_database = f'{catalog}.{override_name}'
    else:
        resolved_database = override_name or raw_database
    return {
        'type': db_type,
        'host': validated_data.get('host', ''),
        'port': int(validated_data.get('port') or 0),
        'username': validated_data.get('username', ''),
        'password': password or validated_data.get('password', ''),
        'database': resolved_database,
        'params': params,
    }

