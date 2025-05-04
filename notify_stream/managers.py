from django.db import models

class NotifyQuerySet(models.query.QuerySet):

    def user_response_required(self, user, notification_query):
        from actions.models import ActionResponse
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(ActionResponse)
        u = user.need_to_respond.need_user_response().values_list('pk', flat = True)
        return Notifications.objects.\
            filter(unread = True).\
            filter(actor_content_type = ct).\
            filter(actor_object_id__in = u)

    def get_unread_notification(self, user):
        return user.notifications.\
            filter(unread = True).\
            exclude(pk__in = self.user_response_required(user))


class NotifyManager(models.Manager):
       def get_queryset(self):
           return OrganizationQuerySet(self.model)

       def get_sub_org(self, org):
           return self.get_queryset(org)
