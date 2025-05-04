#THESE INITIATORS ARE MEANT TO DETERMINE WHAT TYPE OF RESPONSIBILTY IS IS AND INDIVIDUAL CLASSES WILL
#DECIDE WHO GETS TO

from .models import ResponseAction, Record


def initiate_recieversignee(action):

    if action.record_type == Record.SENT:
        return ResponseAction.USER

    if action.record_type == Record.REQUESTED:
        return ResponseAction.ORGANIZATION
    return None

def respond_recieversignee(action):
    return (action.record_type == Record.ACCEPTED or action.record_type == Record.DECLINED)



def initiate_overwatchsignee(action):
    if action.record_type == Record.SENT:
        return ResponseAction.USER

    if action.record_type == Record.REQUESTED:
        return ResponseAction.ORGANIZATION
    return None

def respond_overwatchsignee(action):
    return (action.record_type == Record.ACCEPTED or action.record_type == Record.DECLINED)


def initiate_orgsignees(action):
    if action.record_type == Record.SENT:
        return ResponseAction.USER

    if action.record_type == Record.REQUESTED:
        return ResponseAction.ORGANIZATION
    return None

def respond_orgsignees(action):
    return (action.record_type == Record.ACCEPTED or action.record_type == Record.DECLINED)
