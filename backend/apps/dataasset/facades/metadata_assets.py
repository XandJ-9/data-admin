"""Public facade for cross-app metadata and asset synchronization."""

from apps.dataasset.services import (
    collect_table_metadata,
    sync_standard_asset_from_meta_table,
    upsert_asset_namespace,
)


def upsert_asset_namespace_via_facade(*, data_source_id, catalog_name='', schema_name='', environment='default', user=None):
    return upsert_asset_namespace(
        data_source_id=data_source_id,
        catalog_name=catalog_name,
        schema_name=schema_name,
        environment=environment,
        user=user,
    )


def sync_standard_asset_from_meta_table_via_facade(meta_table, *, user=None):
    return sync_standard_asset_from_meta_table(meta_table, user=user)


def collect_table_metadata_via_facade(info, ds_id, table, *, user=None):
    return collect_table_metadata(info, ds_id, table, user=user)
