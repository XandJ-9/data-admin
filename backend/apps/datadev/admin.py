from django.contrib import admin
from .models import DataDevScript, DataDevScriptVersion, DataDevScriptExecution


@admin.register(DataDevScript)
class DataDevScriptAdmin(admin.ModelAdmin):
    list_display = ['id', 'script_name', 'script_code', 'script_type', 'status', 'owner', 'create_time']
    list_filter = ['script_type', 'status', 'del_flag']
    search_fields = ['script_name', 'script_code']


@admin.register(DataDevScriptVersion)
class DataDevScriptVersionAdmin(admin.ModelAdmin):
    list_display = ['id', 'script', 'version_number', 'is_current', 'create_by', 'create_time']
    list_filter = ['is_current']
    search_fields = ['script__script_name']


@admin.register(DataDevScriptExecution)
class DataDevScriptExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'script', 'execution_id', 'status', 'executor_type', 'executed_by', 'start_time', 'duration_seconds']
    list_filter = ['status', 'executor_type']
    search_fields = ['execution_id', 'script__script_name']
