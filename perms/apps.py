from django.apps import AppConfig


class PermsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'perms'

    def ready(self):
        from .signals import permission_signals
