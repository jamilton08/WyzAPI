from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

# Create your models here.

class TaskAbstractModel(models.Model):
    name = models.SlugField(unique = True)
    responsibility = models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name='permed_model')
    dependecies = models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name='dependent')
    resolutions = models.ForeignKey(ContentType, on_delete = models.CASCADE, related_name='resolves')

    def  _is_service(self):
        from services.models import ServiceClass
        if self.responsibility.all().count() > 1:
            return False;
        return (self.responsibility.get().model_class == ServiceClass)

    def is_perm_class(self, cl):
        return hasattr(cl, "priority_parent")

    #def valid_responsibilities(self):
        #for r in self.responsibility.all()

    def perform_task(self, func):
        import inspect
        self.assert_(callable(func), 'you must submit a function for this')





class TaskModel(models.Model):
    pointer = models.ForeignKey(TaskAbstractModel, on_delete = models.CASCADE, related_name ='abstract')
    name = models.SlugField()


    def get_inject_func():
        import importlib
        mod = importlib.import_module("task.task_executors")
        func = getattr(mod, f'{self.name}_task')

    def _get_vars_list():
        b = dict()
        for i in self.pointer.all():
            b[i.name] = i
        return b

    def _validate_all_dependecies(self, **kwargs):
        checked = set()
        b = self._get_vars_list()
        for key in kwargs:
            self.assert_(key in b , "all keys  must be included in wanted value")
            checked.add(key)
        self.assert_(len(b) == len(checked), "the values you have do not matchup")
        return b


    def fill_dict(**kwargs):
        dic = self.validate_all_dependecies(**kwargs)
        for key in kwargs:
            dic[key] = dic[key].get_value(kwargs[key])
        return dic

    def class_of_res(self, responsibilities):
        from django.contrib.contenttypes.models import ContentType
        self.assert_(type(responsibilities) == type(list()), "responsibilites must come as list")
        for i in responsibility:
            self.assert_(ContentType.objects.filter(model = i.__class__) in self.pointer.responsibility.all())

    def class_of_reso(self, resolutions):
        from django.contrib.contenttypes.models import ContentType
        self.assert_(type(resolutions) == type(list()), "responsibilites must come as list")
        for i in resolutions:
            self.assert_(ContentType.objects.filter(model = i.__class__) in self.pointer.resolutions.all())

    def get_function_resource(self,resolutions, responsibilites, **kwargs):
        self.class_of_res(responsibilites)
        self.class_of_reso(resolutions)
        f = self.get_func()
        f(get_fun)

class TaskCall(models.Model):
    kind = models.ForeignKey(TaskModel,on_delete = models.CASCADE, related_name='calls')
    resolved = models.BooleanField()
    users = models.ManyToManyField(User, related_name ="task_do")

    @classmethod
    def get_resolve_pool(cls, name, responsibility):
        task = TaskModel.objects.get(name = name)
        f = task.get_inject_func()
        user , task_obj= f(responsibility)
        obj = cls.objects.create(kind = task, users = user)


class Attr_Dependecies_Model(models.Model):
    cl= models.ForeignKey(ContentType ,on_delete = models.CASCADE, related_name='dependers')
    attr = models.CharField(max_length = 30)

    def can_create(self, attr):
        return  attr in self.cl.model_class().__dict__

    def is_class(self, obj):
        return obj.__class__  == self.cl.model_class()

    def get_object(self, pk):
        return self.cl.model_class().objects.get(pk = pk)

    def get_value_class(self, val):
        return elf.cl.model_class.get(pk = val)
    def get_value(self):
        return getattr(self.get_value_class(), self.attr)
