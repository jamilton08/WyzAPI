response_signal = {}

# REVIEW: This file is intentions is to get the users their task that they must complete so the moel of the Task
# XXX: and the users who can complete it

#NOTE
#XXX this task must return the task and also object where the task must be done and to who in a double return
# NOTE: returns users and also the taks they will lcomplete in this case
def attendance_task(responsible):
    from django.contrib.contenttypes.models import ContentType
    cont = ContentType.objects.get(model = responsible.__class__.__name__.lower())
    ses_cont = SessionsContainer.objects.get(content_type = cont, object_id = responsible.pk)
    cont = ContentType.objects.get(model = ses_cont.__class__.__name__.lower())
    att = Attendance.objects.get(content_type = cont, object_id=ses_cont.pk)
    return att.users.filter(pk__in = att.allowed_services.get_all_service_providers()), att
