from perms.models import *

class TrafficConcealer:
    @classmethod
    def _get_content(cls, instance):
        from django.contrib.contenttypes.models import ContentType
        return ContentType.objects.get_for_model(instance)

    @classmethod
    def create_record(cls, sender, instance, created, **kwargs):
        from perms.utilities import ParentPriorityGenerator
        if created:
            content = cls._get_content(instance)
            is_child = ParentPriorityGenerator.has_parents(instance)
            if is_child:
                slug_name = instance.get_perm_name()
            else:
                slug_name = ParentPriorityGenerator.no_parent_perm_name(instance)

            created_perms = PermissionSecondLayerModel.create_permissions(content, instance.pk, slug_name)
            TwoPointFiveRegistry.attacher(instance, created_perms)

            if not ParentPriorityGenerator.is_top_level(instance):
                owner = instance.get_top_level().owner.organization_user
                for p in created_perms:
                    owner.permission_retainer.permmissions.add(p)
                perm_querys = PermissionSecondLayerModel.objects.filter(id__in = [permission_layer.id for permission_layer in owner.permission_retainer.permmissions.all()])
                two_point_fives = PermissionTwoPointFiveLayerModel.objects.get_all_perm_functions(perm_querys)
                owner.permission_retainer.functional_permissions.add(*two_point_fives)
                

