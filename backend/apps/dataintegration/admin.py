from django.contrib import admin

from .models import DataIntegrationTask


@admin.register(DataIntegrationTask)
class DataIntegrationTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'task_name',
        'task_code',
        'source_datasource',
        'target_datasource',
        'target_table_name',
        'load_type',
        'write_mode',
        'executor_type',
        'status',
    ]
    list_filter = ['load_type', 'write_mode', 'executor_type', 'status', 'del_flag']
    search_fields = ['task_name', 'task_code', 'target_table_name']
