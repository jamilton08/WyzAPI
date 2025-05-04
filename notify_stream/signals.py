from global_utilities.variable_collections.rocks.collected import l
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType as CT
from importlib import import_module as _i





## # TEMP: rocks will soon be renamed workers as they are transistion for pillarss, rocks are samller services like options
for rock in l:
    @receiver(post_save, sender=rock)
    def generate_options(sender, instance, created, **kwargs):
        cont = CT.objects.get_for_model(instance.__class__)
        pk = str(instance.pk)

        notification = _i("notifications.models").Notification.objects.filter(action_object_content_type = cont, action_object_object_id = pk ).last()
        # TEMP: find a way to involved the user in this specificc one
        if not created:
                if  notification is not None:
                    print("do you go here", notification)
                    if notification.actor_content_type == CT.objects.get_for_model(_i("actions.models").ResponseAction):
                        print("do yioy go here")
                        notification.unread = False
                        notification.save()
