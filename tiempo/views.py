from django.shortcuts import render

from django.views.generic.base import RedirectView
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import WyzDateModel, WyzTimeModel, DateTimeCopyBoard
from .serializers import CreateWyzDateSerializer, CreateWyzTimeSerializer, CopyDateTimeSerializer,\
 PasteDateTimeSerializer, CreateWyzFloatSerializer, DateExtendSerializer, TimeShiftSerializer,\
 TimeExpandSerializer, FloatShiftSerializer, FloatExpandSerializer, WyzDateModelSerializer
from perms.decorators import second_level_perms
from organizations.models import Organization
from global_utilities.security.users import retrieve_org_user


@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "E")
def create_dates(request, *args, **kwargs):
    print(request.data)
    if request.method == 'POST':
        serializer = CreateWyzDateSerializer(data=request.data )
        if serializer.is_valid():
            serializer.create()
            return Response({}, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
def create_times(request, *args, **kwargs):
    if request.method == 'POST':
        serializer = CreateWyzTimeSerializer(data=request.data )
        if serializer.is_valid():
            serializer.create()

            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
def create_floats(request, *args, **kwargs):
    if request.method == 'POST':
        needed_field = CreateWyzFloatSerializer.remove_unused_feild(request.data)
        serializer = CreateWyzFloatSerializer(data=request.data, fields=(list(needed_field)[0],) )
        if serializer.is_valid():
            serializer.create()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@second_level_perms(content = WyzDateModel, perm_type = "R")
def get_available_dates(request, *args, **kwargs):
    from .models import WyzDateModel
    from .utilities import get_remaining_days as g
    if request.method == 'GET':
        mod = WyzDateModel.objects.get(pk = kwargs['pk'])
        print(g(mod))
        return Response(WyzDateModel.unconflict_dates(mod), status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def copy_datetime(request, *args, **kwargs):
    DateTimeCopyBoard.objects.remove_previous(kwargs['org_user'])
    DateTimeCopyBoard.objects.remove_expiry(5)
    if request.method == 'POST':
        serializer = CopyDateTimeSerializer(data=request.data )
        if serializer.is_valid():
            serializer.create()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "E")
@retrieve_org_user
def paste_datetime(request, *args, **kwargs):
    if request.method == 'POST':
        serializer = PasteDateTimeSerializer(data=request.data, clipboard =  kwargs['org_user'].date_clipboard)
        if serializer.is_valid():
            serializer.paste()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def shift_date(request, *args, **kwargs):
    if request.method == 'PUT':
        serializer = DateShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def expand_date(request, *args, **kwargs):
    if request.method == 'PUT':
        serializer = DateExtendSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def shift_time(request, *args, **kwargs):
    if request.method == 'PUT':
        serializer = TimeShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def expand_time(request, *args, **kwargs):
    if request.method == 'PUT':
        serializer = TimeExpandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def shift_float(request, *args, **kwargs):
    if request.method == 'PUT':
        serializer = FloatShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@second_level_perms(content = WyzDateModel, perm_type = "E")
@retrieve_org_user
def expand_float(request, *args, **kwargs):
    if request.method == 'PUT':
        serializer = FloatExpandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@second_level_perms(content = WyzDateModel, perm_type = "D")
def delete_date(request, *args, **kwargs):
    if request.method == 'DELETE':
        #must also remove permission
        WyzDateModel.objects.get(pk = kwargs['date_pk']).delete()
        return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@second_level_perms(content = WyzDateModel, perm_type = "A")
def delete_date(request, *args, **kwargs):
    if request.method == 'GET':
        #must also remove permission
        WyzDateModel.objects.get(pk = kwargs['date_pk']).delete()
        return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@second_level_perms(content = Organization, perm_type = "E")
def get_date(request, *args, **kwargs):
    if request.method == 'GET':
        print("here bro now ")
        org = request.data['organization']
        place = kwargs['obj_place']
        dates = WyzDateModel.get_org_parent_date(org)
        print(dates, place)
        if place < 0:
            curr= dates[0]
        if place < len(dates):
            curr = dates[place]
        if place >= len(dates):
            curr = dates[len(dates) - 1]
            #must also remove permission
        l = list()
        curr.structurize(l,1, WyzDateModelSerializer)
        print(l)

        return Response(l, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
