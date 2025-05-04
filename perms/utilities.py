from .models import PermissionSecondLayerModel as p, PermissionTwoPointFiveLayerModel as p25, PermissionTwoPointFiveLayerModel as p25r

class FieldGen(str):
     def __new__(cls, val):
             obj = str.__new__(cls, val)
             return obj
     def __init__(self, val):
             self.val = val

class ParentPriorityGenerator(object):
    priority_parent = None

    def _get_parent_instance(self):
        if self.priority_parent is not None:
            return getattr(self, self.priority_parent)
        else:
             return None

    def _get_parent_string(self):
        class_name = self._get_parent_instance().__class__.__name__
        instance_name = getattr(self._get_parent_instance(), "name")
        return f'{class_name}_{instance_name}'

    def _sentinel(self):
        return bool(not hasattr(self._get_parent_instance(), "priority_parent" ))

    def _get_perm_parent_name(self):
        if self._sentinel():
            return self._get_parent_string()
        else:
            return f'{self._get_parent_instance()._get_perm_parent_name()}-{self._get_parent_string()}'


    def get_perm_name(self):
        return f'{self._get_perm_parent_name()}-{self.__class__.__name__}_{self.name}'

    def get_top_level(self):
        if self._sentinel():
            return self._get_parent_instance()
        else:
            return self._get_parent_instance().get_top_level()

    @classmethod
    def no_parent_perm_name(cls, instance):
        return f'{instance.__class__.__name__}_{instance.name}'


    @classmethod
    def has_parents(cls, instance):
        return bool(cls in instance.__class__.__bases__)

    @classmethod
    def is_top_level(cls, instance):
        return not hasattr(instance, "priority_parent")



class StructurizePerms():
    def __init__(self, user):
        self.user = user
        self.perms = list()

    def __get_all_perms(self):
        return p.objects.get_user_with_perms(self.user)

    def __remove_duplicates(self, perms_query):
        from django.db.models import Count, Max
        unique_fields = ["content_type", "object_id"]
        return perms_query\
            .values(*unique_fields)\
            .annotate(max_id = Max('id'), count_id = Count('id'))\
            .filter(count_id__gt =1)

    def __get_serializer_obj(self, instance):
        from inspect import getmembers, isfunction
        from global_utilities import serializer_storage
        serializers =  getmembers(serializer_storage)
        for i in serializers:
            if instance.__class__.__name__.lower() ==  i[0]:
                return i[1](instance)
        return None


    def __organize_perms_query(self, unique_query):
        from collections import OrderedDict as od
        default_dict = {"A":0, "E":0, "D":0, "R":0}
        for perm in unique_query:
             d = default_dict.copy()
             obj = None
             for key, value in d.items():
                 f = self.__get_all_perms()\
                    .filter(content_type = perm['content_type'],\
                        object_id = perm['object_id'],\
                        perm_type = key)

                 if f.count() > 0:
                     if obj is None:
                         obj = f[0].content_object
                     d[key] = 1
             self.perms.append(od({"permType" : obj.__class__.__name__.lower(),  "permObj" : od(self.__get_serializer_obj(obj)), "permDict" : d }))


    def structure(self):

        unique_query = self.__remove_duplicates(self.__get_all_perms())
        self.__organize_perms_query(unique_query)
        print(self.perms)

class GeneratePerms():

    @classmethod
    def _perm_generator(cls, l, perms, f_perms):
        for perm in perms:
            for fp in f_perms.filter(perm = perm):
                l.append(perm.perm_id + fp.registry.function_id + str(fp.pk)) 
        return l

    @classmethod
    def get_user_perms(cls, user):
        empt_list = list()
        perms =  p.objects.get_user_with_perms(user)
        f_perms = p25.objects.get_all_user_perm_functions(user)

        return cls._perm_generator( empt_list, perms, f_perms)
    
    @classmethod
    def get_org_user_perms(cls, org_user):
        empt_list = list()
        perms =  org_user.permission_retainer.permmissions.all()
        f_perms = org_user.permission_retainer.functional_permissions.all()

        return cls._perm_generator( empt_list, perms, f_perms)
    
    @classmethod
    def organizations_required_perms(cls, organization):
        p_dict = dict()
        for r in organization.owner.organization_user.permission_retainer.functional_permissions.all():
            p_dict[r.registry.function_id] = r.perm.perm_id + r.registry.function_id + str(r.pk)
        return p_dict

def get_permission_transactions(assigner, asignee):
    assigner_perms = assigner.permission_retainer.permmissions.all()
    asignee_perms = asignee.permission_retainer.permmissions.all()
    assigning_perms = assigner_perms.exclude(pk__in = asignee_perms)
    asigneeing_perms = asignee_perms.filter(pk__in = assigner_perms)

    return assigning_perms, asigneeing_perms

def get_functional_transactions(assigner, asignee):
    assigner_perms = assigner.permission_retainer.functional_permissions.all()
    asignee_perms = asignee.permission_retainer.functional_permissions.all()
    assigning_perms = assigner_perms.exclude(pk__in = asignee_perms)
    asigneeing_perms = asignee_perms.filter(pk__in = assigner_perms)
    return assigning_perms, asigneeing_perms