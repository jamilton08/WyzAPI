from rest_framework import serializers
from notifications.models import Notification
from importlib import import_module as _i


class NotificationSerializer(serializers.ModelSerializer):
        senderType = serializers.SerializerMethodField('st')
        name = serializers.SerializerMethodField('nm')
        organizationName = serializers.SerializerMethodField('on')
        objectTranslate = serializers.SerializerMethodField('ot')
        objectPk= serializers.SerializerMethodField('opk')
        orgPk= serializers.SerializerMethodField('orpk')

        def st(self, bro):
            if hasattr(bro.actor, "response_type"):
                return  bro.actor.response_type == "O"
            else:
                return False

        def nm(self, bro):
            if hasattr(bro.actor.content_object, "user"):
                user = bro.actor.content_object.user
                return user.first_name + " " + user.last_name
            elif isinstance(bro.actor, _i("actions.models").PersonalRecord) :
                user = bro.actor.user
                return user.first_name + " " + user.last_name
            else:
                return "user"

        def on(self, bro):
             print(bro.actor.__class__)
             aff = None 
             if hasattr(bro.actor.content_object, "affiliation"):
                 aff = bro.actor.content_object.affiliation
                 print("are you heeeeere my guys oooooor upper level bro")
             elif isinstance(bro.actor, _i("actions.models").PersonalRecord) :
                 print("are you heeeeere my guys oooooor ")
                 aff = bro.actor.affiliation
                 
             if aff :
                 return aff.name
             else:
                 #for now this is the handlement of incase theres not pk with the frontend but musg modify front end to handle it
                 return "no attached org"

        def orpk(self, bro):
            
             aff = None
             if hasattr(bro.actor.content_object, "affiliation"):
                 aff = bro.actor.content_object.affiliation
             elif isinstance(bro.actor, _i("actions.models").PersonalRecord) :
                 print("are you heeeeere my guys oooooor ")
                 aff = bro.actor.affiliation
                 
             if aff :
                 return aff.pk
             else:
                 #for now this is the handlement of incase theres not pk with the frontend but musg modify front end to handle it
                 return 0

        def ot(self, bro):
            return bro.action_object.__class__.notification_string()

        def opk(self, bro):
            return int(bro.action_object_object_id)


        class Meta:
            model = Notification
            fields = ('unread','pk', 'verb', 'senderType', 'name', 'organizationName', 'objectTranslate', 'objectPk','orgPk',)
