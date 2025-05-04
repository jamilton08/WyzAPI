from django.shortcuts import render
# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from organizations.models import Organization
from perms.decorators import second_level_perms, functional_access
from .serializers import *
from .models import RecieverSignee, OverwatchSignee, ServiceReciever
from global_utilities.security.invitations_decorators import secure_org_invite, secure_user_request, secure_user_accept, secure_org_accept
from actions.signals import record_action_signal
from actions.models import Record
from perms.decorators import SecondLevelPermissionMixin


@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "A")
@functional_access("invite_reciever")
@secure_org_invite
def reciever_invite(request, *args, **kwargs):
    print(kwargs, "brodie")
    if request.method == 'POST':
        print(request.data)
        request.data['admin_approve'] = request.user.pk
        serializer = RecieverSigneeSerializer(data=request.data)

        if serializer.is_valid():
            instance = serializer.create()
            record_action_signal.send(sender = instance.__class__, instance = instance,user = request.user, el = Record.SENT)

            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@secure_user_request
def reciever_request(request):
    if request.method == 'POST':
        serializer = RecieverSigneeSerializer(data=request.data)

        if serializer.is_valid():
            instance  = serializer.create()
            record_action_signal.send(sender = instance.__class__,instance = instance, user = request.user, el = Record.REQUESTED)
            return Response( status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@secure_user_accept(RecieverSignee)
def reciever_accept(request, acceptance, accept):
    from django.forms.models import model_to_dict


    serializer = RecieverSigneeSerializer(data=model_to_dict(acceptance))

    if serializer.is_valid():
            if bool(accept):
                acceptance.user_accept()
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.ACCEPTED)

            else:
                acceptance.deny_accept()
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.DECLINED)
            return Response( status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@second_level_perms(content = Organization, perm_type = "A")
@secure_org_accept(RecieverSignee)
def reciver_org_accept(request, acceptance, accept):
    from django.forms.models import model_to_dict

    serializer = RecieverSigneeSerializer(data=model_to_dict(acceptance))

    if serializer.is_valid():
            if bool(accept):
                acceptance.org_accept(request.user)
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.ACCEPTED)
            else:
                acceptance.deny_accept()
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.DECLINED)
            return Response( status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "A")
@secure_org_invite
def overwatch_invite(request, *args, **kwargs):
    if request.method == 'POST':
        print(request.data)
        request.data['admin_approve'] = request.user.pk
        print("do you make it here")
        serializer = OverwatchSigneeSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.create()
            record_action_signal.send(sender = instance.__class__,instance = instance, user = request.user, el = Record.SENT)
            return Response(status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@secure_user_request
def overwatch_request(request):
    if request.method == 'POST':
        print(request.data)
        serializer = OverwatchSigneeSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.create()
            record_action_signal.send(sender = instance.__class__,instance = instance, user = request.user, el = Record.REQUESTED)
            return Response( status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@secure_user_accept(OverwatchSignee)
def overwatch_accept(request, acceptance, accept):
    from django.forms.models import model_to_dict

    serializer = OverwatchSigneeSerializer(data=model_to_dict(acceptance))


    if serializer.is_valid():
            if bool(accept):
                acceptance.user_accept()
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.ACCEPTED)
            else:
                acceptance.deny_accept()
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.DECLINED)
            return Response( status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@second_level_perms(content = Organization, perm_type = "A")
@secure_org_accept(OverwatchSignee)
def overwatch_org_accept(request, acceptance, accept):
    from django.forms.models import model_to_dict

    serializer = OverwatchSigneeSerializer(data=model_to_dict(acceptance))

    if serializer.is_valid():
            if bool(accept):
                acceptance.org_accept(request.user)
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.ACCEPTED)
            else:
                acceptance.deny_accept()
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.DECLINED)
            return Response( status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetSearchedUsers(generics.ListCreateAPIView, SecondLevelPermissionMixin):
    content = Organization
    perm_type = "A"
    serializer_class = SearchedUserSerializer

    def list(self, request, last, search_term):
        from .user_searches import Searcher  
        query = Searcher.range_return(last, search_term) 
        org = self.content.objects.get(pk = request.META["HTTP_OBJECT"])  
        serializer = self.serializer_class(query, many=True, org = org, user = request.user)
        return Response(serializer.data)
    
class GetRecieversOverwatchers(generics.ListCreateAPIView, SecondLevelPermissionMixin):
    content = Organization
    perm_type = "A"
    serializer_class = AttachedRecieverSerializer

    def list(self, request):
        query =  self.serializer_class.Meta.model.objects.get_organization_recievers(Organization.objects.get(pk = request.META["HTTP_OBJECT"])) 
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data)
    
class GetOverwatchersRecievers(generics.ListCreateAPIView, SecondLevelPermissionMixin):
    content = Organization
    perm_type = "A"
    serializer_class = AttachedRecieverSerializer

    def list(self, request):
        print(request, "this is it here ", request.META)
        query =  self.serializer_class.Meta.model.objects.get_organization_recievers(Organization.objects.get(pk = request.META["HTTP_OBJECT"])) 
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data)

