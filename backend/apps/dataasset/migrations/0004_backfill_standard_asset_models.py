from django.db import migrations


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
        model.objects.using(db_alias).bulk_create(rows, batch_size=batch_size, ignore_conflicts=True)


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
    existing_namespaces = {
        (
            namespace.data_source_id,
            namespace.environment,
            namespace.catalog_name,
            namespace.schema_name,
            namespace.del_flag,
        ): namespace
        for namespace in AssetNamespace.objects.using(db_alias).all().iterator()
    }
    namespace_cache = dict(existing_namespaces)
    namespace_rows = []
    namespace_updates = []

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
        else:
            namespace.namespace_key = _build_namespace_key(
                meta_table.data_source_id, environment, catalog_name, schema_name
            )
            namespace.display_name = '.'.join([part for part in [catalog_name, schema_name] if part]) or environment
            namespace.create_by = meta_table.create_by
            namespace.update_by = meta_table.update_by
            namespace.create_time = meta_table.create_time
            namespace.update_time = meta_table.update_time
            if namespace.pk:
                namespace_updates.append(namespace)

    _bulk_create_in_batches(AssetNamespace, namespace_rows, db_alias, 500)
    _bulk_update_in_batches(
        AssetNamespace,
        namespace_updates,
        ['namespace_key', 'display_name', 'create_by', 'update_by', 'create_time', 'update_time'],
        db_alias,
        500,
    )
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
    existing_assets = {
        asset.legacy_meta_table_id: asset
        for asset in DataAsset.objects.using(db_alias).exclude(legacy_meta_table_id__isnull=True).iterator()
    }
    asset_rows = []
    asset_updates = []
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
        existing_asset = existing_assets.get(meta_table.id)
        if existing_asset is None:
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
        else:
            existing_asset.namespace_id = namespace_id_map[namespace_key]
            existing_asset.asset_type = 'table'
            existing_asset.object_name = object_name
            existing_asset.qualified_name = _build_asset_qualified_name(
                meta_table.data_source_id, environment, catalog_name, schema_name, 'table', object_name
            )
            existing_asset.display_name = object_name
            existing_asset.comment = meta_table.comment or ''
            existing_asset.is_active = meta_table.del_flag == '0'
            existing_asset.last_collected_at = meta_table.update_time
            existing_asset.extra = ''
            existing_asset.del_flag = meta_table.del_flag
            existing_asset.create_by = meta_table.create_by
            existing_asset.update_by = meta_table.update_by
            existing_asset.create_time = meta_table.create_time
            existing_asset.update_time = meta_table.update_time
            asset_updates.append(existing_asset)
        if len(asset_rows) >= 500:
            _bulk_create_in_batches(DataAsset, asset_rows, db_alias, 500)
            asset_rows = []
    _bulk_create_in_batches(DataAsset, asset_rows, db_alias, 500)
    _bulk_update_in_batches(
        DataAsset,
        asset_updates,
        [
            'namespace_id', 'asset_type', 'object_name', 'qualified_name', 'display_name', 'comment',
            'is_active', 'last_collected_at', 'extra', 'del_flag', 'create_by', 'update_by',
            'create_time', 'update_time',
        ],
        db_alias,
        500,
    )

    asset_id_map = {
        asset.legacy_meta_table_id: asset.id
        for asset in DataAsset.objects.using(db_alias).all().only('id', 'legacy_meta_table_id').iterator()
    }

    existing_columns = {
        column.legacy_meta_column_id: column
        for column in DataAssetColumn.objects.using(db_alias).exclude(legacy_meta_column_id__isnull=True).iterator()
    }
    asset_column_rows = []
    asset_column_updates = []
    for meta_column in MetaColumn.objects.using(db_alias).all().iterator():
        asset_id = asset_id_map.get(meta_column.table_id)
        if not asset_id:
            continue
        existing_column = existing_columns.get(meta_column.id)
        if existing_column is None:
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
        else:
            existing_column.asset_id = asset_id
            existing_column.ordinal_position = meta_column.order or 0
            existing_column.column_name = _normalize_part(meta_column.name)
            existing_column.data_type = meta_column.type or ''
            existing_column.is_nullable = not bool(meta_column.notnull)
            existing_column.default_value = str(meta_column.default or '')
            existing_column.is_primary_key = bool(meta_column.primary)
            existing_column.comment = meta_column.comment or ''
            existing_column.extra = ''
            existing_column.del_flag = meta_column.del_flag
            existing_column.create_by = meta_column.create_by
            existing_column.update_by = meta_column.update_by
            existing_column.create_time = meta_column.create_time
            existing_column.update_time = meta_column.update_time
            asset_column_updates.append(existing_column)
        if len(asset_column_rows) >= 1000:
            _bulk_create_in_batches(DataAssetColumn, asset_column_rows, db_alias, 1000)
            asset_column_rows = []
    _bulk_create_in_batches(DataAssetColumn, asset_column_rows, db_alias, 1000)
    _bulk_update_in_batches(
        DataAssetColumn,
        asset_column_updates,
        [
            'asset_id', 'ordinal_position', 'column_name', 'data_type', 'is_nullable', 'default_value',
            'is_primary_key', 'comment', 'extra', 'del_flag', 'create_by', 'update_by',
            'create_time', 'update_time',
        ],
        db_alias,
        1000,
    )

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
    atomic = False

    dependencies = [
        ('dataasset', '0003_metacollectiontask_run_mode_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_standard_asset_models, noop_reverse),
    ]
