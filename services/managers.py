from django.db import models
from django.contrib.contenttypes.models import ContentType


class ServicesContainerQuerySet(models.query.QuerySet):
    # users invited by org should an admin approved already, and the signee of who go invited, with org listed
    def org_services(self, organization):
        from .models import Enviromental, CoEnv, Floater, Controller

        all_enviroment = self.filter\
        (content_type = ContentType.objects.get_for_model(Enviromental),\
        object_id__in = Enviromental.objects.filter(organization = organization).values_list('pk', flat=True))
        all_coenv = self.filter\
        (content_type = ContentType.objects.get_for_model(CoEnv),\
        object_id__in = Enviromental.objects.filter(organization = organization).values_list('pk', flat=True))
        all_floater = self.filter\
        (content_type = ContentType.objects.get_for_model(Floater),\
        object_id__in = Enviromental.objects.filter(organization = organization).values_list('pk', flat=True))
        all_controller = self.filter\
        (content_type = ContentType.objects.get_for_model(Controller),\
        object_id__in = Enviromental.objects.filter(organization = organization).values_list('pk', flat=True))
        return  all_enviroment | all_coenv | all_floater | all_controller

    def get_service_reciever(self):
        recievers_service_retainer = self.filter(recieverserviceprovide_providing__in = RecieverServiceProvide.objects.filter(is_reciever = False))
        recievers = ServiceReciever.objects.filter(pk__in = recievers_service_retainer.values_list('reciever_obj', flat = True))
        return User.objects.filter(pk__in = recievers.values_list('overwatcher', flat = True))

    def get_service_overwatchers(self):
        recievers_service_retainer = self.filter(recieverserviceprovide_providing__in = RecieverServiceProvide.objects.filter(is_reciever = True))
        recievers = ServiceReciever.objects.filter(pk__in = recievers_service_retainer.values_list('reciever_obj', flat = True))
        return User.objects.filter(pk__in = recievers.values_list('overwatcher', flat = True))

    def get_service_org_users(self):
        from organizations.models import OrganizationUser
        org_user_service_retainer = self.filter(providerserviceprovide_providing__in = ProviderServiceProvide.objects.all())
        org_user = OrganizationUser.objects.filter(pk__in = org_user_service_retainer.values_list('providing_obj', flat=True))
        return User.objects.filter(pk__in = org_users.values_list('user', flat = True))

    def get_all_service_providers(self):
        from itertools import chain
        return  list(chain(self.get_service_reciever(),\
                        self.get_service_overwatchers(),\
                        self.get_service_org_users()))

class ServicesContainerManager(models.Manager):
    def get_queryset(self):
        return ServicesContainerQuerySet(self.model)

    def org_services(self,user):
        return self.get_queryset().org_services(user)
