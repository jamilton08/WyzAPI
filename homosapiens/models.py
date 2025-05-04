from django.db import models
from django.contrib.auth.models import User
from organizations.models import Organization, OrganizationUser
from django.contrib.contenttypes.models import ContentType
from orgs.models import OrgSignees
from django.utils.translation import gettext_lazy as _
from .managers import SigneeRecieverManager, OverwatchSigneeManager, ServiceRecieverManager
from django.db.models import Q
from .abstract_models import AbstractSignee
from services.models import ServicesContainer
from actions.response import ActionResponse


class ServiceReciever(models.Model):
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE, related_name='service_receivers')
    reciever = models.ForeignKey(User,on_delete= models.CASCADE, related_name='recieving_service')
    overwatcher = models.ForeignKey(User, on_delete = models.CASCADE, related_name='overwatches', blank = True, null= True)

    objects = ServiceRecieverManager()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "reciever", "overwatcher"],
                                    name='recieve unique services'),
            models.UniqueConstraint(fields=["organization", "reciever"], name='recieve unique service when overwatch is  null',
                                    condition=Q(overwatcher__isnull=True))
    ]

#this will be to create a one to one relation for each reciever and many to many with parents
class ServiceRecieverRefactored(models.Model):
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE, related_name='refactored_receivers')
    reciever = models.ForeignKey(User,on_delete= models.CASCADE, related_name='sr')
    overwathers = models.ManyToManyField(ServiceReciever ,  related_name='compile', blank = True, null= True)

    @classmethod
    def add_to(cls, **kwargs):
        overwatcher = None
        if "overwathers" in kwargs:
            overwatcher = kwargs.pop("overwathers")
        if cls.objects.filter(**kwargs):
            cls.objects.filter(**kwargs).get().overwathers.add(overwatcher)
        else:
            instance = cls.objects.create(**kwargs)
            instance.save()
            kwargs["overwathers"] = overwatcher
        sr = ServiceReciever.objects.create(**kwargs)
        sr.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "reciever"],
                                    name='make sure that each is unique'),
    ]


class RecieverRestrictions(models.Model):

    reciever_instance= models.ForeignKey(ServiceReciever,on_delete=models.CASCADE, related_name='reciever_restrictions')
    restricted = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'restrictions')
    service = models.ManyToManyField(ContentType, related_name='restricts')


class RecieverSignee(ActionResponse, AbstractSignee, models.Model):

    objects  = SigneeRecieverManager()

    def _accept(self):
        r = ServiceReciever.objects.create(organization = self.organization, reciever= self.signee)
        r.save()
    ## NOTE: this helps notification string to be put together
    @classmethod
    def notification_string(cls):
        return "reciever signee"



    class Meta:
        default_related_name = "reciever_signee"
        db_table = "reciever_signee"

class OverwatchSignee(ActionResponse,AbstractSignee, models.Model):
    reciever = models.ForeignKey(ServiceReciever, on_delete = models.CASCADE, related_name ='overwatching_instance')
    objects = OverwatchSigneeManager()

    def _accept(self):
        if self.reciever.overwatcher is None:
            s = self.reciever.reciever
            s.overwatcher = self.signee
        else:
            s = ServiceReciever.objects.create(organization = self.organization,
                                                reciever = self.reciever.reciever,
                                                    overwatcher = self.signee)
        s.save()

    # NOTE: this helps notification string to be put together
    @classmethod
    def notification_string(cls):
        return "overwatcher signee"

    class Meta:
        default_related_name = "overwatcher_signee"
        db_table = "overwatcher_signee"

class RecieverServiceProvide(models.Model):
    is_reciever = models.BooleanField()
    reciever_obj = models.ForeignKey(ServiceReciever, on_delete=models.CASCADE, related_name="service_retainer")
    providing_service = models.ManyToManyField(ServicesContainer, related_name="%(class)s_providing", blank = True, null = True)


    @classmethod
    def add_reciever(cls, user, organization, service, reciever = True):
        query = {'reciever' if reciever else 'overwatcher': user, 'organization' :organization}
        obj = ServiceReciever.objects.get(**query)
        s = None
        if not hasattr(obj, 'service_retainer'):
            s = cls.objects.create(reciever_obj = obj, is_reciever = reciever)
        else:
            if not obj.service_retainer.filter(is_reciever = reciever).count() == 1:
                s = cls.objects.create(reciever_obj = obj, is_reciever = reciever)

        if s is not None:
            s.save()

        obj.service_retainer.get(is_reciever = reciever).providing_service.add(service)


    class Meta:
        db_table = "reciever_service_retainer"
        constraints = [
            models.UniqueConstraint(
                fields=["is_reciever", "reciever_obj"],
                name='provide unique services for reciever'
            )
        ]

class ProviderServiceProvide(models.Model):
    provider_obj = models.OneToOneField(OrganizationUser, on_delete= models.CASCADE, related_name="service_retainer")
    providing_service = models.ManyToManyField(ServicesContainer, related_name="%(class)s_providing", blank = True, null = True)

    @classmethod
    def add_org_user(cls, org_user, service):
        org_user.service_retainer.providing_service.add(service)
    class Meta:
        db_table = "org_user_service_retainer"
