from rest_framework import serializers
from .models import WyzAddress, AddressBridge

class WyzAddressCreateSerializer(serializers.ModelSerializer):


    #def validate(self, data):
        # COMBAK:
        # TODO: have to provide a valid way of making sure address is validate
        #return super(WyzAddressCreateSerializer,self).validate(data)


    def create(self):
        return self.Meta.model.create(**self.validated_data)


    def create_and_assign(self, object):
        obj = self.create()
        AddressBridge.bridge(object, address)



    class Meta:
        model = WyzAddress
        exclude = ('location',)
