from django.db import models
from organizations.models import Organization
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from perms.utilities import FieldGen, ParentPriorityGenerator

# Create your models here.
class ServiceClass(models.Model, ParentPriorityGenerator):
    name = models.CharField(max_length = 50)
    description = models.CharField(max_length = 200)
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_provided_services')
    priority_parent = FieldGen("organization")

    def add_to_provide_service(self):
        pass
    @classmethod
    def is_service(cls, instance):
        return (instance.__class__, cls )

    def _get_service_container(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return ServicesContainer.objects.filter(content_type = content_type, object_id = self.pk).first()

    def _reciever_adding(self, user, recieving):
        from homosapiens.models import RecieverServiceProvide
        RecieverServiceProvide.add_reciever(user, self.organization, self._get_service_container(), recieving)
    #for all these we msut verify that they are part of the organization title therfore must be verified in serializer before adding
    def add_reciever(self, user):

        self._reciever_adding(user, True)

    def add_overwatcher(self, user):
        self._reciever_adding(user, False)

    def add_org_user(self, user):
        from homosapiens.models import ProviderServiceProvide
        from orgs.utilities import get_org_user
        ProviderServiceProvide.add_org_user(get_org_user(user, self.organization),self._get_service_container())


    def save(self, **kwargs):
        super(ServiceClass, self).save(**kwargs)
        s_object = ServicesContainer.objects.create(\


        service_id = f'{self.organization.name}_{self.name}',\
        content_type = ContentType.objects.get_for_model(self.__class__),\
        object_id = self.pk\
        )
        s_object.save()
        return object

    class Meta:
        abstract = True


class Enviromental(ServiceClass, models.Model):


    def details(self, additional):
        return f'{additional} that will provide service on an enviromental level where you usually handling an independent enviroment'

class CoEnv(ServiceClass, models.Model):
    def details(self, additional):
        return f'{additional} that will provide service on an enviromental level where you usually handling a small enviroment which relies on a bigger enviroment'

class Floater(ServiceClass, models.Model):
    def details(self, additional):
        return f'{additional} that will provide service on an enviromental level where you usually handling an small independent enviroment for a service outside of general org services'

class Controller(ServiceClass, models.Model):
    def details(self, additional):
        return f'{additional} that will provide service off an enviroment and will usually have organization management services'


class ServicesContainer(models.Model):
        from .managers import ServicesContainerManager
        service_id = models.SlugField(blank = True, null = True, max_length = 250)#userful for exteernal or frontend identification of permission
        content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='services')
        object_id = models.IntegerField()
        content_object = GenericForeignKey('content_type', 'object_id')

        objects = ServicesContainerManager()
