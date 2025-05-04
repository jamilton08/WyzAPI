from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from organizations.models import Organization



@database_sync_to_async
def returnOrg(pk):
    try:
        org = Organization.objects.get(pk = pk)

    except Organization.DoesNotExist:
        org =  None
    return org


class GetOrganizationMiddleWare:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        query_string = scope["query_string"]
        query_params = query_string.decode()
        print(query_params)
        query_dict = parse_qs(query_params)
        pk = query_dict["org"][0]
        org = await returnOrg(pk)
        scope["org"] = org
        return await self.app(scope, receive, send)
