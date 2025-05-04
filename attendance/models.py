from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from wyz_address.models import WyzAddress
from django.contrib.auth.models import User
from .managers import AbstractAttnManager
from services.models import ServicesContainer

# REVIEW: the framework of this app is attendance will be taken either as a day attendance to login or
#sessions will have individuals and people in those sessions are relied uppn to take the attendance
#complex stuff like conenviroment share students and so when attendance is logged for one, it must also log it for the others


class Attn(models.Model):
        content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='%(class)s_attn')
        object_id = models.IntegerField()
        content_object = GenericForeignKey('content_type', 'object_id')
        login_location = models.ManyToManyField(WyzAddress, related_name = "logger" )
        users = models.ManyToManyField(User, related_name = "needed_logs" )
        ## TODO: sevice must be limited to those who are within the session your connecting this if its session
        allowed_to_take_attendance = models.ManyToManyField(User, related_name = "attendance_take")
        objects = AbstractAttnManager()
        # TODO: we will have a list for enviroments and one for times as blocks and attend class, block will mainly have abilites

        def get_count_done(self):
            return self.users.all().count()  - self.completed_logs.all().count()

        def get_count_missing(self):
            return self.users.all().count() - self.get_count_done()

        def attendance_done(self):
            return self.get_count_done() == 0

        def get_merged(self):
            obj = self.content_object
            if hasattr(obj, "super_merge"):
                return getattr(obj, obj.super_merge).all()
            elif hasattr(obj, "sub_merge"):
                # NOTE: return as a filter list to maintaint consistency when caller of function recieves it
                parent_obj = getattr(obj, obj.sub_merge)
                return parent_obj.__class__objects.filter(pk = parent_obj.pk)
            else:
                return None



        # NOTE: This function is decides wether a user is taking a day attendance or if for something else is happening such
        def allowed_to_take_attendance_add(user):
            from tiempo.models import WyzFloatModel
            if isinstance(self.content_object, WyzFloatModel):
                return user
            else:
                if user in self.content_type.get_users():
                    self.allowed_to_take_attendance_add.add(user)


        def already_taken_att(self, user):
            return  user in User.objects.filter(logins__in = self.completed_log.get_today_logins.all())






class Login(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='logins')
    attended = models.ForeignKey(Attn, on_delete=models.CASCADE, related_name='completed_logs')

    # NOTE: checks if user is within the time frame of signing in
    @classmethod
    def user_belongs(cls, user):
        from datetime import datetime
        curr = datetime.now()
        time = curr.time()
        date = curr.date()
        if user.needed_logs.exists():
            for l in user.needed_logs.get_all_time().all():
                if l.accepted_time_frame(curr) :
                    print("in_some_valid")



        return None
        # NOTE: will take care of any sessions that nmight have same students in their attendance as a cosession
        # XXX: one concern thatYeah  might come up is checking time however it is assumed that if the initial was chrcked for timing
        # XXX: all related sessions are checked for timing becausw they are withing the samw time
    def handle_merges(self, taking_attendance):
        att_query = self.attended.get_merged()
        if att_query is not None:
            for attn in att_query:
                kwargs = dict()
                kwargs["content_type"] = ContentType.objects.get_for_model(attn.__class__)
                kwargs["object_id"] = attn.pk
                # NOTE: check each object if they have attendane and will create a login for them if attn exist
                if Attn.objects.filter(**kwargs):
                    attn_instance = Attn.objects.get(**kwargs)
                    # NOTE: we wanna make sure that evertone taking attendance for other can also do this type of attendance to
                    # make it synchronized amongts all attendaces
                    if self.user in attn_instance.users.all() and taking_attendance in attn_instance.allowed_to_take_attendance.all() :
                        self.create(user = self.user,  attended = attn_instance)
