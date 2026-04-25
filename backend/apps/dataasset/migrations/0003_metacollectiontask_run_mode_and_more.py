import django.db.models.deletion
from django.db import migrations, models


def _normalize_part(value):
    return str(value or '').strip()


def _build_namespace_key(data_source_id, environment, catalog_name, schema_name):
    return ':'.join([
        str(data_source_id or ''),
        _normalize_part(environment).lower(),
        _normalize_part(catalog_name).lower(),
        _normalize_part(schema_name).lower(),
    ])


def _build_asset_qualified_name(data_source_id, environment, catalog_name, schema_name, asset_type, object_name):
    return ':'.join([
        str(data_source_id or ''),
        _normalize_part(environment).lower(),
        _normalize_part(catalog_name),
        _normalize_part(schema_name),
        _normalize_part(asset_type).lower(),
        _normalize_part(object_name),
    ])


def _split_catalog_schema(db_type, database_name):
    database_name = _normalize_part(database_name)
    if _normalize_part(db_type).lower() in {'presto', 'trino'} and '.' in database_name:
        catalog_name, schema_name = database_name.split('.', 1)
        return _normalize_part(catalog_name), _normalize_part(schema_name)
    return database_name, ''


def _resolve_collection_scope(db_type, database_name):
    catalog_name, schema_name = _split_catalog_schema(db_type, database_name)
    scope_level = 'datasource'
    if schema_name:
        scope_level = 'schema'
    elif catalog_name:
        scope_level = 'catalog'
    return scope_level, catalog_name, schema_name


def _bulk_create_in_batches(model, rows, db_alias, batch_size):
    if rows:
        model.objects.using(db_alias).bulk_create(rows, batch_size=batch_size)


def _bulk_update_in_batches(model, rows, fields, db_alias, batch_size):
    if rows:
        model.objects.using(db_alias).bulk_update(rows, fields, batch_size=batch_size)


def backfill_standard_asset_models(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    AssetNamespace = apps.get_model('dataasset', 'AssetNamespace')
    DataAsset = apps.get_model('dataasset', 'DataAsset')
    DataAssetColumn = apps.get_model('dataasset', 'DataAssetColumn')
    DataSource = apps.get_model('datasource', 'DataSource')
    MetaTable = apps.get_model('dataasset', 'MetaTable')
    MetaColumn = apps.get_model('dataasset', 'MetaColumn')
    MetaCollectionTask = apps.get_model('dataasset', 'MetaCollectionTask')

    datasource_types = dict(DataSource.objects.using(db_alias).values_list('id', 'db_type'))
    namespace_cache = {}
    namespace_rows = []

    for meta_table in MetaTable.objects.using(db_alias).all().iterator():
        environment = 'default'
        catalog_name, schema_name = _split_catalog_schema(
            datasource_types.get(meta_table.data_source_id), meta_table.database
        )
        namespace_key = (
            meta_table.data_source_id,
            environment,
            catalog_name,
            schema_name,
            meta_table.del_flag,
        )
        namespace = namespace_cache.get(namespace_key)
        if namespace is None:
            namespace = AssetNamespace(
                data_source_id=meta_table.data_source_id,
                environment=environment,
                catalog_name=catalog_name,
                schema_name=schema_name,
                namespace_key=_build_namespace_key(
                    meta_table.data_source_id, environment, catalog_name, schema_name
                ),
                display_name='.'.join([part for part in [catalog_name, schema_name] if part]) or environment,
                del_flag=meta_table.del_flag,
                create_by=meta_table.create_by,
                update_by=meta_table.update_by,
                create_time=meta_table.create_time,
                update_time=meta_table.update_time,
            )
            namespace_cache[namespace_key] = namespace
            namespace_rows.append(namespace)

    AssetNamespace.objects.using(db_alias).bulk_create(namespace_rows, batch_size=500)
    namespace_id_map = {
        (
            namespace.data_source_id,
            namespace.environment,
            namespace.catalog_name,
            namespace.schema_name,
            namespace.del_flag,
        ): namespace.id
        for namespace in AssetNamespace.objects.using(db_alias).all().only(
            'id', 'data_source_id', 'environment', 'catalog_name', 'schema_name', 'del_flag'
        ).iterator()
    }
    asset_rows = []
    for meta_table in MetaTable.objects.using(db_alias).all().iterator():
        environment = 'default'
        catalog_name, schema_name = _split_catalog_schema(
            datasource_types.get(meta_table.data_source_id), meta_table.database
        )
        namespace_key = (
            meta_table.data_source_id,
            environment,
            catalog_name,
            schema_name,
            meta_table.del_flag,
        )
        object_name = _normalize_part(meta_table.table_name)
        asset_rows.append(
            DataAsset(
                namespace_id=namespace_id_map[namespace_key],
                asset_type='table',
                object_name=object_name,
                qualified_name=_build_asset_qualified_name(
                    meta_table.data_source_id, environment, catalog_name, schema_name, 'table', object_name
                ),
                display_name=object_name,
                comment=meta_table.comment or '',
                is_active=meta_table.del_flag == '0',
                last_collected_at=meta_table.update_time,
                legacy_meta_table_id=meta_table.id,
                extra='',
                del_flag=meta_table.del_flag,
                create_by=meta_table.create_by,
                update_by=meta_table.update_by,
                create_time=meta_table.create_time,
                update_time=meta_table.update_time,
            )
        )
        if len(asset_rows) >= 500:
            _bulk_create_in_batches(DataAsset, asset_rows, db_alias, 500)
            asset_rows = []
    _bulk_create_in_batches(DataAsset, asset_rows, db_alias, 500)

    asset_id_map = {
        asset.legacy_meta_table_id: asset.id
        for asset in DataAsset.objects.using(db_alias).all().only('id', 'legacy_meta_table_id').iterator()
    }

    asset_column_rows = []
    for meta_column in MetaColumn.objects.using(db_alias).all().iterator():
        asset_id = asset_id_map.get(meta_column.table_id)
        if not asset_id:
            continue
        asset_column_rows.append(
            DataAssetColumn(
                asset_id=asset_id,
                ordinal_position=meta_column.order or 0,
                column_name=_normalize_part(meta_column.name),
                data_type=meta_column.type or '',
                is_nullable=not bool(meta_column.notnull),
                default_value=str(meta_column.default or ''),
                is_primary_key=bool(meta_column.primary),
                comment=meta_column.comment or '',
                legacy_meta_column_id=meta_column.id,
                extra='',
                del_flag=meta_column.del_flag,
                create_by=meta_column.create_by,
                update_by=meta_column.update_by,
                create_time=meta_column.create_time,
                update_time=meta_column.update_time,
            )
        )
        if len(asset_column_rows) >= 1000:
            _bulk_create_in_batches(DataAssetColumn, asset_column_rows, db_alias, 1000)
            asset_column_rows = []
    _bulk_create_in_batches(DataAssetColumn, asset_column_rows, db_alias, 1000)

    task_updates = []
    for task in MetaCollectionTask.objects.using(db_alias).all().iterator():
        task.scope_level, task.scope_catalog_name, task.scope_schema_name = _resolve_collection_scope(
            datasource_types.get(task.data_source_id),
            task.database_name,
        )
        task.scope_asset_name = ''
        task.run_mode = 'full'
        task_updates.append(task)
        if len(task_updates) >= 500:
            _bulk_update_in_batches(
                MetaCollectionTask,
                task_updates,
                ['scope_level', 'scope_catalog_name', 'scope_schema_name', 'scope_asset_name', 'run_mode'],
                db_alias,
                500,
            )
            task_updates = []
    _bulk_update_in_batches(
        MetaCollectionTask,
        task_updates,
        ['scope_level', 'scope_catalog_name', 'scope_schema_name', 'scope_asset_name', 'run_mode'],
        db_alias,
        500,
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('dataasset', '0002_move_datasource'),
        ('datasource', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='metacollectiontask',
            name='run_mode',
            field=models.CharField(blank=True, default='full', max_length=32, verbose_name='运行模式'),
        ),
        migrations.AddField(
            model_name='metacollectiontask',
            name='scope_asset_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='范围资产名'),
        ),
        migrations.AddField(
            model_name='metacollectiontask',
            name='scope_catalog_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='范围catalog'),
        ),
        migrations.AddField(
            model_name='metacollectiontask',
            name='scope_level',
            field=models.CharField(blank=True, default='datasource', max_length=32, verbose_name='采集范围层级'),
        ),
        migrations.AddField(
            model_name='metacollectiontask',
            name='scope_schema_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='范围schema'),
        ),
        migrations.CreateModel(
            name='AssetNamespace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('environment', models.CharField(default='default', max_length=32, verbose_name='环境')),
                ('catalog_name', models.CharField(blank=True, default='', max_length=255, verbose_name='catalog')),
                ('schema_name', models.CharField(blank=True, default='', max_length=255, verbose_name='schema')),
                ('namespace_key', models.CharField(db_index=True, max_length=768, verbose_name='命名空间键')),
                ('display_name', models.CharField(blank=True, default='', max_length=512, verbose_name='显示名称')),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_namespaces', to='datasource.datasource')),
            ],
            options={
                'verbose_name': '资产命名空间',
                'verbose_name_plural': '资产命名空间',
                'db_table': 'dataasset_asset_namespace',
            },
        ),
        migrations.CreateModel(
            name='DataAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('asset_type', models.CharField(choices=[('table', '数据表'), ('view', '视图'), ('materialized_view', '物化视图'), ('external_table', '外部表')], default='table', max_length=32, verbose_name='资产类型')),
                ('object_name', models.CharField(max_length=255, verbose_name='对象名称')),
                ('qualified_name', models.CharField(db_index=True, max_length=1024, verbose_name='限定名称')),
                ('display_name', models.CharField(blank=True, default='', max_length=255, verbose_name='显示名称')),
                ('comment', models.CharField(blank=True, default='', max_length=1024, verbose_name='描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否有效')),
                ('last_collected_at', models.DateTimeField(blank=True, null=True, verbose_name='最近采集时间')),
                ('legacy_meta_table_id', models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name='旧元数据表ID')),
                ('extra', models.TextField(blank=True, default='', verbose_name='扩展信息')),
                ('namespace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='dataasset.assetnamespace')),
            ],
            options={
                'verbose_name': '数据资产',
                'verbose_name_plural': '数据资产',
                'db_table': 'dataasset_data_asset',
            },
        ),
        migrations.CreateModel(
            name='DataAssetColumn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('ordinal_position', models.IntegerField(default=0, verbose_name='字段顺序')),
                ('column_name', models.CharField(max_length=255, verbose_name='字段名')),
                ('data_type', models.CharField(blank=True, default='', max_length=255, verbose_name='字段类型')),
                ('is_nullable', models.BooleanField(default=True, verbose_name='是否可空')),
                ('default_value', models.CharField(blank=True, default='', max_length=512, verbose_name='默认值')),
                ('is_primary_key', models.BooleanField(default=False, verbose_name='是否主键')),
                ('comment', models.CharField(blank=True, default='', max_length=1024, verbose_name='字段描述')),
                ('legacy_meta_column_id', models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name='旧元数据字段ID')),
                ('extra', models.TextField(blank=True, default='', verbose_name='扩展信息')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_columns', to='dataasset.dataasset')),
            ],
            options={
                'verbose_name': '数据资产字段',
                'verbose_name_plural': '数据资产字段',
                'db_table': 'dataasset_data_asset_column',
            },
        ),
        migrations.AddIndex(
            model_name='assetnamespace',
            index=models.Index(fields=['del_flag'], name='dataasset_a_del_fla_293828_idx'),
        ),
        migrations.AddIndex(
            model_name='assetnamespace',
            index=models.Index(fields=['data_source', 'environment'], name='dataasset_a_data_so_1f52b3_idx'),
        ),
        migrations.AddIndex(
            model_name='assetnamespace',
            index=models.Index(fields=['data_source', 'catalog_name', 'schema_name'], name='dataasset_a_data_so_ef98a7_idx'),
        ),
        migrations.AddConstraint(
            model_name='assetnamespace',
            constraint=models.UniqueConstraint(fields=('data_source', 'environment', 'catalog_name', 'schema_name', 'del_flag'), name='dataasset_namespace_unique_scope'),
        ),
        migrations.AddIndex(
            model_name='dataasset',
            index=models.Index(fields=['del_flag'], name='dataasset_d_del_fla_4eb949_idx'),
        ),
        migrations.AddIndex(
            model_name='dataasset',
            index=models.Index(fields=['namespace', 'object_name'], name='dataasset_d_namespa_9f954a_idx'),
        ),
        migrations.AddIndex(
            model_name='dataasset',
            index=models.Index(fields=['asset_type'], name='dataasset_d_asset_t_16f8e8_idx'),
        ),
        migrations.AddConstraint(
            model_name='dataasset',
            constraint=models.UniqueConstraint(fields=('namespace', 'asset_type', 'object_name', 'del_flag'), name='dataasset_asset_unique_object'),
        ),
        migrations.AddIndex(
            model_name='dataassetcolumn',
            index=models.Index(fields=['del_flag'], name='dataasset_d_del_fla_67ef38_idx'),
        ),
        migrations.AddIndex(
            model_name='dataassetcolumn',
            index=models.Index(fields=['asset', 'ordinal_position'], name='dataasset_d_asset_i_2826d9_idx'),
        ),
        migrations.AddIndex(
            model_name='dataassetcolumn',
            index=models.Index(fields=['asset', 'column_name'], name='dataasset_d_asset_i_290509_idx'),
        ),
        migrations.AddConstraint(
            model_name='dataassetcolumn',
            constraint=models.UniqueConstraint(fields=('asset', 'column_name', 'del_flag'), name='dataasset_asset_column_unique_name'),
        ),
    ]
