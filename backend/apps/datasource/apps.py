from django.apps import AppConfig


class DatasourceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.datasource'
    verbose_name = '数据源管理'

    def ready(self):
        from . import task_source  # noqa: F401
