from django.shortcuts import render

from django.views.generic.base import RedirectView
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from organizations.models import Organization, OrganizationUser
from perms.decorators import second_level_perms, functional_access
from actions.signals import record_action_signal
from actions.models import Record
from .serializers import OrgSerializer, SearchedOrgUserSerializer
from perms.decorators import SecondLevelPermissionMixin, FunctionalAccessMixin
from global_utilities.security.users import retrieve_org_user
from notify_stream.utilities import user_channel_form


@api_view(['POST'])
def create_org(request):
    from .serializers import CreateOrgExtSerializer
    from django.contrib.gis.geos import Point

    if request.method == 'POST':
        data = request.data
        if "location" in data:
            data["location"] = Point(data["location"][0], data["location"][1])

        serializer = CreateOrgExtSerializer(data=data, request=request )
        if serializer.is_valid():

            org = serializer.create(serializer.validated_data)


            data={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email':request.user.email
            }
            return Response(data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#this will require organizational permission
@api_view(['GET','POST'])
def org_signee_create(request):
    from .serializers import OrgSigneeSerializer
    try:
        organization= Organization.objects.get(pk=request.data['organization'])
    except Organization.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method=="GET":
        accepts = org.signees.all()
        serializer = OrgSigneesSerializer(accepts, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method =="POST":
        #will require functional manner of having permissions here with perms
        try:
            org_user = request.user.organizations_organizationuser.get(organization = organization)
            admin_approve = True
        except  OrganizationUser.DoesNotExist:
            admin_approve = False

        if admin_approve:
            request.data['admin_approve'] = org_user.user.pk
        serializer = OrgSigneeSerializer(data = request.data, user = request.user)
        if serializer.is_valid():
            instance = serializer.org_create()
            record_action_signal.send(sender = instance.__class__, instance = instance,user = request.user, el = Record.SENT)
            return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "E")
@functional_access("approve_provider_request")
def org_accept_and_get(request, *args, **kwargs):
    from .serializers import OrgAcceptInvite
    from django.forms.models import model_to_dict
    from .models import OrgSignees
    from .utilities import is_within_org

    pk = request.data['invite_id']
    accept = request.data['action']

    try:
        acceptance= OrgSignees.objects.get(pk=pk)
    except OrgSignees.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = OrgAcceptInvite(data=model_to_dict(acceptance), user = request.user)
    if serializer.is_valid():
        if not is_within_org(request.user, acceptance.organization ):
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
        created = serializer.org_update(acceptance, bool(accept))
        if created :
            record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.ACCEPTED)
            return Response(status=status.HTTP_201_CREATED)
        else :
            record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.DECLINED)
            return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
def user_signee_create(request):
    from .serializers import OrgSigneeSerializer
    if request.method=="GET":
        accepts = request.user.signees.all()
        serializer = OrgSigneesSerializer(accepts, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method =="POST":
        serializer = OrgSigneeSerializer(data = request.data, user = request.user)
        if serializer.is_valid():
            instance = serializer.user_create()
            record_action_signal.send(sender = instance.__class__,instance = instance, user = request.user, el = Record.REQUESTED)
            return Response( status=status.HTTP_201_CREATED)

@api_view(['POST'])
def user_accept_and_get(request):
    from .models import OrgSignees
    from django.forms.models import model_to_dict

    pk = request.POST.get('pk')
    accept = request.POST.get('action')
    try:
        acceptance= OrgSignees.objects.get(pk=pk)
    except OrgSignees.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user == acceptance.signee:
        serializer = OrgSigneeSerializer( data=model_to_dict(acceptance))
        if serializer.is_valid():
            created = serializer.user_update(acceptance, bool(accept))
            if created :
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.ACCEPTED)
                return Response(status=status.HTTP_201_CREATED)
            else :
                record_action_signal.send(sender = acceptance.__class__,instance = acceptance,  user = request.user, el = Record.DECLINED)
                return Response(status=status.HTTP_200_OK)
        print(serializer.errors)
    return Response( status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def org_invites_view(request, org_pk):
    org = Organization.objects.get(pk = org_pk)
    invitees_sent = OrgSignees.objects.orgs_sent_pending_invites(org)
    invitees = OrgSignees.objects.orgs_pending_invites(org)
    serializer_sent = OrgSigneeSerializer(invitees_sent, many=True)
    serializer = OrgSigneeSerializer(invitees, many=True)
    data = {}
    data.update({'sent': serializer_sent.data, 'recieved': serializer.data})
    return Response(data, status=status.HTTP_200_OK)



class OrganizationList(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrgSerializer
    permission_classes = [AllowAny]

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "E")
@functional_access("set_permissions")
def assign_perm(request, *args, **kwargs):
    from .serializers import PermissionRetainerSerializer
    from django.contrib.auth.models import User
    from .utilities import get_org_user
    from importlib import import_module as _i
    org_user = get_org_user(request.user, request.data['organization'])
    # TODO maybe extract later and put it as a decorator to access the user that will be permed
    org_permed_user = get_org_user(User.objects.get(pk = request.data['user']), request.data['organization'])
    serializer = _i("orgs.serializers").PermissionRetainerSerializer(data = request.data, org_user = org_user, user_to_perm = org_permed_user)
    if serializer.is_valid():
        data = serializer.validated_data
        if data["intention"] == "add":
            action = Record.ADDED
        elif data["intention"] == "remove":     
            action = Record.REMOVED
        instance = org_permed_user.permission_retainer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
        serializer.decision(serializer.validated_data)
        notify_users = record_action_signal.send(sender = instance.__class__,\
                                  instance = instance,\
                                  user = request.user,\
                                  el = action,\
                                  user_query =_i("django.contrib.auth.models")\
                                    .User\
                                    .objects\
                                    .filter(pk = org_permed_user.user.pk) ,\
                                  org =  org_permed_user.organization)
    
        return Response(data = {"users_to_notify" : user_channel_form(notify_users), "details": "implementing soon based on actions" }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetOrgUsers(generics.ListCreateAPIView, SecondLevelPermissionMixin, FunctionalAccessMixin):
    content = Organization
    perm_type = "A"
    serializer_class = SearchedOrgUserSerializer
    functional_string = "view_org_users"

    def list(self, request, last, search_term = ""):
        from homosapiens.user_searches import Searcher
        org = self.content.objects.get(pk = request.META["HTTP_OBJECT"])
        query =  Searcher.org_range_return(last,search_term, org) 
        serializer = self.serializer_class(query, many=True, org = org)
        return Response(serializer.data)


@api_view(['GET'])
@retrieve_org_user
def navigational_org_user(request, *args, **kwargs):
    if kwargs['org_user'] is None:
        print("wer are herae aglkajvajsdklfnealkwnrfekl afdlkanflkadsklfjlekware")
        data = {'pk': 999999999999, 'stack_level': 999999, 'permissions':list()}
        return Response(data, status=status.HTTP_201_CREATED)
    else:
        from .serializers import OrgUserPermSerializer
        serializer = OrgUserPermSerializer(kwargs['org_user'].permission_retainer)
        data = serializer.data
    return Response(serializer.data, status=status.HTTP_201_CREATED)