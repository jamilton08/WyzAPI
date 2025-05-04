from functools import wraps
from django.http import HttpResponseRedirect
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.renderers import JSONRenderer




def secure_org_invite(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
        from orgs.utilities import is_within_org
        from organizations.models import Organization

        org = Organization.objects.get(pk = request.data['organization'])

        if not is_within_org(request.user, org):
            res  = Response(status=status.HTTP_400_BAD_REQUEST)
            res.accepted_renderer = JSONRenderer()
            res.accepted_media_type = 'application/json'
            res.renderer_context = {
                    'request': request,
                    'view': function,
                    }
            return res

        return function(request,*args, **kwargs)
  return wrap

def secure_user_request(function):
     @wraps(function)
     def wrap(request, *args, **kwargs):
           if 'signee' in request.data:
               request.data.update({'signee': request.user.pk})
           else:
               request.data['signee'] = request.user.pk

           return function(request,*args, **kwargs)
     return wrap


def secure_user_accept(c):
    def decorator(function):
      @wraps(function)
      def wrap(request, *args, **kwargs):

          id = request.data.get('invite_id')
          accept = request.data.get('action')
          res = None
          try:
              acceptance= c.objects.get(id=id)
          except c.DoesNotExist:
              res = Response(status=status.HTTP_404_NOT_FOUND)

          if request.user != acceptance.signee:
              res = Response(status=status.HTTP_403_FORBIDDEN)

          #elif acceptance not in c.objects.all_invites():
             #res = Response(status = status.HTTP_409_CONFLICT)

          if res is None:
             return function(request, acceptance, accept)
          else:
                res.accepted_renderer = JSONRenderer()
                res.accepted_media_type = 'application/json'
                res.renderer_context = {
                        'request': request,
                        'view': function,
                        }
                return res
      return wrap
    return decorator



def secure_org_accept(c):
    def decorator(function):
      @wraps(function)
      def wrap(request, *args, **kwargs):
          from orgs.utilities import is_within_org
          id = request.data.get('invite_id')
          accept = request.data.get('action')
          print(accept, "the id is here")
          res = None
          acceptance = None
          try:
              acceptance= c.objects.get(id=id)
          except c.DoesNotExist:
              res = Response(status=status.HTTP_404_NOT_FOUND)
          if acceptance :
              if not is_within_org(request.user, acceptance.organization ):
                  print(acceptance.organization,  "which one is it")
                  res = Response(status=status.HTTP_403_FORBIDDEN)

              elif acceptance not in c.objects.all_requests():
                 res = Response(status = status.HTTP_409_CONFLICT)

          if res is None:
             return function(request, acceptance, accept)
          else:
                res.accepted_renderer = JSONRenderer()
                res.accepted_media_type = 'application/json'
                res.renderer_context = {
                        'request': request,
                        'view': function,
                        }
                return res
      return wrap
    return decorator
