from importlib import import_module as im
from django.contrib.contenttypes.models import ContentType
from .models import PermissionSecondLayerModel, PermissionTwoPointFiveLayerModel, TwoPointFiveRegistry
from organizations.models import OrganizationUser

# NOTE: This model will hold the names of every single options through the app in will be in charge of linking them appropriate
# XXX: to their options
perms_name_model_matcher = list()

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "search users for a respective organization",\
                                "function_id" : "search_users",\
                                "perm_type" : "R"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allowed to view organization personal",\
                                "function_id" : "view_org_users",\
                                "perm_type" : "R"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allowed to send invites for service reciever to join",\
                                "function_id" : "invite_reciever",\
                                "perm_type" : "A"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allowed to send invites for service providers to join",\
                                "function_id" : "invite_provider",\
                                "perm_type" : "A"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allowed to remove service recievers from organization as long as they're below you on perm stack",\
                                "function_id" : "delete_reciever",\
                                "perm_type" : "D"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allowed to remove service providers from organization as long as they're below you on perm stack",\
                                "function_id" : "delete_provider",\
                                "perm_type" : "D"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "accept a service reciever is request to join organization ",\
                                "function_id" : "approve_reciever_request",\
                                "perm_type" : "E"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "accept a provider is request to join an organization",\
                                "function_id" : "approve_provider_request",\
                                "perm_type" : "E"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allows you to manage recievers after they have joineed",\
                                "function_id" : "manage_reciever",\
                                "perm_type" : "E"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allow you to manage users org providers after they have joined",\
                                "function_id" : "manage_providers",\
                                "perm_type" : "E"})

perms_name_model_matcher.append({"model" : ContentType.objects.get_for_model(im("organizations.models").Organization),\
                                "function_detail" : "allow to set schedule of a user within organization, can't change wether it conflicts with other from diffirent orgre ",\
                                "function_id" : "set_schedules",\
                                "perm_type" : "E"})




def update_registry_database():
    for perm in perms_name_model_matcher:
        if not TwoPointFiveRegistry.objects.filter(function_id = perm['function_id']).exists():
            perm_instance = TwoPointFiveRegistry.objects.create(**perm)
            perm_instance.save()

def update_second_layer():
    for registry in TwoPointFiveRegistry.objects.all():
        for perm in PermissionSecondLayerModel.objects.filter(content_type = registry.model, perm_type = registry.perm_type):
            if not PermissionTwoPointFiveLayerModel.objects.filter(registry = registry, perm = perm).exists():
                PermissionTwoPointFiveLayerModel.objects.create(registry = registry, perm = perm).save()
          


def update_owners():
     for owner in OrganizationUser.objects.filter(is_admin = True): 
        for perm in owner.permission_retainer.permmissions.all():
            funcs = PermissionTwoPointFiveLayerModel.objects.filter(perm = perm)
            owner.permission_retainer.functional_permissions.add(*funcs)
     
                









