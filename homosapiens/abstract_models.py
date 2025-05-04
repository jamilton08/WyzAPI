from django.db import models
from django.contrib.auth.models import User
from organizations.models import Organization



class AbstractSignee(models.Model):

    organization = models.ForeignKey(Organization,on_delete=models.CASCADE,related_name = '%(app_label)s_%(class)s_signees')
    signee = models.ForeignKey(User, on_delete = models.CASCADE, null=True, related_name = '%(app_label)s_%(class)s_signed')
    admin_approve = models.ForeignKey(User, on_delete = models.CASCADE,  null = True, related_name = '%(app_label)s_%(class)s_aproving')
    approved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add  = True)
    message = models.CharField(blank = True, null = True)



    def _accept(self):
        pass

    @classmethod
    def create(self, **kwargs):
        inv = self.objects.create(**kwargs)
        inv.save()
        return inv

    def deny_accept(self):
        pass
        self.save()

    def org_accept(self,acceptor):
        self._accept()
        self.approved = True
        self.admin_approve = acceptor
        self.save()

    def user_accept(self):
        self._accept()
        self.approved = True
        self.save()

    def handle_actions_queries(self):
        if self.admin_approve is not None:
            print("admin approve", self.signee)
            return User.objects.filter(pk = self.signee.pk)
        else:
            from perms.models import PermissionSecondLayerModel as p
            from django.contrib.contenttypes.models import ContentType as c
            perm = p.objects.get(content_type = c.objects.get_for_model(Organization), object_id = self.organization.pk, perm_type = "A")#put the rest of the needed params to finish object perm
            return p.objects.get_perm_users(perm)


    def handle_actions_response(self, user):
        if self.admin_approve:
            return Organization, user
        else:
            return User, self.signee

    class Meta:
        abstract = True
