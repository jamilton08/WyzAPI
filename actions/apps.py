from django.apps import AppConfig


class ActionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actions'

    def ready(self):
        from . import signals
        from . import reciever
