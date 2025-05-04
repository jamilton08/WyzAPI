from django.db import models
from django.utils import timezone
import pytz
from organizations.models import Organization, OrganizationUser
from django.contrib.auth.models import User


class ServiceRecieverQuerySet(models.QuerySet):
    def get_service_reciever(self):
        are_recievers = (self.annotate(serviced_by_orgs=Count('organization'))
                            .filter(num_participants__gt=0))
        return are_recievers

    def get_organization_recievers(self, organization):
        r_obj = self.filter(organization = organization)
        return r_obj.filter(reciever__in = User.objects.all())

    def get_organization_overwatchers(self, organization):
        r_obj = self.filter(organization = organization)
        return r_obj.filter(overwatcher__in = User.objects.all())


    def get_organization_recievers_u(self, organization):
        return User.objects.filter(pk__in = self.get_organization_recievers(organization)\
        .values_list('reciever', flat=True))

    def get_organization_overwatchers_u(self, organization):
        return User.objects.filter(pk__in = self.get_organization_overwatchers(organization)\
        .values_list('overwatcher', flat=True))

    def get_reciever_organizations(self, user):
        return Organization.objects.filter(pk__in = user\
                                                .recieving_service\
                                                .values_list('organization', flat = True))

    def get_overwatcher_organizations(self, user):
        return Organization.objects.filter(pk__in = user\
                                                .overwatches\
                                                .values_list('organization', flat = True))
    
    def get_reciever_overwatchers(self, user):
        raw_overwatchers = self.filter(reciever = user).values_list('overwatcher', flat = True)
        return User.objects.filter(pk__in = raw_overwatchers)
    
    def get_overwatchers_reciever(self, user):
        raw_recievers = self.filter(reciever = user).values_list('reciever', flat = True)
        return User.objects.filter(pk__in = raw_recievers)
    
    def get_reciever_overwatchers_org_limit(self, user, organization):
        raw_overwatchers = self.filter(reciever = user, organization = organization).values_list('overwatcher', flat = True)
        return User.objects.filter(pk__in = raw_overwatchers)
    
    def get_overwatchers_reciever_org_limit(self, user, organization):
        raw_recievers = self.filter(reciever = user, organization = organization).values_list('reciever', flat = True)
        return User.objects.filter(pk__in = raw_recievers)




class ServiceRecieverManager(models.Manager):
    def get_queryset(self):
        return ServiceRecieverQuerySet(self.model, using=self._db)

    def get_service_reciever(self):
        return self.get_queryset().get_service_reciever()

    def get_organization_recievers(self, organization):
        return self.get_queryset().get_organization_recievers(organization)

    def get_organization_overwatchers(self, organization):
        return self.get_queryset().get_organization_overwatchers(organization)

    def get_organization_recievers_u(self, organization):
        return self.get_queryset().get_organization_recievers_u(organization)

    def get_organization_overwatchers_u(self, organization):
        return self.get_queryset().get_organization_overwatchers_u(organization)

    def get_reciever_organizations(self, user):
        return self.get_queryset().get_reciever_organizations(user)

    def get_overwatcher_organizations(self, user):
        return  self.get_queryset().get_overwatcher_organizations(user)
    
    def get_reciever_overwatchers(self, user):
        return self.get_queryset().get_reciever_overwatchers(user)
    
    def get_overwatchers_reciever(self, user):
        return self.get_queryset().get_overwatchers_reciever(user)
    
    def get_reciever_overwatchers_org_limit(self, user, organization):
        return self.get_queryset().get_reciever_overwatchers_org_limit(user, organization)
    
    def get_overwatchers_reciever_org_limit(self, user, organization):
        return self.get_queryset().get_overwatchers_reciever_org_limit(user, organization)  

class InvitationsQuerySet(models.QuerySet):
    def user_request(self):
        return self.filter(admin_approve__isnull = True)

    def admin_request(self):
        return self.filter(admin_approve__isnull = False)

    def user_invites(self, user):
        return self.admin_request().filter(signee = user)

    def user_requests(self, user):
        return self.user_request().filter(signee = user)
    
    

    def org_invites(self, org_user, query_tools):
        if not isinstance(org_user, OrganizationUser):
            raise TypeError('must be an organizationuser in order to make this query')
        if query_tools is not None:
            if not isinstance(query, tuple):
                raise TypeError('must be a tuple')
            issubclass(query_tools[0], models.Model)
            if not isinstance(query_tools[1], str):
                raise TypeError('must send str this way')
            k = {f'{query_tools[1]}' : query_tools[0].objects.filter(organization = org_user.organization) }
            return self.admin_request().filter(**k)
        else:
            return self.admin_request().filter(organization = org_user.organization)

    def org_request_recieved(self, org_user, query_tools):
        if not isinstance(org_user, OrganizationUser):
            raise TypeError('must be an organizationuser in order to make this query')
        if query_tools is not None:
            if not isinstance(query, tuple):
                raise TypeError('must be a tuple')
            issubclass(query_tools[0], models.Model)
            if not isinstance(query_tools[1], str):
                raise TypeError('must send str this way')
            k = {f'{query_tools[1]}' : query_tools[0].objects.filter(organization = org_user.organization) }
            return self.user_request().filter(**k)
        else:
            print('jere')
            return self.user_request().filter(organization = org_user.organization)





class SigneeRecieverQuerySet(InvitationsQuerySet, models.QuerySet):
    pass

class OverwatchSigneeQuerySet(InvitationsQuerySet, models.QuerySet):
    pass



class SigneeRecieverManager(models.Manager):
    def get_queryset(self):
        return SigneeRecieverQuerySet(self.model, using=self._db)

    def all_requests(self):
        return self.get_queryset().user_request()

    def all_invites(self):
        return self.get_queryset().admin_request()

    def user_invites(self, user):
        return self.get_queryset().user_invites(user)

    def user_request(self, user):
        return self.get_queryset().user_requests(user)

    def org_invites(self, org_user, query_tools = None):
        return self.get_queryset().org_invites(org_user, query_tools = query_tools)

    def org_request_recieved(self, org_user, query_tools = None):
        return self.get_queryset().org_request_recieved(org_user, query_tools = query_tools)


class OverwatchSigneeManager(models.Manager):
    def get_queryset(self):
        return OverwatchSigneeQuerySet(self.model, using=self._db)

    def all_requests(self):
        return self.get_queryset().user_request()

    def all_invites(self):
        return self.get_queryset().admin_request()

    def user_invites(self, user):
        return self.get_queryset().user_invites(user)

    def user_request(self, user):
        return self.get_queryset().user_requests(user)

    def org_invites(self, org_user, query_tools = None):
        return self.get_queryset().org_invites(org_user, query_tools = query_tools)

    def org_request_recieved(self, org_user, query_tools = None):
        return self.get_queryset().org_request_recieved(org_user, query_tools = query_tools)
