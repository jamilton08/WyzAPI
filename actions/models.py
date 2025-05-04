from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from organizations.models import Organization
from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from .managers import RespondActionManager



class Record(models.Model):
    CREATE = "C"
    CHANGE = "E"
    DELETE = "D"
    TOOK = "T"
    SENT = "S"
    REQUESTED = "Q"
    ACCEPTED = "A"
    DECLINED = "L"
    RESPONDED = "R"
    ADDED = "B"
    REMOVED ="M"


    RECORD_CHOICES = {
        CREATE: _("Create"),
        CHANGE: _("Change"),
        DELETE:_("Delete"),
        TOOK:_("Took"),
        SENT : _("Sent"),
        REQUESTED :_("Requested"),
        ACCEPTED:_("Accepted"),
        DECLINED :_("Declined"),
        RESPONDED : _("Responded"),
        ADDED : _("Added"),
        REMOVED : _("Remove")
         }



    RECORD_TUPLE  = [(k, v) for k, v in RECORD_CHOICES.items()]

    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='%(class)s_class_records')
    object_id = models.IntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    record_type = models.CharField(
        max_length=1,
        choices=RECORD_TUPLE,
        default=CREATE,
    )


    def details(self, rephrase = None):
        return f'{self.RECORD_CHOICES[self.record_type].lower() if rephrase is None else rephrase} {self.content_type.model_class().__name__.lower()}'.replace(" ", "_")
    class Meta:
        abstract = True


class PersonalRecord(Record, models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='actions')
    affiliation = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='affiliated_actions', blank = True, null = True )

    def details(self, sender = None, rephrase = None):
        from orgs.utilities import is_within_org
        super_string = super().details(rephrase = rephrase)
        if sender :
            parsed_sender = sender
        else:
            parsed_sender = "{}".format("user" if not  is_within_org(self.user,self.affiliation) else "organization")
        return f'{parsed_sender} {super_string}'.replace(" ", "_")

class OrganizationRecord(Record,models.Model):
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE, related_name='actions')

    def map_to_user(self):
        return PersonalRecord.objects.get(content_type = self.content_type, object_id = self.object_id, record_type = self.record_type)




class ResponseAction(models.Model):

    ORGANIZATION = "O"
    USER = "U"
    ACCEPTABLE_RES = [(ORGANIZATION, "Organization"),
                        (USER, "User")    ]
    #should always be  limited and connected to only two type of actions
    content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='responses')
    object_id = models.IntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    users =  models.ManyToManyField(User, related_name='need_to_respond')
    responded = models.BooleanField()
    response_type = models.CharField(
        max_length=1,
        choices=ACCEPTABLE_RES,
        default="U",
    )
    linker = models.ManyToManyField(PersonalRecord, related_name = 'linked_response')

    objects = RespondActionManager()
