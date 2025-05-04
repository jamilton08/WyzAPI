from django.db import models
from django.contrib.contenttypes.models import ContentType


class RespondActionQuerySet(models.QuerySet):
    def get_organizational_responses(self):
        return self.filter(response_type = "O")

    def get_user_responses(self):
        return self.filter(response_type = "U")

    def need_user_response(self):
        return self.get_user_responses().filter(responded = False)

    def need_organizational_response(self):
        return self.get_organizational_responses().filter(responded = False)

    def get_organization_responses_needed(self, organization):
        from .models import PersonalRecord
        from django.db.models import Q
        orgs_actions = organization.affiliated_actions.all()

        c1 = Q(content_type = ContentType.objects.get_for_model(PersonalRecord))
        c2 = Q(object_id__in = orgs_actions.values_list('pk', flat = True))

        return self.need_organizational_response().filter(c1 & c2 )

    #def get_organization_needed_response(self, organization):
        #self.need_organizational_response()




class RespondActionManager(models.Manager):
    def get_queryset(self):
        return RespondActionQuerySet(self.model, using=self._db)

    def get_organizational_responses(self):
        return self.get_queryset().get_organizational_responses()

    def get_user_responses(self):
        return self.get_queryset().get_user_responses()

    def need_user_response(self):
        return self.get_queryset().need_user_response()

    def need_organizational_response(self):
        return self.get_queryset().need_organizational_response()

    def get_organization_responses_needed(self, organization):
        return self.get_queryset().get_organization_responses_needed(organization)
