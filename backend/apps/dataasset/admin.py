from django.contrib import admin
from .models import MetaTable, MetaColumn, MetaCollectionTask, TableLineage


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
    list_display = ['id', 'task_id', 'data_source', 'status', 'progress', 'total_tables', 'collected_tables']
    search_fields = ['task_id']
    list_filter = ['status', 'data_source']


@admin.register(TableLineage)
class TableLineageAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_table', 'target_table', 'lineage_type', 'del_flag']
    search_fields = ['source_table__table_name', 'target_table__table_name', 'description']
    list_filter = ['lineage_type', 'del_flag']
