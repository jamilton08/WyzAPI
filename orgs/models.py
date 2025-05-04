from django.db import models as r_models
from django.contrib.gis.db import models
from organizations.models import Organization, OrganizationUser
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from perms.models import ParentPermission, PermissionSecondLayerModel, PermissionTwoPointFiveLayerModel
from .managers import OrgSigneesManager
from perms.utilities import FieldGen, ParentPriorityGenerator
from actions.response import ActionResponse



class OrganizationExtension(ParentPriorityGenerator, models.Model):
    organization = models.OneToOneField(Organization, on_delete = models.CASCADE, related_name ='extension')
    parent_org = models.ForeignKey(Organization, on_delete = models.CASCADE, related_name ='sub_orgs', blank = True, null = True)
    city = models.CharField(max_length=50, blank = True, null = True)
    subtitle = models.CharField(max_length=100, blank = True, null = True)
    text = models.CharField(max_length=300, blank = True, null = True)
    location = models.PointField(blank = True, null = True)
    #icon = models.FileField()
    #background = models.FileField()
    phone = PhoneNumberField(default='+1111111111')
    priority_parent = FieldGen("organization")





class DummyPerm(ParentPriorityGenerator, models.Model):
    name = models.CharField(max_length=100)
    organization = ParentPermission(relation_field = models.OneToOneField, parent = Organization, on_delete = models.CASCADE, related_name ='dum')
    priority_parent = FieldGen("organization")


class DummyPerm2(ParentPriorityGenerator, models.Model):
    name = models.CharField(max_length=100)
    permss = ParentPermission(relation_field = models.OneToOneField, parent = DummyPerm, on_delete = models.CASCADE, related_name ='dum2')
    priority_parent = FieldGen("permss")


class OrgSignees(ActionResponse,  models.Model):
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE)
    signee = models.ForeignKey(User, on_delete = models.CASCADE, related_name ='sign_ups_to', null=True)
    admin_approve = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'org_approvals', null = True)
    approved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add = True)
    message = models.CharField(blank = True, null = True)

    objects = OrgSigneesManager()

    def _accept(self):
        org_user = OrganizationUser.objects.create(organization = self.organization, user = self.signee)
        org_user.save()

    @classmethod
    def _create(self, **kwargs):
        inv = self.objects.create(**kwargs)
        return inv

    @classmethod
    def org_create_accept(self,**creates):
        inv = self._create(**creates)
        inv.save()
        return inv

    def org_deny_accept(self):
        self.save()

    @classmethod
    def user_create_accept(self, **creates):
        inv = self._create(**creates)
        inv.save()
        return inv

    def user_deny_accept(self):
        self.save()


    def org_accept(self,acceptor):
        self._accept()
        self.approved = True
        self.admin_approve = acceptor
        self.save()

    def user_accept(self):
        self._accept()
        self.approved = True
        self.save()

    def handle_actions_queries(self):
        if self.admin_approve is not None:
            User.objects.filter(pk = signee)
        else:
            from perms.models import PermissionSecondLayerModel as p
            from django.contrib.contenttypes.models import ContentType as c
            perm = p.objects.get(content_type = c.objects.get_for_model(Organization), object_id = self.organization.pk, perm_type = "A")#put the rest of the needed params to finish object perm
            return p.objects.get_perm_users(perm)


    def handle_actions_response(self, user):
        if self.admin_approve:
            return Organization, user
        else:
            return User, self.signee

    @classmethod
    def user_profile_active_request(self, user, org):
        if self.objects.filter(org = org, signee= user, approved = False).exists():
            if self.objects.filter(org = org, signee = user, admin_approve__isnull = True ).exists():
                return 'sentbyuser'
            else:
                return 'sentbyadmin'


    @classmethod
    def notification_string(cls):
        return "org signee"
    class Meta:
        default_related_name = "signees"
        db_table = "signees"


class AssignedPermsModel(models.Model):
    org_user = models.OneToOneField(OrganizationUser, on_delete = models.CASCADE, related_name ='permission_retainer')
    permmissions = models.ManyToManyField(PermissionSecondLayerModel, related_name ='allowed_users')
    functional_permissions = models.ManyToManyField(PermissionTwoPointFiveLayerModel, related_name ='functional_users')
    stack_level = models.IntegerField()


    def add_permission(self, permission):
        succeeded = 0
        if permission.get_org() == self.org_user.organization:
            self.permissions.add(permission)

            return bool(succeeded + 1)
        else:
            return bool(succeeded)
        
    def add_permissions(self, permissions_queryset):
        self.permmissions.add(*permissions_queryset)
        
    def add_functional_permission(self, functional_permission):
        
        succeeded = 0
        if functional_permission.get_org() == self.org_user.organization and functional_permission in self.permissions.all():
            self.functional_permissions.add(functional_permission)
            return bool(succeeded + 1)
        else:
            return bool(succeeded)
        
    def add_functional_permissions(self, functional_permission_queryset):
        self.functional_permissions.add(*functional_permission_queryset)
        
   
        
    def remove_permission(self, permissions_queryset):
        self\
        .functional_permissions\
        .remove(*self.functional_permissions.permissions_functions(permissions_queryset))
        self.permmissions.remove(*permissions_queryset)

    def remove_functional_permission(self, functional_queryset):
        self.functional_permissions.remove(*functional_queryset)

    def add_full_permission(self, permission):
        if permission.get_org() == self.org_user.organization:
            self.permmissions.add(permission)
            self.functional_permissions.add(permission.two_point_five)
            return True
        else:
            return False
        
    def get_permissions(self):
        return self.permissions.all()
    
    def get_functional_permissions(self):
        return self.functional_permissions.all()
    
    @classmethod
    def notification_string(cls):
        return "permissions"
    
