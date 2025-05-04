from django.db import models
from django.utils import timezone
import pytz

class CopyDateTimeQuerySet(models.QuerySet):
    def remove_expiry(self, minutes):
        from datetime import datetime, timedelta
        time_threshold = timezone.now() - timedelta(minutes=minutes)
        results = self.filter(created__lt=time_threshold)
        results.delete()

    def remove_previous(self, org_user):
        user_copyboard = self.filter(org_user = org_user.pk)
        if user_copyboard.count() > 0:
            user_copyboard.delete()



class CopyDateTimeManager(models.Manager):
    def get_queryset(self):
        return CopyDateTimeQuerySet(self.model, using=self._db)

    def remove_expiry(self, minutes):
        return self.get_queryset().remove_expiry(minutes)

    def remove_previous(self, org_user):
        return self.get_queryset().remove_previous(org_user)


class DaysOfWeekQuerySet(models.QuerySet):
    def in_session(self,sche):
        import datetime
        days = self.filter(schedule_holding = sche)
        has_today = days.filter(day_of_week = datetime.date().today().weekday())
        if sche.include_or_exclude and has_today.count() > 0:
            return (has_today.count() > 0)
        else:
            return (has_today == 0)





class DaysOfWeekManager(models.Manager):
    def get_queryset(self):
        return DaysOfWeekQuerySet(self.model, using=self._db)

    def in_session(self, minutes):
        return self.get_queryset().in_session(minutes)
    

class DateQuerySet(models.QuerySet):
    def get_all_model_perms(self, model):
        id = ContentType.objects.get_for_model(model).id
        return self.filter(content_type = id)

    def get_user_with_perms(self, user):
        from orgs.models import AssignedPermsModel
        org_users = user.organizations_organizationuser.all()
        assigned_perms = AssignedPermsModel.objects.filter(org_user__in = org_users)
        return self.filter(allowed_users__in = assigned_perms)

    def get_perm_users(self, perm):
        from orgs.models import AssignedPermsModel
        from organizations.models import OrganizationUser
        assigned_perms = AssignedPermsModel.objects.filter(permmissions = perm)
        org_users = OrganizationUser.objects.filter(permission_retainer__in = assigned_perms)
        return User.objects.filter(organizations_organizationuser__in = org_users)
