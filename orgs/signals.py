from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from organizations.models import Organization, OrganizationUser, OrganizationOwner
from .models import AssignedPermsModel
from perms.models import *


@receiver(post_save, sender=OrganizationUser)
def create_user_extension(sender, instance, created, **kwargs):
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    from perms.models import PermissionSecondLayerModel
    if instance.organization.organization_users.count() == 1:
         perm_stack = 0
    else:
        perm_stack = AssignedPermsModel\
            .objects\
            .filter\
            (pk__in = instance.organization.organization_users.values_list('permission_retainer', flat = True))\
            .order_by('stack_level')\
            .last()\
            .stack_level + 1
    if created:
        perm  = AssignedPermsModel.objects.create(org_user = instance, stack_level = perm_stack)
        perm.save()



@receiver(post_save, sender=OrganizationOwner)
def create_owner(sender, instance, created, **kwargs):
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q


    if created:
            org = instance.organization
            content = ContentType.objects.get_for_model(org)
            c1 = Q(content_type = content)
            c2 = Q(object_id = org.pk)
            owner_permissions = PermissionSecondLayerModel.objects.filter(c1 & c2)
            perm_querys = PermissionSecondLayerModel.objects.filter(id__in = owner_permissions)
            for p in owner_permissions:
                instance.organization_user.permission_retainer.permmissions.add(p)
            two_point_fives = PermissionTwoPointFiveLayerModel.objects.get_all_perm_functions(perm_querys)
           
            for fp in two_point_fives:
                instance.organization_user.permission_retainer.functional_permissions.add(fp)
            instance.organization_user.permission_retainer.functional_permissions.add(*two_point_fives)
