from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mdh_intranet.core'
    verbose_name = 'Core Infrastructure'

    def ready(self):
        import mdh_intranet.core.signals
