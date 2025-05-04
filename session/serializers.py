from rest_framework import serializers
from .models import ServiceClass, ServicesContainer
from orgs.serializers import OrgSerializer
from django.contrib.auth.models import User
from organizations.models import Organization
from .models import EnviromentalSession, CoEnvSession, FloaterSession, SessionsContainer


class CreateSessionByTimeSerializer(serializers.Serializer):
    sessions_list = ['E', 'C', 'F']


    name = serializers.CharField(max_length = 50)
    time_obj = serializers.IntegerField()
    session_type = serializers.ChoiceField(choices = sessions_list)
    organization = serializers.IntegerField()

    def validate_service_type(self, value):
         if self.get_service_class(value) is None:
             raise serializers.ValidationError(" must be E, C, F")
         return value

    def validate(self,data):
        s, t = self.get_service_class(data["session_type"])
        object = t.objects.get(pk = data['time_obj'])
        if data["session_type"] != 'C':
            object = object.dates

        if getattr(object, 'organization').pk != data['organization']:
            raise serializers.ValidationError(" can only includ time object in org")
        return data


    def get_service_class(self, k):
        from tiempo.models import WyzTimeModel, WyzFloatModel

        if k == 'E':
            return EnviromentalSession, WyzTimeModel
        if k == 'C':
            return CoEnvSession, EnviromentalSession
        if k == 'F':
            return FloaterSession, WyzFloatModel
        return None


    def create(self):
        s, t = self.get_service_class(self.validated_data.pop("session_type"))
        object = t.objects.get(pk = self.validated_data.pop('time_obj'))
        org = Organization.objects.get(pk = self.validated_data.pop('organization'))
        obj = s.create_obj(object, org, **self.validated_data)

class AddUserToSessionSerializer(serializers.Serializer):

    adders_list = ['R', 'O', 'U']

    session_pk = serializers.IntegerField()
    adder_type = serializers.ChoiceField(choices = adders_list)
    organization = serializers.IntegerField()
    user = serializers.IntegerField()


    def validate_adder_type(self, value):
         if self.get_adder_class(value) is None:
             raise serializers.ValidationError(" must be R, O and U")
         return value

    def validate(self,data):
        org = Organization.objects.get(pk = data["organization"])
        s = SessionsContainer.objects.get(pk = data["session_pk"])
        user = User.objects.get(pk = data["user"])
        obj = s.content_object
        t = self.get_adder_class(data["adder_type"])
        if  not getattr(obj,f'can_add_{t}')(user, org):
            raise serializers.ValidationError(f"{t} type user is not in your organization to add")
        if not getattr(obj, f'valid_{t}'):
            raise serializers.ValidationError(f"{t} type user is not alloed to be added ")
        return data


    def get_adder_class(self, k):
        if k == 'R':
            return 'reciever'
        if k == 'O':
            return 'overwatcher'
        if k == 'U':
            return 'org_user'
        return None

    def add(self):
        data = self.validated_data
        s = SessionsContainer.objects.get(pk = data["session_pk"])
        user = User.objects.get(pk = data["user"])
        obj = s.content_object
        t = self.get_adder_class(data["adder_type"])

        getattr(obj, f'add_{t}')(user)




class OverlappingSerializer(serializers.Serializer):
     def __init__(self, *args, **kwargs):
         user = kwargs['user']
         super(OverlappingSerializer, self).init(*args, **kwargs)


     overlapping_pk = serializers.IntegerField()

     def validate(self, data):
        try:
            o = OverlappingSessions.objects.get(pk = data['overlapping_pk'])
        except OverlappingSessions.DoesNotExist:
           raise serializers.ValidationError("bro you're not a real user")
        if not o.decision.can_approve(user):
           raise serializers.ValidationError("not allowed to make any decions right now")
        return data


     def approve(self):
         o = OverlappingSessions.objects.get(pk = data['overlapping_pk'])
         o.decision.approve(user)


class ChangeProposalSerializer(serializers.Serializer):
     def __init__(self, *args, **kwargs):
         user = kwargs['user']
         super(OverlappingSerializer, self).init(*args, **kwargs)


     overlapping_pk = serializers.IntegerField()

     def validate(self, data):
        try:
            o = OverlappingSessions.objects.get(pk = data['overlapping_pk'])
        except OverlappingSessions.DoesNotExist:
           raise serializers.ValidationError("bro you're not a real user")
        if not o.decision.can_approve(user):
           raise serializers.ValidationError("not allowed to make any decions right now")
        return data

          #computer has added component to this
     def change_proposal(self):
         o = OverlappingSessions.objects.get(pk = data['overlapping_pk'])
         o.priority = not(o.priority)
         o.decision.approve(self.user)
         o.save()
