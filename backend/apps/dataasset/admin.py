from django.contrib import admin
from .models import (
    AssetNamespace,
    DataAsset,
    DataAssetColumn,
    MetaTable,
    MetaColumn,
    MetaCollectionTask,
    TableLineage,
)


@admin.register(AssetNamespace)
class AssetNamespaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'data_source', 'environment', 'catalog_name', 'schema_name', 'namespace_key', 'del_flag']
    search_fields = ['catalog_name', 'schema_name', 'namespace_key']
    list_filter = ['data_source', 'environment', 'del_flag']


@admin.register(DataAsset)
class DataAssetAdmin(admin.ModelAdmin):
    list_display = ['id', 'namespace', 'asset_type', 'object_name', 'qualified_name', 'is_active', 'del_flag']
    search_fields = ['object_name', 'qualified_name', 'display_name', 'comment']
    list_filter = ['asset_type', 'namespace__data_source', 'is_active', 'del_flag']


@admin.register(DataAssetColumn)
class DataAssetColumnAdmin(admin.ModelAdmin):
    list_display = ['id', 'asset', 'column_name', 'data_type', 'ordinal_position', 'is_primary_key', 'del_flag']
    search_fields = ['column_name', 'data_type', 'comment']
    list_filter = ['asset__namespace__data_source', 'is_primary_key', 'del_flag']


@admin.register(MetaTable)
class MetaTableAdmin(admin.ModelAdmin):
    list_display = ['id', 'data_source', 'table_name', 'database', 'del_flag']
    search_fields = ['table_name', 'database']
    list_filter = ['data_source', 'del_flag']


@admin.register(MetaColumn)
class MetaColumnAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'name', 'type', 'order', 'primary', 'del_flag']
    search_fields = ['name', 'type']
    list_filter = ['table__data_source', 'primary', 'del_flag']


@admin.register(MetaCollectionTask)
class MetaCollectionTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'task_id', 'data_source', 'status', 'scope_level', 'run_mode',
        'progress', 'total_tables', 'collected_tables'
    ]
    search_fields = ['task_id']
    list_filter = ['status', 'data_source', 'scope_level', 'run_mode']


@admin.register(TableLineage)
class TableLineageAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_table', 'target_table', 'lineage_type', 'del_flag']
    search_fields = ['source_table__table_name', 'target_table__table_name', 'description']
    list_filter = ['lineage_type', 'del_flag']
