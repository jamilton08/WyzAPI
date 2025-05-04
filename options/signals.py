from global_utilities.variable_collections.pillars.collected import l
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import OptionLinker




for pillar in l:
    @receiver(post_save, sender=pillar)
    def generate_options(sender, instance, created, **kwargs):
        if created:
            OptionLinker.options_linker(instance)
