
from rest_framework.permissions import IsAuthenticated
from perms.decorators import second_level_perms
from organizations.models import Organization
from .serializers import WyzAddressCreateSerializer
from rest_framework.views import APIView
from django.utils.decorators import method_decorator

class AbstractClassAddressLink(APIView):
    serializer = WyzAddressCreateSerializer
    permissions = [ IsAuthenticated]
    # NOTE: Nust provide how we will get this object when inherited


@method_decorator(second_level_perms(content = Organization, perm_type = "A"), name='post')
class OrganizationAssignAddress(AbstractClassAddressLink):
    def get_obj(self, request):
         return request.data['organization']


    def post(self, request, **kwargs):
        super(OrganizationAssignAddress, self).post(request)

class UserAssignAddress(AbstractClassAddressLink):
    def get_obj(self, request):
        return request.user.pk
