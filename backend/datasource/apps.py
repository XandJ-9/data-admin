from django.apps import AppConfig


class DatasourceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datasource'
    verbose_name = '数据源管理'