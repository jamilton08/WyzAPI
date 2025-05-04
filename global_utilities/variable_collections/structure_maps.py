from importlib import import_module as _i
I = _i("actions.models")
ACTION = I.Record
RES = I.ActionResponse

def org_invited_overwatcher(action):
    return action.record_type == I.SEND and action.content_type == _i("homosapiens.models").RecieverSignee
notifiables_dict = dict()
notifiableD_
