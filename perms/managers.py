from django.db import models
from django.utils import timezone
import pytz
from organizations.models import OrganizationUser
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType




class PermsQuerySet(models.QuerySet):
    def get_all_model_perms(self, model):
        id = ContentType.objects.get_for_model(model).id
        return self.filter(content_type = id)

    def get_user_with_perms(self, user):
        from orgs.models import AssignedPermsModel
        org_users = user.organizations_organizationuser.all()
        assigned_perms = AssignedPermsModel.objects.filter(org_user__in = org_users)
        return self.filter(allowed_users__in = assigned_perms)

    def get_perm_users(self, perm):
        from orgs.models import AssignedPermsModel
        from organizations.models import OrganizationUser
        assigned_perms = AssignedPermsModel.objects.filter(permmissions = perm)
        org_users = OrganizationUser.objects.filter(permission_retainer__in = assigned_perms)
        return User.objects.filter(organizations_organizationuser__in = org_users)
    


class PermsFunctionQuerySet(models.QuerySet):
    def get_all_perm_functions(self, permissions):
        return self.filter(perm__in = permissions)
    
    def get_all_perm_function_users(self, permissions):
        from orgs.models import AssignedPermsModel
        from organizations.models import OrganizationUser
        assigned_perms = AssignedPermsModel.objects.filter(permmissions__in = permissions)
        org_users = OrganizationUser.objects.filter(permission_retainer__in = assigned_perms)
        return User.objects.filter(organizations_organizationuser__in = org_users)
    
    def get_all_perm_function_orgs(self, permissions):
        from orgs.models import AssignedPermsModel
        from organizations.models import OrganizationUser
        assigned_perms = AssignedPermsModel.objects.filter(permmissions = permissions)
        org_users = OrganizationUser.objects.filter(permission_retainer__in = assigned_perms)
        return org_users.values_list('organization', flat = True)
    
    def get_all_user_perm_functions(self, user):
        from orgs.models import AssignedPermsModel
        org_users = user.organizations_organizationuser.all()
        assigned_perms = AssignedPermsModel.objects.filter(org_user__in = org_users)
        return self.filter(pk__in = assigned_perms.values_list('functional_permissions', flat = True))
    
    def get_all_org_user_perm_functions(self, user, org):
        from orgs.utilities import get_org_user
        org_user = get_org_user(user, org)
        assign = org_user.permission_retainer.functional_permissions.all()
        return self.filter(perm = assigned_perms)

    
    def get_org_user_functions_within_perm(self, org_user, perm):
        functional_perms = org_user.permission_retainer.functional_permissions.all()
        perms_functions = self.get_all_perm_functions(perm)
        return functional_perms.filter(perm__in = perms_functions)
    
    def get_missing_functions(self, org_user, perm):
        functional_perms = org_user.permission_retainer.functional_permissions.all()
        perms_functions = self.get_all_perm_functions(perm)
        return perms_functions.exclude(perm__in = functional_perms)
    
    def permissions_functions(self, permissions_queryset):
        return self.filter(perm__in = permissions_queryset)
    

class PermsFunctionManager(models.Manager):
    def get_queryset(self):
        return PermsFunctionQuerySet(self.model, using=self._db)
    def get_all_perm_functions(self, permissions):
        return self.get_queryset().get_all_perm_functions(permissions)
    def get_all_perm_function_users(self, permissions):
        return self.get_queryset().get_all_perm_function_users(permissions)
    def get_all_perm_function_orgs(self, permissions):
        return self.get_queryset().get_all_perm_function_orgs(permissions)
    def get_all_user_perm_functions(self, user):
        return self.get_queryset().get_all_user_perm_functions(user)
    def get_all_org_user_perm_functions(self, user, org):
        return self.get_queryset().get_all_org_user_perm_functions(user, org)
    def get_org_user_functions_within_perm(self, org_user, perm):
        return self.get_queryset().get_org_user_functions_within_perm(org_user, perm)
    def get_missing_functions(self, org_user, perm):
        return self.get_queryset().get_missing_functions(org_user, perm)
    def permissions_functions(self, permissions_queryset):
        return self.get_queryset().permissions_functions(permissions_queryset)


class PermsManager(models.Manager):
    def get_queryset(self):
        return PermsQuerySet(self.model, using=self._db)

    def get_all_model_perms(self, model):
        return self.get_queryset().get_all_model_perms(model)

    def get_user_with_perms(self, user):
        return self.get_queryset().get_user_with_perms(user)

    def get_perm_users(self, perm):
        return self.get_queryset().get_perm_users(perm)
