from organizations.models import OrganizationUser
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from homosapiens.models import ProviderServiceProvide




@receiver(post_save, sender=OrganizationUser)
def create_service_retainer(sender, instance, created, **kwargs):
    if created:
        obj = ProviderServiceProvide.objects.create(provider_obj = instance)
        obj.save()
