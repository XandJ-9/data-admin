from django.db import migrations, models


def cleanup_duplicate_active_tasks(apps, schema_editor):
    MetaCollectionTask = apps.get_model('dataasset', 'MetaCollectionTask')
    db_alias = schema_editor.connection.alias

    active_tasks = MetaCollectionTask.objects.using(db_alias).filter(
        status__in=['pending', 'running']
    ).order_by('data_source_id', '-update_time', '-id')

    survivor_ids = set()
    grouped_tasks = {}
    for task in active_tasks.iterator():
        grouped_tasks.setdefault(task.data_source_id, []).append(task)

    for tasks in grouped_tasks.values():
        winner = max(
            tasks,
            key=lambda item: (
                1 if item.status == 'running' else 0,
                item.started_at or item.update_time,
                item.update_time,
                item.id,
            ),
        )
        survivor_ids.add(winner.id)

    duplicate_tasks = []
    for task in active_tasks.iterator():
        if task.id in survivor_ids:
            continue
        task.status = 'failed'
        task.completed_at = task.completed_at or task.update_time
        task.error_message = task.error_message or '升级时清理重复活动采集任务'
        duplicate_tasks.append(task)

    if duplicate_tasks:
        MetaCollectionTask.objects.using(db_alias).bulk_update(
            duplicate_tasks,
            ['status', 'completed_at', 'error_message'],
            batch_size=500,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('dataasset', '0004_backfill_standard_asset_models'),
    ]

    operations = [
        migrations.RunPython(cleanup_duplicate_active_tasks, noop_reverse),
        migrations.AddConstraint(
            model_name='metacollectiontask',
            constraint=models.UniqueConstraint(
                fields=('data_source',),
                condition=models.Q(status__in=['pending', 'running']),
                name='dataasset_single_active_collection_task',
            ),
        ),
    ]
