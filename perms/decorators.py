from functools import wraps
from django.http import HttpResponseRedirect
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

def create_dict_copy(data):
    copy = dict()
    for key, value  in data.items():
        copy[key] = value
    return copy

def second_level_perms(content, perm_type):
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            from django.contrib.contenttypes.models import ContentType
            from perms.models import PermissionSecondLayerModel
            print("made it here")
            if not 'HTTP_OBJECT' in request.META:
                raise KeyError("must have http object  permission")
            accesible, org = PermissionSecondLayerModel.has_perm(request.user, content, request.META['HTTP_OBJECT'], perm_type)
            if accesible:
                kwargs["organization"] = org
                kwargs["permissions"] = PermissionSecondLayerModel.get_permission(content, request.META['HTTP_OBJECT'], perm_type)
                kwargs["verified"] = True
                if hasattr(content, 'priority_parent'):
                    request.data.update({content.priority_parent: request.META['HTTP_OBJECT']})
                else:
                    try :
                        request.data.update({'organization': org.pk})
                    except AttributeError:
                        print("couldnt")
                return function(request,*args, **kwargs)
            else:
                res  = Response(status=status.HTTP_403_FORBIDDEN)
                res.accepted_renderer = JSONRenderer()
                res.accepted_media_type = 'application/json'
                res.renderer_context = {
                        'request': request,
                        'view': function,
                        }
                return res
        return wrapper
    return decorator

#NOTE this relies on  out
def functional_access(functional_string):
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            from perms.models import PermissionTwoPointFiveLayerModel as p
            print("you're in functional access", kwargs)
            accesible = p.verify_function(kwargs["permissions"], functional_string, request.user, kwargs["organization"])
            print (accesible, " this is accesible")
            if accesible and kwargs["verified"]:
                return function(request,*args, **kwargs)
            else:
                res  = Response(status=status.HTTP_403_FORBIDDEN)
                res.accepted_renderer = JSONRenderer()
                res.accepted_media_type = 'application/json'
                res.renderer_context = {
                        'request': request,
                        'view': function,
                        }
                return res
        return wrapper
    return decorator


@api_view(['GET'])
def failed(request,*args, **kwargs):
    return Response(status=status.HTTP_403_FORBIDDEN)


from django.http import HttpResponseForbidden
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from perms.models import PermissionSecondLayerModel, PermissionTwoPointFiveLayerModel as p

class SecondLevelPermissionMixin(permissions.BasePermission):
    permissions = [IsAuthenticated]
    content = None
    perm_type = None
    
    def has_permission(self, request):
        """
        Check if the user has second-level permissions based on the request and permission type.
        """
        print("is it passing thorough here ")
        if not 'HTTP_OBJECT' in request.META:
            raise KeyError("must have http object permission")
        print(request.user, self.content, request.META['HTTP_OBJECT'], self.perm_type)
        accessible, org = PermissionSecondLayerModel.has_perm(
            request.user, self.content, request.META['HTTP_OBJECT'], self.perm_type
        )
        
        return accessible, org

    def handle_no_permission(self, request):
        """
        Return a 403 forbidden response.
        """
        
        res = Response(status=status.HTTP_403_FORBIDDEN)
        res.accepted_renderer = JSONRenderer()
        res.accepted_media_type = 'application/json'
        res.renderer_context = {'request': request, 'view': self}
        return res

    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to include permission checks before allowing access.
        """
        try:
            accessible, org = self.has_permission(request)
            if accessible:
                kwargs["organization"] = org
                if hasattr(self.content, 'priority_parent'):
                    request.data.update({self.content.priority_parent: request.META['HTTP_OBJECT']})
                else:
                    try:
                        request.data.update({'organization': org.pk})
                    except AttributeError:
                        print("couldn't update request data")
            else:
                return self.handle_no_permission(request)
        except KeyError as e:
            return HttpResponseForbidden(str(e))
        
        return super().dispatch(request, *args, **kwargs)


class FunctionalAccessMixin:
    functional_string = None  # Set this in the view that uses the mixin

    def check_functional_access(self, request, *args, **kwargs):
        if not self.functional_string:
            raise ValueError("Functional string must be defined in the view using this mixin.")
        
        print("You're in functional access", kwargs)
        
        # Check if the user has access
        accessible = p.verify_function(kwargs["permissions"], self.functional_string, request.user, kwargs["organization"])
        print(accessible, "this is accessible")

        # If accessible and verified, return None to proceed with the view function
        if accessible and kwargs.get("verified"):
            return None

        # If not accessible, return a 403 Forbidden response
        res = Response(status=status.HTTP_403_FORBIDDEN)
        res.accepted_renderer = JSONRenderer()
        res.accepted_media_type = 'application/json'
        res.renderer_context = {
            'request': request,
            'view': self,
        }
        return res