from django.db import models
from services.models import ServiceClass, ServicesContainer
from homosapiens.models import ServiceReciever
from django.contrib.contenttypes.models import ContentType
from organizations.models import Organization, OrganizationUser, OrganizationOwner
from django.contrib.auth.models import User
from tiempo.models import WyzTimeModel, WyzFloatModel
from django.contrib.contenttypes.fields import GenericForeignKey
from .managers import EnviromentalSessionManager, CoEnvSessionManager, FloaterSessionManager, SessionsContainerManager
from task.time_master import TaskTimable
from options.clean import ObjectCleaner


# Create your models here.

class Session(models.Model):
    name = models.CharField(max_length = 100)
    organization = models.ForeignKey(Organization, on_delete = models.CASCADE, related_name ='%(class)s_float_models')
    overwatchers = models.ManyToManyField(User, related_name = "%(class)s_attending_overwatcher" )
    service_receiver = models.ManyToManyField(User, related_name = "%(class)s_attending_reciever" )
    service_providers = models.ManyToManyField(User, related_name = "%(class)s_attending_providers")
    overwatchers_restrict = models.BooleanField(default = False)
    service_receiver_restrict = models.BooleanField(default = False)
    service_providers_restrict = models.BooleanField(default = False)

    time = ""

    @classmethod
    def create_obj(cls, time_relicance, org, **kwargs):
        query = {cls.time : time_relicance, 'organization' : org}
        kwargs.update(query)
        s = cls.objects.create(**kwargs)
        return s

    def add_session_manager(self, manager):
        pass

    def times_objects(self):
        pass
    # TODO:
    # NOTE: this is a shared and should actually be implemented in every model, will expand further as todo is above
    def get_users(self):
        users = list()
        if not overwatchers_restrict:
            users.append(self.overwatchers)

        if not service_receiver_restrict:
            users.append(self.service_receiver)

        if not service_providers_restrict:
            users.append(self.service_providers)
        return list(chain(*users))

    def save(self, **kwargs):
        super(Session, self).save(**kwargs)
        s_object = SessionsContainer.objects.create(\
        session_id = f'{self.organization.name}_{self.name}',\
        content_type = ContentType.objects.get_for_model(self.__class__),\
        object_id = self.pk\
        )
        s_object.save()


    def can_add_overwatcher(self, user, org):
        from homosapiens.models import ServiceReciever
        return  user in ServiceReciever.objects.get_organization_overwatchers_u(org)

    def can_add_reciever(self, user, org):
        from homosapiens.models import ServiceReciever
        return  user in ServiceReciever.objects.get_organization_recievers_u(org)

    def can_add_org_user(self, user, org):
        from orgs.utilities import is_within_org
        return is_within_org(user, org)

    def valid_overwatcher(self):
        return self.overwatchers_restrict

    def valid_reciever(self):
        return self.service_receiver_restrict

    def valid_org_user(self):
        return self.service_providers_restrict

    def add_overwatcher(self, user):
        self.overwatchers.add(user)

    def add_reciever(self, user):
        self.service_receiver.add(user)

    def add_org_user(self, user):
        self.service_providers.add(user)

    class Meta:
        abstract = True


class SessionManagerAdder(models.Model):
    session_provider = models.ManyToManyField(User, related_name="%(class)s_hosting_enviroment")
    session_provider_class = models.ManyToManyField(ContentType,  related_name='%(class)s_allowed_provider_content')
    session_service = models.ManyToManyField(ServicesContainer, related_name='%(class)s_allowed_service')

    def _provider(self, manager):
        cl = manager.__class__
        return cl, cl.__name__

    def is_in_provider_class(self, manager):
        is_in = False
        for s in self.session_provider_class.all():
            if isinstance(manager, s.model_class()):
                is_in = True
        return is_in

    def overwathcer_provider(self, manager, service, receiver = None):
        if  not self.is_in_provider_class(manager):
            raise TypeError("the user must be part of the stuff you know")
        p_cl, p_cl_name = self._provider(manager)
        r_obj = None
        person = None
        if hasattr(manager, 'service_retainer'):
            r_obj = getattr(manager, 'service_retainer')
            if reciever is not  None:
                r_obj = r_obj.filter(is_reciever = reciever).get()
            if self.service.content_object in getattr(r_obj, f'{r_obj.__class__.__name__}_providing').all():
                if reciever is None:
                    person = r_obj.provider_obj.user
                else:
                    person = r_obj.reciever_obj.reciever if reciever else r_obj.reciever_obj.overwatcher
                self.provider.add(person)
                self.save()
                return True
        return False

    class Meta:
        abstract = True




class EnviromentalSession(Session, SessionManagerAdder, TaskTimable,  models.Model):
    active_time = models.ForeignKey(WyzTimeModel, on_delete=models.CASCADE, related_name = "%(class)s_session")
    time = "active_time"
    time_m = "active_time"
    # NOTE: every sessions for purposes of defining which users may be in nboth and only require one noting
    #so example attendance and many other will ahve sub groups  and super groups and they need to understand
    #what will be in each other to synchronize their attendance and other services
    super_merge = 'coenvsession_sessions'
    objects = EnviromentalSessionManager()
    def times_objects(self):
        return self.active_time




class CoEnvSession(Session, SessionManagerAdder, TaskTimable, models.Model):
     enviroment = models.ForeignKey(EnviromentalSession, on_delete=models.CASCADE, related_name = "%(class)s_sessions")
     time = "enviroment"
     time_m = "enviroment"
     # NOTE:  this will be the other side of super merge which goes into the parents to synchronize services
     #these variables will be looked at by the services to understand and denote synchronization
     sub_merge = 'enviroment'
     objects = CoEnvSessionManager()

     def times_objects(self):
         return self.enviroment.active_time

class FloaterSession(Session, SessionManagerAdder, TaskTimable, models.Model):
    active_time = models.ForeignKey(WyzFloatModel, on_delete=models.CASCADE, related_name = "%(class)s_sessions")
    time = "active_time"
    time_m = "active_time"
    objects = FloaterSessionManager()

    def times_objects(self):
        return self.active_time

class SessionsContainer(ObjectCleaner, models.Model):
        from wyz_address.models  import WyzAddress
        session_id = models.SlugField(blank = True, null = True, max_length = 250)#userful for exteernal or frontend identification of permission
        content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='sessions')
        object_id = models.IntegerField()
        content_object = GenericForeignKey('content_type', 'object_id')


        objects = SessionsContainerManager()

        allowed_contents = [EnviromentalSession,CoEnvSession,FloaterSession]
        @classmethod
        def get_all_user_sessions(cls, user):
            from itertools import chain
            chain_list= list()
            for c in cls.allowed_contents:
                # TODO: make a list such as [overwatcher, reciever, providers, enviroment] andn loop trough them to shorten this code
                chain_list.append(getattr(user, f'{c.__name__}_attending_overwatcher'.lower()).all())
                chain_list.append(getattr(user,f'{c.__name__}_attending_reciever'.lower()).all())
                chain_list.append(getattr(user,f'{c.__name__}_attending_providers'.lower()).all())
                chain_list.append(getattr(user,f'{c.__name__}_hosting_enviroment'.lower()).all())
            return list(chain(*chain_list))
        # NOTE:  this give a list with the user is sessions and the start time and end time for them for a single user
        @classmethod
        def get_times_list(cls, user):
            times_list = list()
            for t in cls.get_all_user_sessions(user):
                t_obj = t.times_objects()
                times_list.append([t, t_obj.start_time, t_obj.end_time])
            return sorted(times_list, key=lambda x:x[1])

        # NOTE: this gives a breakdown of during what times the user is busy
        def conflict_session(self, user):
            from tiempo.utilities import date_clash, matches_days
            time_obj= self.content_object.times_objects()
            conflicts = list()
            s = time_obj.start_time
            e = time_obj.end_time

            for c in self.__class__.get_times_list(user):
                ot = c[0].times_objects()
                if  ((s >= c[1] and s <= c[2]) or (e >= c[1] and e <= c[2])) and date_clash(time_obj.dates, ot.dates) and matches_days(time_obj, ot):
                    conflicts.append(c[0])
            return conflicts


class OverlappingSessions(models.Model):
    session1 =  models.ForeignKey(SessionsContainer,on_delete=models.CASCADE, related_name='overlapInvolvement1')
    session2 =  models.ForeignKey(SessionsContainer,on_delete=models.CASCADE, related_name='overlapInvolvement2')
    priority = models.BooleanField()
    approved = models.BooleanField()

    @classmethod
    def filter_existing_overlap(cls, session):
        from django.db.models import Q
        c1 = Q(session1 = session)
        c2 = Q(session2 = session)
        qs = cls.objects.filter(c1 & c2)
        return qs.exists(), qs


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session1", "session2"],
                                    name='unique'),]


class OverLapDecision(models.Model):
    overlap_sessions = models.OneToOneField(OverlappingSessions, on_delete= models.CASCADE, related_name = "decision")
    user1 = models.ForeignKey(User, on_delete = models.CASCADE, related_name ='overlapping_decisiomaker1', blank = True, null = True )
    user2 = models.ForeignKey(User, on_delete = models.CASCADE, related_name ='overlapping_decisiomaker2', blank = True, null = True )


    def approval_count(self, user):
        from org.utilities import is_within_org
        true1 = False
        true2 = False
        session1 = self.overlap_sessions.session1
        session2 = self.overlap_sessions.session2
        org1 = session1.content_object.organization
        org2 = session2.content_object.organization
        if is_within_org(user, org1):
            # TODO: check if it has perms to edit these specific session_servic
            #true1 = bool(has_perm(user,session1.content_type, session1.object_id, "E" ))
            pass

        if is_within_org(user, org2):
            # TODO: check if it has perms to edit these specific session_servic
            #true2 = bool(has_perm(user,session2.content_type, session1.object_id, "E" ))
            pass

        return list(true1, true2)


    def can_approve(self, user):
        if self.approved:
            return False
        ca = False
        for i, count in zip(self.approval_count(user), range(2)):
            if i and  getattr(self, f'user{str(count)}') is None:
                ca = True
        return ca


    def approve(self, user):
        ca = False
        for i, count in zip(self.approval_count(user), range(2)):
            if i and  getattr(self, f'user{str(count)}') is None:
                setattr(self, f'user{str(count)}', user)
        self.save()
        if self.user1 is not None and self.user2 is not None:
            self.approved = true

    def change_settings(self):
        self.overlap_sessions
