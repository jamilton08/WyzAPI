from actions.models import ResponseAction, OrganizationRecord

class Builder():
    # NOTE: this will build off actions the intention is to build regular notifications and
    # XXX: responses notifications and one is about read and the other one is about werther
    # XXX: you responded
    # NOTE: all response actions will record a notification to every use in the response and certain actions will prompt
    # XXX: a notification to be created
    def __init__(self, action, users = None, response = False):
        self.action = action
        self.users = users
        self.response = response
        print("your're being called ")


    def construct_notification(self):
        from notifications.signals import notify
        actor = self.action
        recipient = self.action.users.all() if self.users is None else self.users
        verb = self.action.content_object.details() if self.response else self.action.details()
        action_object = self.action.content_object.content_object if self.response else self.action.content_object
        notify.send(actor, recipient = recipient, verb = verb, action_object = action_object)

    def __call__(self):
        self.construct_notification()

    @classmethod
    def user_unrespondeds(self, user):
        from django.contrib.contenttypes.models import ContentType
        from notifications.models import Notification
        ct = ContentType.objects.get_for_model(ResponseAction)
        u = user.need_to_respond.values_list('pk', flat = True)
        u = [str(x) for x in u]
        ## TODO: add later but after tOh esting
        #need_user_response()
        return Notification.objects.\
            filter(unread = True).\
            filter(actor_content_type = ct).\
            filter(actor_object_id__in = u).\
            order_by('timestamp')

    @classmethod
    def user_unreads(self, user):
        from .utilities import get_unread_notification
        return get_unread_notification(user)
