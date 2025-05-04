from django.apps import AppConfig


class HomosapiensConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'homosapiens'

    def ready(self):
        from . import signals
