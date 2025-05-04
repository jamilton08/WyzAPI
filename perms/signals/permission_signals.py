from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from perms.signals.manager import TrafficConcealer
from global_utilities.variable_collections.pillars.collected import l



for pillar in l:
    @receiver(post_save, sender=pillar)
    def create_permissions(sender, instance, created, **kwargs):
        TrafficConcealer().create_record(sender, instance, created, **kwargs)
        


#@receiver(post_save, sender=Organization)
#def create_org_permissions(sender, instance, created, **kwargs):
#    TrafficConcealer().create_record(sender, instance, created, **kwargs)
