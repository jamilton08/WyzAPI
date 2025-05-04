from rest_framework import serializers
from .models import ResponseAction

class ResponseSerializer(serializers.ModelSerializer):

    #object_show = serializers.SerializerMethodField('obj')
    object = serializers.SerializerMethodField('n')
    contentAsName = serializers.SerializerMethodField('content')

    #def em(self, bro):
        #instance = EmailSerializer(bro.emails.all(), many=True)
        #return instance.data
        # TODO: will have to implement something that returns objects based on content object

    def n(self, obj):
        return obj.content_object.content_object.__class__.__name__.lower()

    def content(self, obj):
        return obj.content_type.model_class().__name__



    class Meta:
        model = ResponseAction
        fields = ( 'pk', 'object', 'object_id', 'contentAsName')
