from django.db import models
from tiempo.models import WyzFloatModel, WyzTimeModel
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

def is_minutes_from_today_times(env_queryset, minute):
    from task.managers import absorb_real_time

    # TODO: Must make sure that your that your ae using a queryset as obj
    time = absorb_real_time(minute)
    times = env_queryset.all_with_time().filter(dates__in = allowed_dates).filter(Q(start_time__lte= time) & Q(end_time__gte=time))
    return times()

# NOTE: query for all thew sessions that will use similarly





class CoEnvSessionQuerySet(models.QuerySet):
    def  all_with_time(self):
         from .models import EnviromentalSession
         envs = EnviromentalSession.objects.filter(coenvsession_sessions__in = self.all())
         return WyzTimeModel.objects.filter(enviromentalsession_session__in = envs)

    def all_with_org_time(self, organization):
        org_co_envs = self.filter(pk__in = organization.coenvsession_float_models.all())
        return org_co_envs.all_with_time()

    def is_min_away(self, minutes):
        times = is_minutes_from_today_times(self, minutes)
        return self.filter(enviroment__in=EnviromentalSession.objects.filter(active_time__in =times ))



class FloaterSessionQuerySet(models.QuerySet):
    def  all_with_time(self):
         return WyzFloatModel.objects.filter(floatersession_sessions__in = self.all())

    def  all_with_org_time(self, organization):
        floater_envs =  self.filter(pk__in = organization.floatersession_float_models.all())
        return floater_envs.all_with_time()

    def is_min_away(self, minutes):
        times = is_minutes_from_today_times(self, minutes)
        return self.filter(active_time__in=times)

class EnviromentalSessionQuerySet(models.QuerySet):
    def  all_with_time(self):
         return WyzTimeModel.objects.filter(enviromentalsession_session__in = self.all())


    def  all_with_org_time(self, organization):
        org_envs =  self.filter(pk__in = organization.enviromentalsession_float_models.all())
        return org_envs.all_with_time()

    def is_min_away(self, minutes):
        times = is_minutes_from_today_times(self, minutes)
        return self.filter(active_time__in=times)

class SessionsContainerQuerySet(models.QuerySet):
    def  all_with_time(self, organization):
        from itertools import chain
        from organizations.models import Organization
        contents_list = list(set(self.all().values_list('content_type', flat = True)))
        chain_list = list()
        assert(isinstance(organization, Organization) or organization is None, "it needs to be an instance or None ")
        for c in contents_list:
            model_class = ContentType.objects.get(pk = c).model_class()
            f =  model_class.objects.filter(pk__in = self.filter(content_type = c).values_list('object_id', flat = True))
            print(f)
            time_objs = f.all_with_time() if organization is None else f.all_with_org_time(organization)
            chain_list.append(time_objs)
        return list(chain(*chain_list))

    def is_minutes_from_today(self, minutes):
        from itertools import chain
        floaters = self.filter(content_type = ContentType.objecs.get(model = "floatersession"))
        sessions = self.filter(content_type = ContentType.objecs.get(model = "enviromentalsession"))
        coenvs = self.filter(content_type = ContentType.objecs.get(model = "coenvsession"))

        return list(chain(floaters.is_min_away(minutes),\
                            sessions.is_min_away(minutes),\
                            conenv.is_min_away(minutes)))





class CoEnvSessionManager(models.Manager):
    def get_queryset(self):
        return CoEnvSessionQuerySet(self.model, using=self._db)

    def all_with_time(self):
        return self.get_queryset().all_with_time()

    def all_with_org_time(self, organization):
        return self.get_queryset().all_with_org_time(organization)

class FloaterSessionManager(models.Manager):
    def get_queryset(self):
        return FloaterSessionQuerySet(self.model, using=self._db)

    def all_with_time(self):
        return self.get_queryset().all_with_time()

    def all_with_org_time(self, organization):
        return self.get_queryset().all_with_org_time(organization)

class EnviromentalSessionManager(models.Manager):
    def get_queryset(self):
        return EnviromentalSessionQuerySet(self.model, using=self._db)

    def all_with_time(self):
        return self.get_queryset().all_with_time()

    def all_with_org_time(self, organization):
        return self.get_queryset().all_with_org_time(organization)

class SessionsContainerManager(models.Manager):
    def get_queryset(self):
        return SessionsContainerQuerySet(self.model, using=self._db)

    def all_with_time(self, organization=None):
        return self.get_queryset().all_with_time(organization)
