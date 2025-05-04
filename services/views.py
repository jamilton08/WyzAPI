from django.shortcuts import render

from django.views.generic.base import RedirectView
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, views
from perms.decorators import second_level_perms
from organizations.models import Organization



@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "A")
def create_service(request, *args, **kwargs):
    from .serializers import CreateServiceSerializer
    if request.method == 'POST':
        serializer = CreateServiceSerializer(data=request.data )
        if serializer.is_valid():
            serializer.create()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_org_services(request,org_pk):
    from .serializers import ServicesContainerSerializer
    from .models import ServicesContainer
    org = Organization.objects.get(pk = org_pk)
    serializer = ServicesContainerSerializer(ServicesContainer.objects.org_services(org), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@second_level_perms(content = Organization, perm_type = "A")
def add_to_service(request, *args, **kwargs):
    from .serializers import AddServiceSerializer
    if request.method == 'PUT':
        serializer = AddServiceSerializer(data=request.data, org = kwargs["organization"] )
        if serializer.is_valid():
            serializer.add()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
