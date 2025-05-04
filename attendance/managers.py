from django.db import models
from tiempo.models import WyzFloatModel
from session.models import SessionsContainer
from django.contrib.contenttypes.models import ContentType

class AbstractAttnQuerySet(models.QuerySet):
    def get_sessions(self):
        content_pk = ContentType.objects.get_for_model(SessionsContainer)
        attns = self.filter(content_type = content_pk)
        return SessionsContainer.objects.filter(pk__in = attns.values_list('object_id', flat = True))

    def get_blocks(self):
        content_pk = ContentType.objects.get_for_model(WyzFloatModel)
        f =  self.filter(content_type = content_pk)
        return WyzFloatModel.objects.filter(pk__in = f.values_list('object_id', flat = True))

    def get_all_time(self):
         from itertools import chain
         return list(chain(self.get_sessions().all_with_time(organization = None), self.get_blocks()))




class AbstractAttnManager(models.Manager):
    def get_queryset(self):
        return AbstractAttnQuerySet(self.model, using=self._db)

    def get_sessions(self):
        return self.get_queryset().get_sessions()

    def get_blocks(self):
        return self.get_queryset().get_blocks()

    def get_all_time(self):
        return self.get_queryset().get_all_time()

class LoginQuerySet(models.QuerySet):
    def get_today_logins(self):
        from datetime import datetime
        today = datetime.now().date()
        return self.filter(timestamp__year = today.year, timestamp__month = today.month, timestamp__day = today.day)




class LoginManager(models.Manager):
    def get_queryset(self):
        return LoginQuerySet(self.model, using=self._db)

    def get_today_logins(self):
        return self.get_queryset().get_today_logins()
