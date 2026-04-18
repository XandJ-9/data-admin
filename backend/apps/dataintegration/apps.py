from django.apps import AppConfig


class DataintegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dataintegration'
    verbose_name = '数据集成'

    def ready(self):
        import apps.executors  # noqa: F401
