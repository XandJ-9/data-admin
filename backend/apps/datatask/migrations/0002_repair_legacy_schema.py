import json
import re

from django.db import migrations


TASK_CODE_PATTERN = re.compile(
    r'^(?P<task_type>data_sync|sql_compute)_(?P<source_module>dataintegration_task|datadev_script)_(?P<source_record_id>\d+)$'
)


def _table_columns(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
    return [column.name for column in description]


def _parse_task_config(raw_value):
    if not raw_value:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, ValueError):
        return {}


def _infer_source_binding(task_code):
    if not task_code:
        return '', None
    match = TASK_CODE_PATTERN.match(task_code)
    if not match:
        return '', None
    return (
        match.group('source_module').replace('_', '.'),
        int(match.group('source_record_id')),
    )


def repair_legacy_schema(apps, schema_editor):
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())
    Task = apps.get_model('datatask', 'Task')
    TaskDependency = apps.get_model('datatask', 'TaskDependency')
    TaskInstance = apps.get_model('datatask', 'TaskInstance')
    legacy_tables_to_drop = ['datatask_dependency', 'datatask_instance']

    for legacy_table in legacy_tables_to_drop:
        if legacy_table in existing_tables:
            schema_editor.execute(f'DROP TABLE {legacy_table}')
            existing_tables.remove(legacy_table)

    expected_task_columns = {
        'source_module',
        'source_record_id',
        'schedule_type',
        'last_instance_status',
        'last_instance_at',
    }

    if 'datatask_task' not in existing_tables:
        schema_editor.create_model(Task)
        existing_tables.add('datatask_task')
    else:
        current_columns = set(_table_columns(schema_editor, 'datatask_task'))
        if not expected_task_columns.issubset(current_columns):
            legacy_table_name = 'datatask_task_legacy_backup'
            if legacy_table_name in existing_tables:
                schema_editor.execute(f'DROP TABLE {legacy_table_name}')
                existing_tables.remove(legacy_table_name)

            schema_editor.execute(f'ALTER TABLE datatask_task RENAME TO {legacy_table_name}')
            existing_tables.remove('datatask_task')
            existing_tables.add(legacy_table_name)

            schema_editor.create_model(Task)
            existing_tables.add('datatask_task')

            with connection.cursor() as cursor:
                cursor.execute(
                    f'''
                    SELECT
                        id, create_by, update_by, create_time, update_time, del_flag,
                        task_name, task_code, task_type, description, status, owner,
                        cron_expression, task_config, remark
                    FROM {legacy_table_name}
                    ORDER BY id
                    '''
                )
                legacy_rows = cursor.fetchall()

            task_objects = []
            for row in legacy_rows:
                (
                    task_id,
                    create_by,
                    update_by,
                    create_time,
                    update_time,
                    del_flag,
                    task_name,
                    task_code,
                    task_type,
                    description,
                    status,
                    owner,
                    cron_expression,
                    task_config,
                    remark,
                ) = row
                source_module, source_record_id = _infer_source_binding(task_code)
                normalized_cron = (cron_expression or '')[:64]
                task_objects.append(
                    Task(
                        id=task_id,
                        create_by=create_by,
                        update_by=update_by,
                        create_time=create_time,
                        update_time=update_time,
                        del_flag=del_flag,
                        task_name=task_name,
                        task_code=task_code,
                        task_type=task_type,
                        status=status,
                        source_module=source_module,
                        source_record_id=source_record_id,
                        schedule_type='cron' if normalized_cron else 'manual',
                        cron_expression=normalized_cron,
                        owner=owner,
                        task_config=_parse_task_config(task_config),
                        last_instance_status='',
                        last_instance_at=None,
                        remark=remark or description or '',
                    )
                )

            if task_objects:
                Task.objects.bulk_create(task_objects)

            schema_editor.execute(f'DROP TABLE {legacy_table_name}')
            existing_tables.remove(legacy_table_name)

    if 'datatask_task_dependency' not in existing_tables:
        schema_editor.create_model(TaskDependency)
        existing_tables.add('datatask_task_dependency')

    if 'datatask_task_instance' not in existing_tables:
        schema_editor.create_model(TaskInstance)


class Migration(migrations.Migration):

    dependencies = [
        ('datatask', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(repair_legacy_schema, migrations.RunPython.noop),
    ]
