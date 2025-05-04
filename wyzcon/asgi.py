"""
ASGI config for wyzcon project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

import task.routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from task.consumers import TaskConsumer
from actions.consumers import ActionsConsumer
from notify_stream.consumers import NotifyConsumers
from django.urls import path
from global_utilities.middlewares.websocket_jwt import TokenAuthMiddleWare
from global_utilities.middlewares.channels_org import GetOrganizationMiddleWare

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wyzcon.settings')

application = get_asgi_application()


application = ProtocolTypeRouter({
  'http': application,
  "websocket": TokenAuthMiddleWare(
          AllowedHostsOriginValidator(
                AuthMiddlewareStack(
                    URLRouter([
                        path("testing/", TaskConsumer.as_asgi()),
                        path("actions/", ActionsConsumer.as_asgi()),
                        path("notify/", NotifyConsumers.as_asgi())
                    ])
                )
            ),
    )
})