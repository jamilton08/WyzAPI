from django.db import models

#class Generator(models.Model):
#    gmail = models.OneToOneField(OrgEmailField,on_delete = models.CASCADE, related_name='teacher_email', unique = True)
#    password = models.CharField(max_length = 60)
#
#class OrgEmailField(models.Model):
#    username = models.CharField()
#    domain_name = models.CharField()
#    extension = models.CharField()

#    constraints = [
#        models.UniqueConstraint(
#            fields=["username", "domain_name", "extension"],
#            name='provide unique services for reciever'
#        )
#    ]
#
#class StudentReportModel(models.Model):
#    first_name= models.CharField()
#    last_name = models.CharField()
#    send_to = models.ManyToManyField(OrgEmailField, related_name = "stu_emal")
