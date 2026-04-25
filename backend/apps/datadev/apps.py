from django.apps import AppConfig


class DatadevConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.datadev'
    verbose_name = '建模与加工'

    def ready(self):
        import apps.executors  # noqa: F401
