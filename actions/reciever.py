from django.dispatch import receiver
from . import signals
from .models import Record, PersonalRecord
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User


@receiver(signals.record_action_signal)
def handle_record_action(sender, instance, user , el, **kwargs):
    from notify_stream.engine import Builder
    l = el.upper()
    assert el in Record.RECORD_CHOICES, "it must be one of the commands found in the Record Type Class"
    content = ContentType.objects.get_for_model(sender)
    id = instance.pk
    org = None
    # organization should be passed in through kwargs or collected througn instance
    if hasattr(instance, 'organization'):
         org = instance.organization
    elif "org" in kwargs:
         org = kwargs["org"]
    rec = PersonalRecord.objects.create(user = user, content_type = content, object_id = id,\
     record_type = el, affiliation = org )
    print("does this occur before searching")
    r_cont = ContentType.objects.get_for_model(rec.__class__).responses.filter(object_id = rec.pk)
    l_cont = rec.linked_response

    b = None
    users = None

    if r_cont.count() > 0:
        r = r_cont.get()
        print("calling here but we need actor")
        b = Builder(r, response = True)
    elif l_cont.count() > 0:
        print("are we definitely here in this one ")
        ## this is if user is the one
        ## NOTE:  will get this to check wether multiple people need to be notified
        # or just on so we get response action and check

        ### NOTE: it is assumed that if mulltiple respondends is cause the request was sent to org
        #and one respondend would be one sent it

        linked_response_action = l_cont.get()
        #if linked_response_action.users.count() > 1:
        users = User.objects.filter(pk = linked_response_action.linker.exclude(pk = rec.pk).get().user.pk)
        print("first one  ")
        #else:
           # users = linked_response_action.users.all()
            #print("second one")
        b = Builder(rec, users = users)
    elif 'user_query' in kwargs:
            users = kwargs['user_query']
            #this is for recording regular notifications
            b = Builder(rec, users = users)

    if b is not None:
        b()
    return users