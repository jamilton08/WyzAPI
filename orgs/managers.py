from django.db import models

class OrganizationQuerySet(models.query.QuerySet):
    def get_sub_org(self, org):
        return self.filter(parent_org = org)

class OrganizationManager(models.Manager):
       def get_queryset(self):
           return OrganizationQuerySet(self.model)

       def get_sub_org(self, org):
           return self.get_queryset(org)
       
class OrgSigneesQuerySet(models.query.QuerySet):
    # users invited by org should an admin approved already, and the signee of who go invited, with org listed
    def personal_pending_invites(self,user):
        return user.sign_ups_to.filter(admin_approve__isnull = False, approved = False, signee = user)

        # for orgs invited by user should an admin empty already, and the signee of who invited them , with org listed
    def orgs_pending_invites(self,org):
             return self.filter(organization=org, admin_approve__isnull =True, approved=False)

    def orgs_sent_pending_invites(self,org):
             return self.filter(organization=org, admin_approve__isnull =False, approved=False)

class OrgSigneesManager(models.Manager):
    def get_queryset(self):
        return OrgSigneesQuerySet(self.model)

    def personal_pending_invites(self,user):
        return self.get_queryset().personal_pending_invites(user)

    def orgs_pending_invites(self,org):
             return self.get_queryset().orgs_pending_invites(org)

    def orgs_sent_pending_invites(self,org):
             return self.get_queryset().orgs_sent_pending_invites(org)
