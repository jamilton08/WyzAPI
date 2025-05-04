from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Active, RandCodeModel, Phone, Profile



@receiver(post_save, sender=User)
def create_user_extension(sender, instance, created, **kwargs):
    if created:
        active_obj = Active.objects.create(user =instance)
        active_obj.save()
        profile = Profile.objects.create(user = instance)
        profile.save()

@receiver(pre_save, sender=Phone)
def create_phone_code_model(sender, instance, **kwargs):
    if instance.pk is None:
        pass
    else:
        active_obj = RandCodeModel.objects.create( phone=instance)
