from django.shortcuts import render

from django.views.generic.base import RedirectView
# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from perms.decorators import second_level_perms, functional_access
from organizations.models import Organization
from django.contrib.auth.models import User




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
    


@api_view(['GET'])
@second_level_perms(content = Organization, perm_type = "E")
@functional_access("set_permissions")
def perm_transactional_exchange(request, asignee_id,  *args, **kwargs):
    if request.method == 'GET':
        from .serializers import FrontendPermSerializer, FrontendFPermSerializer
        from .utilities import get_permission_transactions, get_functional_transactions
        from orgs.utilities import get_org_user
        org =  kwargs["organization"]
        assigner_user = get_org_user(request.user, org)
        asignee_user = get_org_user(User.objects.get(pk = asignee_id), org)     
        assigner, asignee = get_permission_transactions(assigner_user, asignee_user)
        assignerF, asigneeF = get_functional_transactions(assigner_user, asignee_user)
        assigner_serializer = FrontendPermSerializer(data = list(assigner.values()), many = True)
        asignee_serializer = FrontendPermSerializer(data = list(asignee.values()), many = True)
        assignerF_serializer = FrontendFPermSerializer(assignerF, many=True)
        asigneeF_serializer = FrontendFPermSerializer(asigneeF, many=True)
        if assigner_serializer.is_valid() and asignee_serializer.is_valid():
            data = {
                "assigner": assigner_serializer.data,
                "asignee": asignee_serializer.data,
                "assigner_f": assignerF_serializer.data,
                "asignee_f": asigneeF_serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        print(assignerF_serializer.errors)
        return Response(assigner_serializer.errors, status=status.HTTP_400_BAD_REQUEST)