from django.contrib import admin
from .models import DataSource


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'db_type', 'host', 'port', 'status', 'del_flag']
    search_fields = ['name', 'host']
    list_filter = ['db_type', 'status', 'del_flag']
