from django.contrib.auth.models import User
from organizations.models import Organization
from orgs.utilities import get_org_user
from homosapiens.models import ServiceReciever
from services.models import ServicesContainer
import inspect

class CollectUserInvolvement(object):

# NOTE: This is a class based on collecting how is a user involved within a specic organiztion
    def __init__(self, user, organization):
        assert isinstance(user, User), "this must be a user your giving"
        assert isinstance(organization, Organization), "this must be a user your giving"
        self.user = user
        self.organization = organization
        self.org_user =  get_org_user(self.user, self.organization)

    known_handle_models = [ServiceReciever, ServicesContainer]
    structure = ["name", "details", "type", "content", "obj"]
    struct_type_src = {"sr": known_handle_models[0],\
                       "ow": known_handle_models[0],\
                       "sp": known_handle_models[1],\
                       "rp": known_handle_models[1],\
                       "op": known_handle_models[1]
                        }

    struct_f = list()

    def _get_recievers_as_recievers_sr(self):
        return self.user.recieving_service.filter(organization = self.organization)

    def _get_overwatchers_as_overwatchers_ow(self):
        return self.user.overwatches.filter(organization = self.organization)

    def _get_services_providing_sp(self):
        if self.org_user:
            if hasattr(self.org_user, "providing_service"):
                return self.org_user.providing_service.all()
        return list()

    def _get_recievers_as_services_rp(self):
        if self._get_recievers_as_recievers_sr().count() != 0:
            s = self._get_recievers_as_recievers_sr().first().service_retainer.filter(is_reciever = True)
            return self.struct_type_src["rp"].objects.filter(pk__in = s.values_list('providing_service', flat = True))
        return list()

    def _get_overwatchers_as_serviceop(self):

        if self._get_overwatchers_as_overwatchers_ow().count() != 0:

            s = self._get_overwatchers_as_overwatchers_ow().first().service_retainer.filter(is_reciever = False)
            return self.struct_type_src["rp"].objects.filter(pk__in = s.values_list('providing_service', flat = True))
        return list()
    
    def _get_provider_as_nons(self):

        if self._get_overwatchers_as_overwatchers_ow().count() != 0:

            s = self._get_overwatchers_as_overwatchers_ow().first().service_retainer.filter(is_reciever = False)
            return self.struct_type_src["rp"].objects.filter(pk__in = s.values_list('providing_service', flat = True))
        return list()

    def name0(self, type, instance):
        if type == "sr":
            return "reciever"
        elif type == "ow":
            return "overwatcher"

    def name1(self, type, instance):
        return instance.content_object.name

    def details0(self, type, instance):
        if type == "sr":
            return "you recieve services from this organization"
        elif type == "ow":
            return "you have acces to someone who recievers organization from this organization"

    def details1(self, type, instance):
        worker_type = ""
        if type == "sp":
            worker_type = "Employee"
        elif type == "rp":
            worker_type = "Service Reciever"
        elif type == "op":
            worker_type = "Service Reciever Overwatcher"
        return instance.content_object.details(worker_type)
    #********************************** Beggining of handles *************************

    def handle(self, instance, type, num):
        kwargs = dict()
        kwargs[self.structure[0]] = getattr(self, self.structure[0] + num)(type, instance)
        kwargs[self.structure[1]] = getattr(self, self.structure[1] + num)(type, instance)
        kwargs[self.structure[2]] = type
        kwargs[self.structure[3]] = self.struct_type_src[type]
        kwargs[self.structure[4]] = instance.pk

        self.struct_f.append(kwargs)

    def _handle_0(self, instance, type):
        frame = inspect.currentframe()
        num = frame.f_code.co_name[-1]
        assert isinstance(instance, self.known_handle_models[int(num)]), " needs to be a service reciever or overwatcher"
        self.handle(instance, type, num)

    def _handle_1(self, instance, type):
        frame = inspect.currentframe()
        num = frame.f_code.co_name[-1]
        assert isinstance(instance, self.known_handle_models[int(num)]), " needs to be a service reciever or overwatcher"
        self.handle(instance, type, num)

    #****************************************handle******************************over

    def collect(self):
        for name in dir(self):
            if name.startswith('_get_'):
                for q in getattr(self, name)():
                    num =  self.known_handle_models.index(q.__class__)
                    getattr(self, f'_handle_{num}')(q, name[-2:] )
        return self.struct_f
