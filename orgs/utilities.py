from organizations.models import Organization
from homosapiens.models import ServiceReciever

def is_within_org(user, org):
    org_users = user.organizations_organizationuser
    orgs_to_search  = Organization.objects.filter(pk = org.pk)
    involved_orgs = org_users.filter(organization__in = orgs_to_search).count()
    return bool(involved_orgs > 0)

def get_org_user(user, org):
    return user.organizations_organizationuser.filter(organization = org).first()

def is_in_org(user, org):
        return user.organizations_organizationuser.filter(organization = org).exists()

def get_user_involved_organizations(user):
    from global_utilities.serializer_storage import organization
    user_orgs = user.organizations_organization.all()
    reciever_orgs = ServiceReciever.objects.get_reciever_organizations(user)
    overwatcher_orgs = ServiceReciever.objects.get_overwatcher_organizations(user)
    combine = user_orgs | reciever_orgs | overwatcher_orgs
    return organization(combine, many = True)

def is_admin(user, org):
           return user.organizations_organizationuser.filter(organization = org, is_admin = True).exists()
       
def is_member( user, org):
           return user.organizations_organizationuser.filter(organization = org).exists()
       
def is_service_reciever(user, org):
           from importlib import import_module as _i 
           return _i('homosapiens.models').ServiceReciever.objects.filter(reciever = user, organization = org).exists()

def is_service_overwatcher(user, org):
            from importlib import import_module as _i 
            return _i('homosapiens.models').ServiceReciever.objects.filter(overwatcher = user, organization = org).exists()

def get_organizations_users(organizations):
    overwatchers = ServiceReciever.objects.get_organization_overwatchers_u(organizations)
    recievers = ServiceReciever.objects.get_organization_recievers_u(organizations)
    providers  = organizations.users.all()

    all = overwatchers | recievers | providers
    return all.distinct()
