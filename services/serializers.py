from rest_framework import serializers
from .models import ServiceClass, ServicesContainer
from orgs.serializers import OrgSerializer
from django.contrib.auth.models import User


class CreateServiceSerializer(serializers.Serializer):
    services_list = ['E', 'C', 'F', 'O']


    name = serializers.CharField(max_length = 50)
    description = serializers.CharField(max_length = 200)
    service_type = serializers.ChoiceField(choices = services_list)
    organization = serializers.IntegerField()

    def validate_service_type(self, value):
         if self.get_service_class(value) is None:
             raise serializers.ValidationError(" must be E, C, F, or O")
         return value


    def get_service_class(self, k):
        from .models import Enviromental, CoEnv, Floater, Controller
        print(k)

        if k == 'E':
            return Enviromental
        if k == 'C':
            return CoEnv
        if k == 'F':
            return Floater
        if k == 'O' == Controller:
            return Controller
        return None


    def create(self):
        from organizations.models import Organization
        org = Organization.objects.get(pk = self.validated_data.pop('organization'))
        obj_type = self.get_service_class(self.validated_data.pop('service_type'))
        obj = getattr(obj_type, 'objects').\
        create( organization = org, **self.validated_data)
        return obj

class ServicesContainerSerializer(serializers.ModelSerializer):
    #day_of_week = serializers.SerializerMethodField('el_dia')

    #def el_dia(self,bro):
        #return bro.org_time.get_day_of_week_str()
    class Meta:
        model = ServicesContainer
        fields = '__all__'


class AddServiceSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop("org")
        super(AddServiceSerializer, self).__init__(*args, **kwargs)

    accepted_user_type = ["R", "O", "U"]
    user_type = serializers.ChoiceField(choices = accepted_user_type)
    user_pk = serializers.IntegerField()
    service_pk = serializers.IntegerField()


    def get_aut_instance(self, a):
        if a == "R":
            return "reciever"
        elif a == "O":
            return "overwatcher"
        elif a == "U":
            return "org_user"
        return ""

    def validate(self, data):
        from homosapiens.models import ServiceReciever
        from orgs.utilities import is_within_org
        user = User.objects.get(pk = data['user_pk'])
        type = data["user_type"]
        if type == "R" and user not in ServiceReciever.objects.get_organization_recievers_u(self.org):
            raise serializers.ValidationError("This is not a reciever in the organization")
        if type == "O" and user not in ServiceReciever.objects.get_organization_overwatchers_u(self.org):
            raise serializers.ValidationError("This is not a overwatcher in the organization")
        if type == "U" and not is_within_org(user, self.org):
            raise serializers.ValidationError("This is not a org_user in the organization")
        if ServicesContainer.objects.get(pk = data["service_pk"]).content_object.organization != self.org:
            raise ValidationError("it must be part of the organization ")
        return data

    def add(self):
        s = ServicesContainer.objects.get(pk = self.validated_data["service_pk"])
        getattr(s.content_object, f'add_{self.get_aut_instance(self.validated_data["user_type"])}')\
        (User.objects.get(pk = self.validated_data['user_pk']))
