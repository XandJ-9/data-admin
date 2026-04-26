from django.db import migrations


SCRIPT_STATUS_TO_TASK_STATUS = {
    'draft': 'draft',
    'published': 'active',
    'archived': 'archived',
}


def build_task_code(task_type: str, source_module: str, source_record_id: int) -> str:
    normalized_module = source_module.replace('.', '_').replace('-', '_')
    return f'{task_type.lower()}_{normalized_module}_{source_record_id}'


def backfill_script_execution_to_taskinstance(apps, schema_editor):
    Script = apps.get_model('datadev', 'DataDevScript')
    ScriptVersion = apps.get_model('datadev', 'DataDevScriptVersion')
    ScriptExecution = apps.get_model('datadev', 'DataDevScriptExecution')
    Task = apps.get_model('datatask', 'Task')
    TaskInstance = apps.get_model('datatask', 'TaskInstance')

    source_module = 'datadev.script'

    for execution in ScriptExecution.objects.select_related('script', 'version', 'task_instance').order_by('create_time', 'id'):
        if execution.task_instance_id:
            task_instance = TaskInstance.objects.filter(pk=execution.task_instance_id).first()
            if task_instance is None:
                continue
            task = Task.objects.filter(pk=task_instance.task_id).first()
            merged_runtime_config = dict(task_instance.runtime_config or {})
            merged_runtime_config.setdefault('scriptVersionId', execution.version_id)
            merged_runtime_config.setdefault('params', execution.executor_params or {})
            merged_result_summary = dict(task_instance.result_summary or {})
            for key, value in (execution.result_summary or {}).items():
                merged_result_summary.setdefault(key, value)
            update_fields = []
            if merged_runtime_config != (task_instance.runtime_config or {}):
                task_instance.runtime_config = merged_runtime_config
                update_fields.append('runtime_config')
            if merged_result_summary != (task_instance.result_summary or {}):
                task_instance.result_summary = merged_result_summary
                update_fields.append('result_summary')
            if not task_instance.error_message and execution.error_message:
                task_instance.error_message = execution.error_message
                update_fields.append('error_message')
            if not task_instance.executor_type and execution.executor_type:
                task_instance.executor_type = execution.executor_type
                update_fields.append('executor_type')
            if task_instance.started_at != execution.start_time:
                task_instance.started_at = execution.start_time
                update_fields.append('started_at')
            if task_instance.finished_at != execution.end_time:
                task_instance.finished_at = execution.end_time
                update_fields.append('finished_at')
            if task_instance.duration_seconds != execution.duration_seconds:
                task_instance.duration_seconds = execution.duration_seconds
                update_fields.append('duration_seconds')
            if update_fields:
                task_instance.save(update_fields=update_fields)
            if task_instance.create_time != execution.create_time:
                TaskInstance.objects.filter(pk=task_instance.pk).update(create_time=execution.create_time)
            candidate_last_instance_at = execution.end_time or execution.start_time or execution.create_time
            if task is not None and (
                not getattr(task, 'last_instance_at', None)
                or (candidate_last_instance_at and candidate_last_instance_at >= task.last_instance_at)
            ):
                Task.objects.filter(pk=task.pk).update(
                    last_instance_status=execution.status,
                    last_instance_at=candidate_last_instance_at,
                )
            continue

        script = Script.objects.filter(pk=execution.script_id).first()
        if script is None:
            continue

        task_del_flag = '0' if getattr(script, 'del_flag', '0') == '0' else '1'
        current_version = ScriptVersion.objects.filter(script_id=script.id, is_current=True).first()
        task_status = SCRIPT_STATUS_TO_TASK_STATUS.get(getattr(script, 'status', ''), 'draft')
        task = Task.objects.filter(
            source_module=source_module,
            source_record_id=script.id,
        ).first()
        if task is None:
            task = Task.objects.create(
                source_module=source_module,
                source_record_id=script.id,
                del_flag=task_del_flag,
                task_name=script.script_name,
                task_code=build_task_code('SQL_COMPUTE', source_module, script.id),
                task_type='SQL_COMPUTE',
                status=task_status,
                schedule_type='manual',
                cron_expression='',
                owner=script.owner or execution.executed_by or '',
                task_config={
                    'scriptId': script.id,
                    'scriptCode': script.script_code,
                    'scriptType': script.script_type,
                    'scriptRole': getattr(script, 'script_role', ''),
                    'engineType': getattr(script, 'engine_type', ''),
                    'targetModelId': getattr(script, 'target_model_id', None),
                    'currentVersionId': current_version.id if current_version else None,
                    'sqlText': current_version.content if current_version else '',
                    '_platformSourceScheduleType': 'manual',
                    '_platformSourceCronExpression': '',
                },
                remark=script.remark or '',
                create_by=execution.executed_by or '',
                update_by=execution.executed_by or '',
            )

        if TaskInstance.objects.filter(instance_id=execution.execution_id).exists():
            continue

        runtime_config = {
            'scriptVersionId': execution.version_id,
            'params': execution.executor_params or {},
        }
        task_instance = TaskInstance.objects.create(
            task=task,
            instance_id=execution.execution_id,
            status=execution.status,
            trigger_mode='manual',
            scheduled_at=execution.start_time or execution.create_time,
            started_at=execution.start_time,
            finished_at=execution.end_time,
            duration_seconds=execution.duration_seconds,
            runtime_config=runtime_config,
            executor_type=execution.executor_type or '',
            result_summary=execution.result_summary or {},
            error_message=execution.error_message or '',
            triggered_by=execution.executed_by or '',
        )
        TaskInstance.objects.filter(pk=task_instance.pk).update(create_time=execution.create_time)
        candidate_last_instance_at = execution.end_time or execution.start_time or execution.create_time
        if (
            not getattr(task, 'last_instance_at', None)
            or (candidate_last_instance_at and candidate_last_instance_at >= task.last_instance_at)
        ):
            Task.objects.filter(pk=task.pk).update(
                last_instance_status=execution.status,
                last_instance_at=candidate_last_instance_at,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('datadev', '0010_alter_datadevscript_options_and_more'),
        ('datatask', '0003_alter_task_task_type'),
    ]

    operations = [
        migrations.RunPython(backfill_script_execution_to_taskinstance, migrations.RunPython.noop),
    ]
