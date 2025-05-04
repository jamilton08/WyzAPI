from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from .models import  OrganizationRecord
from django import dispatch
from session.models import SessionsContainer
from .models import PersonalRecord
from django.contrib.contenttypes.models import ContentType

##actions will have two components, once when something is created and when somethings are added. when things
##are added they will manually fire a signal and when objects are saved the signals will be here on post_save
record_action_signal = dispatch.Signal(["sender","instance","user", "el"])

@receiver(post_save, sender=PersonalRecord)
def record_response_reaction(sender, instance, created, **kwargs):
    from .response import ActionResponse
    from django.contrib.contenttypes.models import ContentType
    model_content = instance.content_type
    model = model_content.model_class()
    if hasattr(model, "construct"):
        response = model.construct(instance)
        if not response: #check if a response already exist
            instance.content_object.responding(instance)

def abs_func_ae(sender, instance, created, org):
    if created:
        type = OrganizationRecord.CREATE
    else:
        type = OrganizationRecord.CHANGE

    content = ContentType.objects.get_for_model(sender)
    id = instance.pk
    r = OrganizationRecord.objects.create(organization = org, content_type = content,  object_id= id,\
     record_type = type )
    r.save()

def abs_func_d(sender, instance, org):

    r = OrganizationRecord.objects.create(organization = org, content_type = content, object_id = id,\
     record_type = OrganizationRecord.DELETE )
    r.save()

@receiver(post_save, sender=SessionsContainer)
def record_sessions_ae(sender, instance, created, **kwargs):
    org = instance.content_object.organization
    abs_func_ae(sender, instance, created, org)

@receiver(pre_delete, sender=SessionsContainer)
def record_sessions_d(sender, instance, created, **kwargs):
    org = instance.content_object.organization
    abs_func_ae(sender, instance, created, org)
