from importlib import import_module as im
from django.contrib.contenttypes.models import ContentType

# NOTE: This model will hold the names of every single options through the app in will be in charge of linking them appropriate
# XXX: to their options
option_name_model_matcher = list()
option_name_model_matcher.append(('grab attendance' , ContentType.objects.get_for_model(im("session.models").SessionsContainer)))
option_name_model_matcher.append(('location needed' , ContentType.objects.get_for_model(im("attendance.models").Attn)))
option_name_model_matcher.append(('block user from organization' , ContentType.objects.get_for_model(im("organizations.models").Organization)))
option_name_model_matcher.append(('assign permissions upon join' , ContentType.objects.get_for_model(im("organizations.models").OrganizationUser)))
option_name_model_matcher.append(("session_personal", ContentType.objects.get_for_model(im("session.models").Session)))

# NOTE: this will allow you to map to under what model must the query be
query_mapper = dict()
query_mapper["block user from organization"] = ContentType.objects.get_for_model(im("django.contrib.auth.models").User)
query_mapper["assign permissions upon join"] = ContentType.objects.get_for_model(im("perms.models").PermissionSecondLayerModel)


bool_mapper = dict()
bool_mapper["grab attendance"] = False
bool_mapper["location needed"] = False

choice_mapper = dict()

# NOTE: choiches to have a preselected
default_choice = dict()


selection_pre_configuration = dict()
selection_pre_configuration["session personal"] = ("service_reciever", "service_providers", "overwatchers")
