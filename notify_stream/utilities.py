from importlib import import_module as _i

#action = _i("actions.models").ResponseAction
#ct_type = _i("django.contrib.contenttypes.models").ContentType
#notif = _i("notifications.models").Notification
#ct = ct_type.objects.get_for_model(action)

def user_reponses(user):
    u = list(user.need_to_respond.need_user_response().values_list('pk', flat = True))
    return notif.objects.\
        filter(actor_content_type = ct).\
        filter(actor_object_id__in = u)

def user_response_required(user):
    return user_reponses(user).filter(unread = True)

def get_unread_notification(user):
    return user.notifications.filter(unread = True).\
        exclude(pk__in = user_reponses(user))

#NOTE this functions will take action signals and extract the return value is signal to return a list of user slug to send a notificatioin in channels
def user_channel_form(signal_return):
  user_query_extract = signal_return[0][1]   
  l = list()
  for user in user_query_extract:
         l.append(user.username)   
  return l

