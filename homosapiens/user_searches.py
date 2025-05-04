from django.contrib.auth.models import User
from .models import ServiceReciever
from django.db.models import Q, Count
from organizations.models import Organization


class Searcher(object):
    
    @classmethod
    def _find_qs(cls,search_term):
        org_recievers = ServiceReciever.objects.filter(organization__in = Organization.objects.filter(name__icontains = search_term))
        # Query to get users based on the number of matching fields
        users = User.objects.annotate(
            match_count=Count(
                'id', 
                filter=Q(username__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term) | 
                    Q(organizations_organization__name__icontains = search_term) |
                    Q(recieving_service__in = org_recievers) | 
                    Q(overwatches__in = org_recievers) |
                    Q(emails__email__icontains = search_term) |
                    Q(phones__phone_number__icontains = search_term)
            )
        ).filter(match_count__gt=0).distinct().order_by('-match_count')

        return users

    @classmethod
    def range_return(cls, index, search_term):
        qs = cls._find_qs(search_term)
        size = len(qs)
        print(index, search_term) 
        last_element = index + 5

        if  last_element > size:
            return qs[index : size]
        else:
            return qs[index : last_element]
        
    @classmethod
    def collect_tags(cls, user):
        from orgs.utilities import get_user_involved_organizations as gei
        merged = list()
        merge_tags = lambda org, user: merged.extend(cls.get_tag(user, org))
        seen_list = list()
        orgs = list()
        for org in gei(user):
            if org["pk"] not in seen_list:
                orgs.append(org)
                seen_list.append(org["pk"])
        for org in  orgs:
            merge_tags(Organization.objects.get(pk = org['pk']), user)
        return merged
    
    @classmethod
    def get_tag(cls, user, org):
        from importlib import import_module as _i
        tags = list()
        role = list() 
        org_util = _i('orgs.utilities')
        if org_util.is_admin(user, org):
           role.append('admin')
        if org_util.is_member(user, org):
           role.append('member')
        if org_util.is_service_reciever(user, org):
           role.append('service reciever')
        if org_util.is_service_overwatcher(user, org):
            role.append('service overwatcher')
        for r in role:
            tags.append("{} {}".format(org.name, r))

        return tags
    
    @classmethod
    def _find_orgs_involved_qs(cls,search_term, orgs):
        from orgs.utilities import get_organizations_users
        # Query to get users based on the number of matching fields
        users = get_organizations_users(orgs).annotate(
            match_count=Count(
                'id', 
                filter=Q(username__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term) | 
                    Q(emails__email__icontains = search_term) |
                    Q(phones__phone_number__icontains = search_term)
            )
        ).filter(match_count__gt=0).distinct().order_by('-match_count')

        return users
    
    # TODO: eventually condense and find a location for thise function and add a queryset as a parameter
    @classmethod
    def org_range_return(cls, index, search_term, orgs):
        qs = cls._find_orgs_involved_qs(search_term, orgs)
        size = len(qs)
        last_element = index + 5

        if  last_element > size:
            return qs[index : size]
        else:
            return qs[index : last_element]
        

