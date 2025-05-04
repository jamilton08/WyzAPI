from django.db import models
from django.utils import timezone
import pytz

class TextCodeQuerySet(models.QuerySet):
    def remove_expiry(self, minutes):
        from datetime import datetime, timedelta
        time_threshold = timezone.now() - timedelta(minutes=minutes)
        results = self.filter(created__lt=time_threshold)
        results.delete()


class TextCodeManager(models.Manager):
    def get_queryset(self):
        return TextCodeQuerySet(self.model, using=self._db)

    def remove_expiry(self, minutes):
        return self.get_queryset().remove_expiry(minutes)
