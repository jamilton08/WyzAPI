from django.shortcuts import render

from django.views.generic.base import RedirectView
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from perms.decorators import second_level_perms
from organizations.models import Organization



@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "A")
def create_session(request, *args, **kwargs):
    from .serializers import CreateSessionByTimeSerializer
    if request.method == 'POST':
        serializer = CreateSessionByTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.create()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def add_user_to_session(request, *args, **kwargs):
    from .serializers import AddUserToSessionSerializer
    if request.method == 'PUT':
        serializer = AddUserToSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.add()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "A")
def sign_overlap(request, *args, **kwargs):
    from .serializers import OverlappingSerializer
    if request.method == 'POST':
        serializer = OverlappingSerializer(data=request.data, user = reqeust.user)
        if serializer.is_valid():
            serializer.approve()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def change_overlap(request, *args, **kwargs):
    from .serializers import AddUserToSessionSerializer
    if request.method == 'PUT':
        serializer = ChangeProposalSerializer(data=request.data, user = request.user)
        if serializer.is_valid():
            serializer.change_proposal()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
