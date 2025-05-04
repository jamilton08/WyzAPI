from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def returnUser(token_string):
    try:
        j = JWTAuthentication()
        v_token = j.get_validated_token(token_string)
        user = j.get_user(v_token)

    except:
        user = AnonymousUser()
    return user


class TokenAuthMiddleWare:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"]
        query_params = query_string.decode()
        query_dict = parse_qs(query_params)
        token = query_dict["token"][0]
        user = await returnUser(token)
        scope["user"] = user
        return await self.app(scope, receive, send)
