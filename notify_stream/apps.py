from django.apps import AppConfig


class NotifyStreamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notify_stream'

    def ready(self):
        from . import signals
