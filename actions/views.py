from django.shortcuts import render

# Create your views here.
from django.db.models import Q
from django.shortcuts import render
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from organizations.models import Organization, OrganizationUser
from perms.decorators import second_level_perms

from actions.signals import record_action_signal
from actions.models import Record
from organizations.models import Organization


@api_view(['PUT'])
def respond_action(request, *args, **kwargs):
    from .models import RespondAction
    rp = RespondAction.objects.get(pk = request.data.action_id)
    if request.method == 'PUT':
        #incase of any changes in termis of  perm will check for user exists and etc and has permissions still because we didnt put the second layer perm annotation
        if not request.user in rp.content_object.content_object.handle_actions_queries():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rp.responding(request.user)

        return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
@second_level_perms(content = Organization, perm_type = "A")
def get_needed_responses(request, org,  *args, **kwargs):
    from .serializers import ResponseSerializer
    if request.method == 'GET':
        try:
            org = Organization.objects.get(pk = org)
        except Organization.DoesNotExist:
            return Response( "interesting that your scamming bro", status=status.HTTP_405_METHOD_NOT_ALLOWED)
        serializer = ResponseSerializer(request.user.need_to_respond.get_organization_responses_needed(org), many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    else:
        return Response( status=status.HTTP_400_BAD_REQUEST)
