from django.contrib.contenttypes.models import ContentType

class  ActionResponse(object):

    @classmethod
    def construct(cls, action):
        involved =  cls.__det_ini(action, "initiate")
        if involved is None:
            return False
        query = action.content_object.handle_actions_queries()
        cls.__create_response(action, involved, query)
        return True


    #set out to those who need to respond

    @classmethod
    def __get_ini_functions(cls):
        from inspect import getmembers, isfunction
        from . import build_response_ini
        return getmembers(build_response_ini)

    @classmethod
    def __det_ini(cls, action, word):
        for i in cls.__get_ini_functions():
            if word in i[0]:
                if i[0].split("_")[1] == action.content_type.model_class().__name__.lower():
                    return i[1](action)
        return None

    @classmethod
    def __create_response(cls, action, involved, query):
        from .models import ResponseAction
        obj = ResponseAction.objects.create(content_type = ContentType.objects.get_for_model(action.__class__),\
                                        object_id = action.pk,\
                                        responded = False, \
                                      response_type = involved)
        obj.users.set(query)
        obj.linker.add(action)
        obj.save()

    def responses(self, action):
        return ContentType.objects.get_for_model(action.__class__).responses.filter(object_id = action.pk)

    def __has_res(self, action):
        print(f"list :{self.responses(action)} ")
        return (self.responses(action).count() > 0)

    def __det_res(self, action):
        return self.__class__.__det_ini(action, "respond")

    def __response_involved(self, action):
        for act in action.__class__.objects.filter(content_type = ContentType.objects.get_for_model(self.__class__), object_id = self.pk):
            if self.__has_res(act):
                for res in self.responses(act):
                    if not res.responded and action.user in res.users.all():
                        return res
        return -1


    def response_inquiry(self, user):
        return self.content_object.content_object.handle_actions_response(user)


#this will return what time of response is it in classes wether is user or org
    def handle_actions_response(self, user):
        pass

    def responding(self, action):
        from django.forms.models import model_to_dict

        if self.__det_res(action):
            print("so the call has been called here is wierd")
            response_builder = self.__response_involved(action)
            if response_builder != -1:
                from actions.signals import record_action_signal
                from actions.models import Record
                record_action_signal.send(sender = self.__class__,instance = self,  user = action.user, el = Record.RESPONDED)
                response_builder.responded = True
                response_builder.linker.add(action)
                response_builder.save()
