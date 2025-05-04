from django.db import models
from tiempo.models import WyzFloatModel, WyzTimeModel
from django.contrib.contenttypes.models import ContentType


##abpve function is only meant to capture the current time from the minutes specified and implementation is left up to implementer
class TimeDetectQuery():
    @classmethod
    def absorb_real_time(cls, minute):
        import datetime as d
        from_now = d.datetime().now() + d.timedelta(minutes = minute)
        date = d.datetime.now().date()
        wd = DaysOfWeek.objects.filter(date.weekday())
        time = from_now.time()
        all_weekday = SchedulingModel.objects.filter(days_of_week = wd)
        allowed_dates = WyzDateModel.objects.filter(object_schedule__in=all_weekday)
    # NOTE: depencdecy is the model thats being relied to to release attendance which in this case is session
    def attendance_dispatch(self, minutes, responsible_abs, dependecy):
        ## TODO: should add dependecy as variable to make it make more sense when adding this and getting the required models that will need task on
        return dependecy.objects.is_minutes_from_today(5)




class NotifyQuerySet(models.QuerySet):

    def attendance_pool(self, responsible, dependecy, resolve):
        service = responsible['service'][1]
        users = responsible[0].objects.get_all_service_providers()
        return users


class NotifyManager(models.Manager):
    def get_queryset(self):
        return NotifyQuerySet(self.model, using=self._db)

    def all_with_time(self):
        return self.get_queryset().all_with_time()

    def all_with_org_time(self, organization):
        return self.get_queryset().all_with_org_time(organization)
