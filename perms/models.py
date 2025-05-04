from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .managers import PermsManager, PermsFunctionManager
from django.db.models import Q
from organizations.models import Organization as O

#TODO: add a permission type that is a combination of all the other permissions

class PermissionSecondLayerModel(models.Model):
    class PermissionType(models.TextChoices):
            ADD = "A", _("add")
            DELETE = "D", _("delete")
            EDIT = "E", _("edit")
            READ = "R", _("read")
    perm_id = models.SlugField(blank = True, null = True, max_length = 250, unique = True)#userful for exteernal or frontend identification of permission
    content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='permissions')
    object_id = models.IntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    perm_type = models.CharField(
            max_length=2,
            choices=PermissionType.choices,
            default=PermissionType.READ,
        )

    objects = PermsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["content_type", "object_id", "perm_type"],
                                    name='unique permission'),
    ]

    @classmethod
    def create_permissions(cls, content, instance_pk, slug_name):
        creation_args = dict()
        creation_args["content_type"] = content
        creation_args["object_id"] = instance_pk
        instances_list = []

        a = cls.objects.create(perm_type = cls.PermissionType.ADD, perm_id =f'{slug_name}_{cls.PermissionType.ADD}',  **creation_args )
        d = cls.objects.create(perm_type = cls.PermissionType.DELETE, perm_id =f'{slug_name}_{cls.PermissionType.DELETE}', **creation_args )
        e = cls.objects.create(perm_type = cls.PermissionType.EDIT, perm_id =f'{slug_name}_{cls.PermissionType.EDIT}', **creation_args )
        r = cls.objects.create(perm_type = cls.PermissionType.READ, perm_id =f'{slug_name}_{cls.PermissionType.READ}', **creation_args )

        a.save()
        d.save()
        e.save()
        r.save()

        instances_list.extend([a, d, e, r])

        return instances_list
    
    def get_org(self):
        from .utilities import ParentPriorityGenerator as P
        instance = self.content_type
        return instance if P.is_top_level(instance) else instance.get_top_level()
    
    

    @classmethod
    def has_perm(cls, user, content, object, type):
          from .utilities import ParentPriorityGenerator as P
          cont = ContentType.objects.get_for_model(content)
          c1 = Q(content_type = cont)
          c2 = Q(object_id = object)
          c3 = Q(perm_type = type)
          c = cls.objects.filter(c1 & c2 & c3).first()


          if c is None:
              return False, None
          else:
              instance = c.content_object
          if P.is_top_level(instance):
              org = instance
          else:
              org = instance.get_top_level()
          if hasattr(user, 'organizations_organizationuser'):
              org_user_q =  user.organizations_organizationuser.filter(organization__in = O.objects.filter(pk = org.pk))
          else:
              return False, None
          if org_user_q.count() != 1:
             return False, None

          org_user = org_user_q.first()


          return bool(c in org_user.permission_retainer.permmissions.all()), org
    
    @classmethod
    def get_permission(cls, content, object, type):
        cont = ContentType.objects.get_for_model(content)
        c1 = Q(content_type = cont)
        c2 = Q(object_id = object)
        c3 = Q(perm_type = type)
        c = cls.objects.filter(c1 & c2 & c3).first()
        return c
    
    @classmethod
    def belong_to_org(cls, org, permissions):
        num_of_perms = permissions.count()
        count = 0

        for p in permissions:
            if p.get_org() == org:
                count += 1
        return count == num_of_perms

class ParentPermission(object):
    def __init__(self, relation_field, parent,  **kwargs):
        self.relation_field = relation_field
        self.related_to = related_to
        self.kwargs = kwargs

    def __new__(cls, *args, **kwargs):
        return kwargs.pop('relation_field')(kwargs.pop('parent'), **kwargs)

class TwoPointFiveRegistry(models.Model):
    class PermissionType(models.TextChoices):
            ADD = "A", _("add")
            DELETE = "D", _("delete")
            EDIT = "E", _("edit")
            READ = "R", _("read")
    model  = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='perm_registries')
    function_detail = models.CharField(max_length = 250)
    function_id = models.SlugField(blank = True, null = True, max_length = 250, unique = True)#userful for exteernal or frontend identification of permission
    perm_type = models.CharField(
            max_length=2,
            choices=PermissionType.choices,
            default=PermissionType.READ,
        )
    #objects = PermsManager()

    #NOTE: when a permission second layer model is created this will attach a function permission
    @classmethod
    def attacher(cls, content, permission_layer):
        contents = ContentType.objects.get_for_model(content)
        functions  = cls.objects.filter(model = contents)
        if functions.count() > 0:
            print("are we in number 1")
            for f in functions:
                print("are we in number 2")
                print(f, permission_layer)
                perm = PermissionSecondLayerModel.objects\
                    .filter(id__in = [permission_layer.id for permission_layer in permission_layer])\
                    .filter(perm_type = f.perm_type)\
                    .first()  
                print("are we in number 2", f.perm_type, perm.perm_type)
                p = PermissionTwoPointFiveLayerModel.objects.create(registry = f, perm = perm)
                p.save




class PermissionTwoPointFiveLayerModel(models.Model):
    registry = models.ForeignKey(TwoPointFiveRegistry, on_delete = models.CASCADE, related_name = 'layer_model')
    perm = models.ForeignKey(PermissionSecondLayerModel, on_delete = models.CASCADE, related_name = 'two_point_five')

    objects = PermsFunctionManager()
        
    def parent_permission(self):
        return self.perm
   
    def get_org(self):
         return self.parent_permission().get_org()
    
    @classmethod
    def verify_function(cls, permission, registry, user, organization):
        from orgs.utilities import get_org_user
        org_user = get_org_user(user, organization)
        return org_user\
        .permission_retainer\
        .functional_permissions\
        .filter(registry = TwoPointFiveRegistry.objects.filter(function_id = registry).get(), perm = permission).exists()
