from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PermissionSecondLayerModel, PermissionTwoPointFiveLayerModel

class PermissionsSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = PermissionSecondLayerModel
        fields = '__all__'

class PermissionFunctionalSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = PermissionTwoPointFiveLayerModel
        fields = '__all__'

class FrontendPermSerializer(serializers.ModelSerializer):
    perm_id = serializers.CharField()
    class Meta:
        model = PermissionSecondLayerModel
        fields = ('perm_id', 'perm_type')

class FrontendFPermSerializer(serializers.ModelSerializer):
    permission = serializers.SerializerMethodField('perm')
    parent_perm = serializers.SerializerMethodField('pp')
    

    def perm(self, bro):
        print(bro, "this is the instance")
        return bro.registry.function_id

    def pp(self, bro):
        instance = FrontendPermSerializer(bro.perm)
        print(instance.data)
        return instance.data

    

    class Meta:
        model = PermissionTwoPointFiveLayerModel
        fields = ['permission', 'parent_perm', 'pk']

