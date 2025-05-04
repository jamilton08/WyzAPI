from rest_framework import serializers
from django.contrib.auth.models import User
from .models import OrganizationExtension, OrgSignees
from organizations.models import Organization, OrganizationUser
from importlib import import_module as _i


class CreateOrgExtSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.request= kwargs.pop('request')
        super(CreateOrgExtSerializer,self).__init__(*args, **kwargs)

    name =serializers.CharField(max_length = 150)

    def validate(self, data):
        try:
            Organization.objects.get(name = data['name'])
            raise serializers.ValidationError("each org must have a unique name ")
        except Organization.DoesNotExist:
            return data


    def create(self, validated_data):
        # COMBAK: # TODO:  : Point creation and addrress has been removed therefore, Must check if succesful creation afte creation
        from organizations.utils import create_organization
        name = validated_data.pop('name')
        org = create_organization(user = self.request.user,
                                    name = name,
                                    slug = name,
                                    is_active = True)
        ## TODO: must eventually serialize address to make sure is valid before saving


        instance = OrganizationExtension.objects.create( organization = org,  **validated_data)
        instance.save()
        return instance




    class Meta:
        model = OrganizationExtension
        fields = ('phone', 'parent_org', 'name', 'location',)


class OrgSigneeSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        self.user= kwargs.pop('user')
        super(OrgSigneeSerializer,self).__init__(*args, **kwargs)

    userInfo = serializers.SerializerMethodField('details')

    def details(self, bro):
        serializer = UserSearchSerializer(bro.signee)
        return serializer.data

    def org_create(self):
        cop = self.validated_data
        cop["signee"] = self.user
        instance = self.Meta.model.org_create_accept(**cop)
        return instance

    def org_update(self, instance, approved):
        if self.validated_data['approved']:
            instance.org_accept(approved)
            return bool(1)
        else:
            instance.org_deny_accept()
            return bool(0)

    def user_create(self):
        cop = self.validated_data
        cop["signee"] = self.user
        instance = self.Meta.model.user_create_accept(**cop)
        return instance


    def user_update(self, instance, action):
        if action:
            instance.user_accept()
            return True
        else:
            instance.user_deny_accept()
            return False


    class Meta:
        model = OrgSignees
        fields = '__all__'

class OrgCreateAccept(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(OrgCreateAccept,self).__init__(*args, **kwargs)

    def create(self):
        data = self.validated_data
        data.update({'admin_approve':self.user})

        self.Meta.model.org_create_accept(**data)

    class Meta:
        model = OrgSignees
        fields = ( 'org', 'signee')

class OrgAcceptInvite(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.user  = kwargs.pop("user")
        super(OrgAcceptInvite,self).__init__(*args, **kwargs)

    def org_update(self, instance, accepted):
        if accepted:
            instance.org_accept(self.user)
        else:
            instance.org_deny_accept()
    class Meta:
        model = OrgSignees
        fields = ( 'approved',)

class UserSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username','first_name', 'last_name', 'id')


class AbstractOrgSerializer(serializers.ModelSerializer):
    #sub_orgs = serializers.SerializerMethodField('subs')
    subtitle = serializers.SerializerMethodField('sb')
    text = serializers.SerializerMethodField('txt')

    def subs(self, bro):
        instance = self(OrganizationExtension.objects.get_sub_org(bro), many=True)
        return instance.data

    def sb(self, bro):
        return bro.extension.subtitle

    def txt(self, bro):
        return bro.extension.text

    class Meta:
        model = Organization
        fields = ['name', 'subtitle', 'text', 'pk']
        abstract = True  #


class OrgSerializer(AbstractOrgSerializer):

    permissions = serializers.SerializerMethodField('get_perms')


    
    def get_perms(self, bro):
        from perms.utilities import GeneratePerms as G
        return G.organizations_required_perms(bro)
    

    class Meta(AbstractOrgSerializer.Meta):
        fields = ['name', 'subtitle', 'text', 'pk', 'permissions']

class OrgUserAccessSerializer(AbstractOrgSerializer):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(OrgUserAccessSerializer, self).__init__(*args, **kwargs)

    perm_stack = serializers.SerializerMethodField('level')


    
    def level(self, bro):
        o = _i("orgs.utilities")
        if o.is_in_org(self.user, bro):
            return  o.get_org_user(self.user, bro)
        else:
            return None
    

    class Meta(AbstractOrgSerializer.Meta):
        fields = ['name', 'subtitle', 'text', 'pk', 'perm_stack']


class PermissionRetainerSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self.org_user = kwargs.pop('org_user')
        self.org_user_to_perm = kwargs.pop('user_to_perm')
        super(PermissionRetainerSerializer, self).__init__(*args, **kwargs)

    permissions = serializers.ListField(
        child=serializers.CharField()
    )
    functional_permissions = serializers.ListField(
        child=serializers.IntegerField()
    )

    intention = serializers.CharField()

    def validate(self, data):

        if self.org_user_to_perm is None:
            raise serializers.ValidationError("you must have a organization user to assign permissions to")
        from importlib import import_module as _i
        perm = _i('perms.models')
        perms = perm.PermissionSecondLayerModel.objects.filter(perm_id__in = data['permissions'])
        functions = perm.PermissionTwoPointFiveLayerModel.objects.filter(pk__in = data['functional_permissions'])
        permission_residual = perms.exclude(pk__in = self.org_user.permission_retainer.permmissions.all())
        functional_residual = functions.exclude(pk__in = self.org_user.permission_retainer.functional_permissions.all())
        if  permission_residual.exists():  
            for perm in permission_residual:
                    raise serializers.ValidationError("you must have {} permission in order to assign or remove permission ".format(perm.perm_id))
        if data['intention'] == 'add':
            for func_perm in functions:
                if func_perm.parent_permission() not in perms and func_perm.parent_permission() not in self.org_user_to_perm.permission_retainer.permmissions.all():
                    raise serializers.ValidationError("you need {} permission in order to add this functional permission ".format(func_perm.parent_permission().perm_id))
        if data['intention'] == 'remove':
            #TODO : check if user has is high enough on stack to do such thing 
              pass
            
        if functional_residual.exists():
            for f_perm in functional_residual:
                raise serializers.ValidationError("you mukst have {} permission in order to assign or remove functional permission".format(f_perm.registry.function_detail))
        return {'permissions': perms, 'functional_permissions': functions, "intention": data['intention']}
    
    def add_permissions(self, data):
        
        if data["permissions"].count() > 0:
            self.org_user_to_perm.permission_retainer.add_permissions(data["permissions"])
        if data["functional_permissions"].count() > 0:
            self.org_user_to_perm.permission_retainer.add_functional_permissions(data["functional_permissions"])

    def remove_permissions(self, data):
        
        if data["permissions"].count() > 0:
            self.org_user_to_perm.permission_retainer.remove_permission(data["permissions"])
        if data["functional_permissions"].count() > 0:
            self.org_user_to_perm.permission_retainer.remove_functional_permission(data["functional_permissions"])

    def decision(self, data):
        if data['intention'] == 'add':
            self.add_permissions(data)
        elif data['intention'] == 'remove':
            self.remove_permissions(data)
            
       

    class Meta:
        fields = ['permissions', 'functional_permissions']


class SearchedOrgUserSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop('org')
        super(SearchedOrgUserSerializer, self).__init__(*args, **kwargs)

    perm_stack = serializers.SerializerMethodField('permission_stack')
    is_admin = serializers.SerializerMethodField('admin')
    is_reciever = serializers.SerializerMethodField('reciever')
    is_overwatcher = serializers.SerializerMethodField('overwatcher')
    is_staff = serializers.SerializerMethodField('provider')
    status = serializers.SerializerMethodField('current_status')


    org_utils = _i("orgs.utilities")


    
    def permission_stack(self, bro):
        if self.org_utils.is_in_org(bro, self.org):
            org_user = self.org_utils.get_org_user(bro, self.org)
        return org_user.permission_retainer.stack_level
    
    
    def admin(self, bro):
        return self.org_utils.is_admin(bro, self.org)
    
    def provider(self, bro):
        return self.org_utils.is_member(bro, self.org)
    
    def reciever(self, bro):
        return self.org_utils.is_service_reciever(bro, self.org)

    def overwatcher(self, bro):
        return self.org_utils.is_service_overwatcher(bro, self.org) 
    
    def current_status(self, bro):
        return "signed in"



    class Meta:
        model = User
        fields = ['pk',  'first_name', 'last_name', 'is_reciever', 'is_overwatcher', 'is_admin', 'is_staff', 'perm_stack', 'status']
    


class OrgUserPermSerializer(serializers.ModelSerializer):
    
    permissions = serializers.SerializerMethodField('perms')

    def perms(self, bro):
        from perms.utilities import GeneratePerms as G
        return G.get_org_user_perms(bro.org_user)

    class Meta:
        model = _i('orgs.models').AssignedPermsModel
        fields = ('pk', 'stack_level', 'permissions',)
    

    