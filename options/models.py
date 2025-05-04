from django.db import models
from django.contrib.contenttypes.models import ContentType
from .configuration import *
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.


# here are examples
class MainOptionBucket(models.Model):
    model_content = models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name = "options")
    # TODO: will be used to located the algoritm that will be applied to the model_contet as an object
    option_name = models.CharField(unique = True)
    option_content = models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name = "bucket")


class OptionBucketAbstract(models. Model):
    main_bucket = models.ForeignKey(MainOptionBucket, on_delete = models.CASCADE, related_name ='%(class)s_sub_bucket')

    def format_to_functional_name(self):
        return self.main_bucket.option_name.replace(" ", "_")

    get_affair_type = None


    def save(self, *args, **kwargs):
        ## TODO: make sure that the object being called for save is the same class as mainbucket so
        # XXX: make sure that self.__class__ == self.main_bucket.option_content.model_class()
        return super(OptionBucketAbstract, self).save()

    class Meta:
        abstract = True

#-------------------------------------------------- QUERY-OPTION-------------------------------------------------------------
# NOTE: this will be for queryoptions to hold the object that is limited in everyquery
class QuerySelect(models.Model):
    object_id = models.IntegerField()

    def retrieve_object(self):
        return self\
            .query_select_bucket.object_type\
            .model_class()\
            .objects.get(self.object_id)


# TODO:  create a class where it will read
class QueryOptionBucket(OptionBucketAbstract, models.Model):
    object_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='query_input_req')
    selected_limitaions = models.ManyToManyField(QuerySelect, related_name = "query_select_bucket")

    get_affair_type=  "queries"

    def get_pk_as_list(self):
        return self.selected_limitaions.all().values_list('object_id', flat = True)


#-------------------------------------------------- SELECT -------------------------------------------------------------

class SelectSelected(models.Model):
    name = models.CharField(unique = True)


class SelectOptionBucket(OptionBucketAbstract, models.Model):
    # NOTE: Here we have total options and from those options less sould be selected
    select_options = models.ManyToManyField(SelectSelected, related_name = 'selected_select_bucket')
    selected = models.ManyToManyField(SelectSelected, related_name = 'selects_selected')

    get_affair_type = "select"
    # NOTE: check if the selected one in on the options
    def selected_is_in_options(self):
        return obj in self.select_options.all()



    def add_option(self, obj):
        if self.selected_is_in_options():
            self.selected.add(obj)
            self.save()


#-------------------------------------------------- CHOICES -------------------------------------------------------------
class ChoicesSelect(models.Model):
    name = models.CharField(unique = True)

class ChoicesOptionBucket(OptionBucketAbstract, models.Model):
    # NOTE: Here we have total options and from those choices one sould be selected
    choices_options = models.ManyToManyField(SelectSelected, related_name = 'choices_select_bucket')
    selected = models.ForeignKey(SelectSelected, on_delete=models.CASCADE, related_name = 'choices_selected')

    get_affair_type =  "choice"
    # NOTE: check if the selected one in on the options
    def selected_is_in_options(self, obj):
        return obj in self.choices_options.all()

    def add_option(self, obj):
        if self.selected_is_in_options():
            self.selected = obj
            self.save()


    #-------------------------------------------------- BOOL -------------------------------------------------------------

class BoolOptionBucket(OptionBucketAbstract, models.Model):
    # NOTE: Here we have total options and from those options less sould be selected
    on = models.BooleanField(default = False)
    get_affair_type =  "bool"
    # NOTE: check if the selected one in on the options



# NOTE: this willl have all objects linked to their respective options
class OptionLinker(models.Model):
    option_content = models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name = "attached_options")
    option_id = models.IntegerField()
    object_content =  models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name = "option_linkers")
    object_id = models.IntegerField()
    option_object = GenericForeignKey('option_content', 'option_id')
    object = GenericForeignKey('object_content', 'object_id')


    # NOTE: every objects created should pass through this functions in order to link all its options to it
    @classmethod
    def options_linker(cls, obj):
        from itertools import chain
        # NOTE: object of the content to see which one were choosing to create its options
        content = ContentType.objects.get_for_model(obj.__class__)
        buckets = MainOptionBucket.objects.filter(model_content = content)
        for b in buckets :
            bucket_content = b.option_content.model_class()
            if bucket_content == QueryOptionBucket:
                general_bucket_instance = bucket_content.objects.create(main_bucket = b, object_type = query_mapper[b.option_name])
            elif bucket_content == BoolOptionBucket:
                general_bucket_instance = bucket_content.objects.create(main_bucket = b, on = bool_mapper[b.option_name])
            elif bucket_content == ChoicesOptionBucket:
                general_bucket_instance = bucket_content.objects.create(main_bucket = b, selected = choice_mapper[b.option_name])
            else:
                general_bucket_instance = bucket_content.objects.create(main_bucket = b)
            # NOTE: select and choices have specific string you have to choose from so they should be addressed before creating
            linker_dict = dict()
            linker_dict["object_content"] = content
            linker_dict["object_id"] = obj.pk
            linker_dict["option_content"] = ContentType.objects.get_for_model(general_bucket_instance.__class__)
            linker_dict["option_id"] = general_bucket_instance.pk
            cls.objects.create(**linker_dict)
