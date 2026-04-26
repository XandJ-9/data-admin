import hashlib

from django.db import migrations


def _build_collection_task_code(data_source_id, database_name):
    raw = f'{data_source_id}|database|{database_name or ""}'
    readable = str(database_name or '').strip().lower().replace(' ', '_').replace('-', '_')[:48] or 'default'
    digest = hashlib.md5(raw.encode('utf-8')).hexdigest()[:8]
    return f'ds_collect_{data_source_id}_database_{readable}_{digest}'


def _build_collection_task_name(data_source_name, database_name):
    source_name = str(data_source_name or '数据源').strip() or '数据源'
    database_display = str(database_name or '').strip() or '默认库'
    return f'采集 {source_name} / {database_display}'


def backfill_legacy_database_runs(apps, schema_editor):
    LegacyRun = apps.get_model('datasource', 'DatabaseAssetSyncRun')
    DataSourceCollectionTask = apps.get_model('datasource', 'DataSourceCollectionTask')
    Task = apps.get_model('datatask', 'Task')
    TaskInstance = apps.get_model('datatask', 'TaskInstance')

    for legacy_run in LegacyRun.objects.select_related('data_source').order_by('create_time', 'id'):
        data_source = legacy_run.data_source
        data_source_name = data_source.name if data_source else ''
        collection_task = DataSourceCollectionTask.objects.filter(
            data_source_id=legacy_run.data_source_id,
            collection_scope='database',
            database_name=legacy_run.database_name,
            table_name='',
            del_flag='0',
        ).first()
        if collection_task is None:
            collection_task = DataSourceCollectionTask.objects.create(
                task_name=_build_collection_task_name(data_source_name, legacy_run.database_name),
                task_code=_build_collection_task_code(legacy_run.data_source_id or 0, legacy_run.database_name),
                data_source_id=legacy_run.data_source_id,
                collection_scope='database',
                database_name=legacy_run.database_name,
                table_name='',
                continue_on_error=True,
                status='active',
                schedule_type='manual',
                owner=legacy_run.update_by or legacy_run.create_by or '',
                task_config={},
                remark='由 DatabaseAssetSyncRun 自动迁移',
                create_by=legacy_run.create_by,
                update_by=legacy_run.update_by,
                del_flag='0',
            )
            DataSourceCollectionTask.objects.filter(pk=collection_task.pk).update(
                create_time=legacy_run.create_time,
                update_time=legacy_run.update_time,
            )

        task_config = {
            'dataSourceId': legacy_run.data_source_id,
            'dataSourceName': data_source_name,
            'collectionScope': 'database',
            'databaseName': legacy_run.database_name,
            'tableName': '',
            'continueOnError': True,
            'scheduleType': 'manual',
            'cronExpression': '',
            'taskConfig': {},
        }
        platform_task = Task.objects.filter(
            source_module='datasource.collection',
            source_record_id=collection_task.id,
        ).first()
        if platform_task is None:
            platform_task = Task.objects.create(
                task_name=collection_task.task_name,
                task_code=f'asset_collection_datasource_collection_{collection_task.id}',
                task_type='ASSET_COLLECTION',
                status='active',
                source_module='datasource.collection',
                source_record_id=collection_task.id,
                schedule_type='manual',
                cron_expression='',
                owner=collection_task.owner,
                task_config=task_config,
                remark=collection_task.remark,
                create_by=collection_task.create_by,
                update_by=collection_task.update_by,
                del_flag='0',
            )
            Task.objects.filter(pk=platform_task.pk).update(
                create_time=legacy_run.create_time,
                update_time=legacy_run.update_time,
            )

        result_summary = dict(legacy_run.result_summary or {})
        result_summary.setdefault('collectionScope', 'database')
        result_summary.setdefault('databaseName', legacy_run.database_name)
        result_summary.setdefault('tableName', '')
        result_summary.setdefault('totalTables', legacy_run.total_tables)
        result_summary.setdefault('successfulTables', legacy_run.successful_tables)
        result_summary.setdefault('failedTables', legacy_run.failed_tables)
        result_summary.setdefault('skippedTables', legacy_run.skipped_tables or result_summary.pop('skippedObjects', 0))
        result_summary.setdefault('currentTable', legacy_run.current_table or '')
        result_summary.setdefault('failedDetails', result_summary.get('failedDetails', []))
        runtime_config = {
            'collectionTaskId': collection_task.id,
            'dataSourceId': legacy_run.data_source_id,
            'dataSourceName': data_source_name,
            'collectionScope': 'database',
            'databaseName': legacy_run.database_name,
            'tableName': '',
            'heartbeatAt': (legacy_run.finished_at or legacy_run.started_at or legacy_run.create_time).isoformat(),
        }
        duration_seconds = None
        if legacy_run.started_at and legacy_run.finished_at:
            duration_seconds = round((legacy_run.finished_at - legacy_run.started_at).total_seconds(), 2)

        task_instance = TaskInstance.objects.filter(instance_id=legacy_run.run_id).first()
        if task_instance is None:
            task_instance = TaskInstance.objects.create(
                task=platform_task,
                instance_id=legacy_run.run_id,
                status='success' if legacy_run.status == 'completed' else legacy_run.status,
                trigger_mode='manual',
                scheduled_at=legacy_run.create_time,
                started_at=legacy_run.started_at,
                finished_at=legacy_run.finished_at,
                duration_seconds=duration_seconds,
                runtime_config=runtime_config,
                executor_type='asset_collection',
                result_summary=result_summary,
                error_message=legacy_run.error_message or '',
                triggered_by=legacy_run.create_by or legacy_run.update_by or '',
            )
            TaskInstance.objects.filter(pk=task_instance.pk).update(create_time=legacy_run.create_time)

        platform_task.last_instance_status = task_instance.status
        platform_task.last_instance_at = task_instance.finished_at or task_instance.started_at or task_instance.create_time
        platform_task.save(update_fields=['last_instance_status', 'last_instance_at', 'update_time'])


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0007_datasourcecollectiontask_delete_databaseassetsyncrun_and_more'),
        ('datatask', '0003_alter_task_task_type'),
    ]

    operations = [
        migrations.RunPython(backfill_legacy_database_runs, migrations.RunPython.noop),
    ]
