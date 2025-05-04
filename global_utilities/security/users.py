from organizations.models import Organization as O
from functools import wraps

def retrieve_org_user(function):
     @wraps(function)
     def wrap(request, *args, **kwargs):
           query =  request.user.organizations_organizationuser.filter(organization__in = O.objects.filter(pk = request.META['HTTP_OBJECT']))
           print("does this query exist my guy", query.exists())
           if query.exists():
               kwargs['org_user'] =  query.first()
           else:
            kwargs['org_user'] = None
           return function(request,*args, **kwargs)
     return wrap
