# REVIEW: bool are a way to provide limitations trough true and false


def object_content(model_name):
    from django.contrib.contenttypes.models import ContentType as C
    return C.objects.get_for_model(model_name)


def grab_attendance(session, value):
    if value:
        return  object_content(session.__class__).attn_attn.filter(object_id = session.pk)
    return None


def location_neded(attendance, value, location = None):
    # TODO: succesfully process location validation  if not return error string
    dummy_location = "some location"
    if value :
        # TODO: process location
        return "location"
    return value
