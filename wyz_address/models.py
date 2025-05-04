from django.db import models
from django.contrib.auth.models import User
from organizations.models import Organization
from django.contrib.gis.db import models as g_models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class WyzAddress(models.Model):
    location = g_models.PointField(unique = True)
    address = models.CharField(max_length=100, unique = True)

    @classmethod
    def create(cls, **kwargs):
        from global_utilities.geo import get_map_coors
        from django.contrib.gis.geos import Point
        # NOTE:  will check if it exists if not it will create
        a = kwargs['address']
        points = Point(get_map_coors(a))
        kwargs.update({'location': points})
        if cls.objects.filter(**kwargs).exists():
            obj = cls.objects.filter(**kwargs).first()
        else:
            obj = cls.objects.create(**kwargs)
            obj.save()
        return obj

class AddressBridge(models.Model):
    address = models.ForeignKey(WyzAddress, on_delete = models.CASCADE, related_name ='bridge', blank = True, null = True)
    content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='addresses')
    object_id = models.IntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    allowed_contents = [Organization, User]

    @classmethod
    def bridge(cls, obj, address):
        from django.contrib.contenttypes.models import ContentType
        assert_(obj.__class__ in cls.content_object, 'must be withingn allowed contents list')
        b = dict()
        b['content_type'] = ContentType.objects.get_for_model(obj)
        b['object_id'] = obj.pk
        b['address'] = address

        bridge = cls.objects.create(**b)
        bridge.save()
