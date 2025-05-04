from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RecieverSignee, OverwatchSignee, ServiceReciever
from importlib import import_module as _i



class RecieverSigneeSerializer(serializers.ModelSerializer):

    def create(self):
        inv = self.Meta.model.create(**self.validated_data)
        inv.save()
        return inv


    class Meta:
        model = RecieverSignee
        fields = '__all__'


class  OverwatchSigneeSerializer(serializers.ModelSerializer):

    def validate(self, data):
        org = _i("organizations.models").Organization
        try:
            print(data['organization'], data['reciever'].organization )
            if data['organization'] == data['reciever'].organization:
                return super(OverwatchSigneeSerializer, self).validate(data)
            else:
                raise serializers.ValidationError("each thing have diffirent organization")
        except org.DoesNotExist:
            raise serializers.ValidationError("organization must exist")

    def create(self):
        inv = self.Meta.model.create(**self.validated_data)
        inv.save()
        return inv

    class Meta:
        model =  OverwatchSignee
        fields = '__all__'
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RecieverSignee, OverwatchSignee


class RecieverSigneeSerializer(serializers.ModelSerializer):

    def create(self):
        inv = self.Meta.model.create(**self.validated_data)
        inv.save()
        return inv


    class Meta:
        model = RecieverSignee
        fields = '__all__'


class  OverwatchSigneeSerializer(serializers.ModelSerializer):

    def validate(self, data):
        org = _i("organizations.models").Organization
        try:
            print(data['organization'], data['reciever'].organization )
            if data['organization'] == data['reciever'].organization:
                return super(OverwatchSigneeSerializer, self).validate(data)
            else:
                raise serializers.ValidationError("each thing have diffirent organization")
        except org.DoesNotExist:
            raise serializers.ValidationError("organization must exist")

    def create(self):
        inv = self.Meta.model.create(**self.validated_data)
        inv.save()
        return inv

    class Meta:
        model =  OverwatchSignee
        fields = '__all__'

class SearchedUserSerializer(serializers.HyperlinkedModelSerializer):

    def __init__(self, *args, **kwargs):
            self.user= kwargs.pop('user')
            self.org = kwargs.pop('org')
            super(SearchedUserSerializer,self).__init__(*args, **kwargs)

    tags = serializers.SerializerMethodField("get_tags")
    is_user = serializers.SerializerMethodField('is_user_method')
    is_reciever = serializers.SerializerMethodField('is_reciever_method')
    is_overwatcher = serializers.SerializerMethodField('is_overwatcher_method')
    is_admin = serializers.SerializerMethodField('is_admin_method')
    is_staff = serializers.SerializerMethodField('is_staff_method')

    org_utils = _i("orgs.utilities")



    def get_tags(self, bro):
        from .user_searches import Searcher
        tags = Searcher.collect_tags(bro)
        print('here bro', tags)
        return tags 

    def is_user_method(self, bro):
        print('is user ', bro == self.user)
        return bro == self.user
    
    def is_admin_method(self, bro):
        print('is admin ', self.org_utils.is_admin(bro, self.org))
        return self.org_utils.is_admin(bro, self.org)
    
    def is_staff_method(self, bro):
        print('is staff ', self.org_utils.is_member(bro, self.org))
        return self.org_utils.is_member(bro, self.org)
    
    def is_reciever_method(self, bro):
        print('is reciever ', self.org_utils.is_service_reciever(bro, self.org))
        return self.org_utils.is_service_reciever(bro, self.org)

    def is_overwatcher_method(self, bro):
        print('is overwatcher ', self.org_utils.is_service_overwatcher(bro, self.org))
        return self.org_utils.is_service_overwatcher(bro, self.org) 


    class Meta:
        model = User
        fields = ['pk',  'first_name', 'last_name', 'tags', 'is_user', 'is_reciever', 'is_overwatcher', 'is_admin', 'is_staff']


class AttachedRecieverSerializer(serializers.Serializer):
     
     attached = serializers.SerializerMethodField('overwatched')
     first_name = serializers.SerializerMethodField('f_name')
     last_name = serializers.SerializerMethodField('l_name')
     pk = serializers.SerializerMethodField('user_pk')
    
    

     def f_name (self, bro):
        return bro.reciever.first_name

     def l_name (self, bro):
        return bro.reciever.last_name

     def user_pk (self, bro):
        return bro.reciever.pk

     def overwatched (self, bro):
        overwatchers = self.Meta.model.objects.get_reciever_overwatchers_org_limit(bro.reciever, bro.organization)
        return AttachedOverwatcherSerializer(overwatchers, many=True).data
        

     class Meta:
        model = ServiceReciever
        fields = 'first_name', 'last_name', 'pk', 'attached'

class AttachedOverwatcherSerializer(serializers.Serializer):

     attached = serializers.SerializerMethodField('overwatching')
     first_name = serializers.SerializerMethodField('f_name')
     last_name = serializers.SerializerMethodField('l_name')
     pk = serializers.SerializerMethodField('user_pk')

     org_utils = _i("organizations.utils")
    
     def f_name (self, bro):
        return bro.reciever.first_name

     def l_name (self, bro):
        return bro.reciever.last_name

     def user_pk (self, bro):
        return bro.reciever.pk

     def overwatching (self, bro):
        recievers = self.Meta.model.objects.get_reciever_reciever_org_limit(bro.reciever, bro.organization)
        return AttachedOverwatcherSerializer(recievers, many=True).data
     
     


     class Meta:
        model = ServiceReciever
        fields = 'first_name', 'last_name', 'pk', 'attached'