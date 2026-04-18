from django.db import transaction

from .models import (
    AssetNamespace,
    DataAsset,
    DataAssetColumn,
    MetaColumn,
    MetaTable,
    build_asset_qualified_name,
    build_namespace_key,
    normalize_asset_part,
    split_catalog_schema,
)


def _apply_audit_fields(obj, created, user):
    username = getattr(user, 'username', '')
    if not username:
        return
    if created:
        obj.create_by = username
        obj.update_by = username
        obj.save(update_fields=['create_by', 'update_by'])
    else:
        obj.update_by = username
        obj.save(update_fields=['update_by', 'update_time'])


def upsert_asset_namespace(data_source_id, catalog_name='', schema_name='', environment='default', user=None):
    environment = normalize_asset_part(environment) or 'default'
    catalog_name = normalize_asset_part(catalog_name)
    schema_name = normalize_asset_part(schema_name)
    namespace, created = AssetNamespace.objects.update_or_create(
        data_source_id=data_source_id,
        environment=environment,
        catalog_name=catalog_name,
        schema_name=schema_name,
        del_flag='0',
        defaults={
            'namespace_key': build_namespace_key(data_source_id, environment, catalog_name, schema_name),
            'display_name': '.'.join([part for part in [catalog_name, schema_name] if part]) or environment,
        },
    )
    _apply_audit_fields(namespace, created, user)
    return namespace


def sync_standard_asset_from_meta_table(meta_table, user=None):
    catalog_name, schema_name = split_catalog_schema(meta_table.data_source.db_type, meta_table.database)
    namespace = upsert_asset_namespace(
        data_source_id=meta_table.data_source_id,
        catalog_name=catalog_name,
        schema_name=schema_name,
        environment='default',
        user=user,
    )
    object_name = normalize_asset_part(meta_table.table_name)
    asset_defaults = {
        'namespace': namespace,
        'asset_type': DataAsset.AssetType.TABLE,
        'object_name': object_name,
        'qualified_name': build_asset_qualified_name(
            namespace.data_source_id,
            namespace.environment,
            namespace.catalog_name,
            namespace.schema_name,
            DataAsset.AssetType.TABLE,
            object_name,
        ),
        'display_name': object_name,
        'comment': meta_table.comment or '',
        'is_active': True,
        'last_collected_at': meta_table.update_time,
        'legacy_meta_table_id': meta_table.id,
        'del_flag': '0',
    }
    asset = DataAsset.objects.filter(legacy_meta_table_id=meta_table.id).first()
    if asset:
        created = False
        for field, value in asset_defaults.items():
            setattr(asset, field, value)
        asset.save()
    else:
        asset, created = DataAsset.objects.update_or_create(
            namespace=namespace,
            asset_type=DataAsset.AssetType.TABLE,
            object_name=object_name,
            del_flag='0',
            defaults=asset_defaults,
        )
    _apply_audit_fields(asset, created, user)

    columns = MetaColumn.objects.filter(table=meta_table, del_flag='0').order_by('order', 'id')
    seen_column_ids = set()
    for meta_column in columns:
        normalized_name = normalize_asset_part(meta_column.name)
        column_defaults = {
            'asset': asset,
            'ordinal_position': meta_column.order or 0,
            'column_name': normalized_name,
            'data_type': meta_column.type or '',
            'is_nullable': not bool(meta_column.notnull),
            'default_value': str(meta_column.default or ''),
            'is_primary_key': bool(meta_column.primary),
            'comment': meta_column.comment or '',
            'legacy_meta_column_id': meta_column.id,
            'del_flag': '0',
        }
        column = DataAssetColumn.objects.filter(legacy_meta_column_id=meta_column.id).first()
        if column:
            column_created = False
            for field, value in column_defaults.items():
                setattr(column, field, value)
            column.save()
        else:
            column, column_created = DataAssetColumn.objects.update_or_create(
                asset=asset,
                column_name=normalized_name,
                del_flag='0',
                defaults=column_defaults,
            )
        seen_column_ids.add(meta_column.id)
        _apply_audit_fields(column, column_created, user)
    DataAssetColumn.objects.filter(asset=asset, del_flag='0').exclude(legacy_meta_column_id__in=seen_column_ids).delete()
    return asset


def collect_table_metadata(info, ds_id, table, user=None):
    from apps.dbutils import get_table_info, get_table_schema

    tinfo = get_table_info(info, table) or {}
    cols = get_table_schema(info, table) or []
    comment = tinfo.get('comment') or ''
    database_name = tinfo.get('databaseName') or ''

    with transaction.atomic():
        meta_table, created = MetaTable.objects.update_or_create(
            data_source_id=ds_id,
            table_name=table,
            database=database_name,
            defaults={'comment': comment, 'del_flag': '0'}
        )
        _apply_audit_fields(meta_table, created, user)

        if not cols:
            raise ValueError(f'表 {table} 的字段采集结果为空，已中止同步')

        MetaColumn.objects.filter(data_source_id=ds_id, table=meta_table).delete()

        for raw_column in cols:
            meta_column, column_created = MetaColumn.objects.update_or_create(
                data_source_id=ds_id,
                table=meta_table,
                name=raw_column.get('name'),
                defaults={
                    'order': raw_column.get('order') or 0,
                    'type': raw_column.get('type') or '',
                    'notnull': bool(raw_column.get('notnull')),
                    'default': str(raw_column.get('default') or ''),
                    'primary': bool(raw_column.get('primary')),
                    'comment': raw_column.get('comment') or '',
                    'del_flag': '0'
                }
            )
            _apply_audit_fields(meta_column, column_created, user)

        sync_standard_asset_from_meta_table(meta_table, user=user)
        return meta_table
