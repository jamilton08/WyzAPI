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
        # decode & parse query string (may be empty)
        raw_qs = scope.get("query_string", b"")
        qs = parse_qs(raw_qs.decode())

        # only if there's a token parameter, do your lookup
        token_list = qs.get("token")
        if token_list:
            token = token_list[0]
            user = await returnUser(token)
            scope["user"] = user

        # always continue to the next app in the stack
        return await self.app(scope, receive, send)
