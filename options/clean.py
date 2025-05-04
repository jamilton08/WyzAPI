from django.contrib.contenttypes.models import ContentType

# REVIEW: this class is based on objects returning what they can do and not do
# XXX: for instance a bool will limit certain part of the program so will query and
# XXX: all the other so clean will be about removing them for objets and models in queries

class ObjectCleaner():
    # NOTE: this is in perspective of object itself holding its options
    options = None
    pool = list()
    affairs_retainers = ["queries", "bool", "select", "choice"]
    # NOTE: assign inner class to variable  options to not intefere with other initializers
    def __populate_inner(self):
        print("coming her ")
        self.options = self.Options(self)

    # NOTE: when you have an object this what you will use to populate so anything besides this will raise and assertion error
    def populate_options(self):
        self.formated_functions_dict()
        print(self.pool)
        self.__populate_inner()


    def get_options(self):
        return ContentType.objects.get_for_model(self.__class__).option_linkers.filter(object_id = self.pk)



    def get_all_functions(self):
        from inspect import getmembers, isroutine
        from importlib import import_module

        options_dict = {self.affairs_retainers[0]: [], self.affairs_retainers[1] : [], self.affairs_retainers[2] : [], self.affairs_retainers[3] : [] }
        for affairs, options in options_dict.items():
            mod  = f'.{affairs}'
            affair_module  = import_module(mod, package = "options.affairs" )
            for functions in getmembers(affair_module):
                if isroutine(functions[1]):
                    options_dict[affairs].append(functions[1])
        return options_dict

    def formated_functions_dict(self):
        global_options_retainer = self.get_all_functions()
        instance_options = self.get_options()
        for option in instance_options:
            options_instance = option.option_object
            for af in global_options_retainer[options_instance.get_affair_type]:
                print(options_instance.format_to_functional_name())
                if options_instance.format_to_functional_name() == af.__name__:
                    print("this")
                    instance, value  = self.get_option_values(option)
                    self.pool.append((af, instance, value))

        #for af_index in range(len(self.affairs_retainers)):
            #if af_index == 0:
            #    options_retainer[as]

    def get_option_values(self, option):
        instance = option.object
        return instance, option.option_object

    def factory(self, func):
        print("being called")
        from inspect import signature
        #assert '_call_function' in kwargs, "this could not continue without having a function"
            # NOTE: here we will store the values of func
        l1 = [func[1], func[2]]
        def f(*args, **kwargs):
            #if len(signature(func[0]).parameters) == len(func):
            from inspect import getcallargs
                # NOTE: make sure all the arguments provided are valid for the smber thats being asked by the function

                # NOTE: make sure all the arguments provided are valid for the smber thats being asked by the function
            if getcallargs(func[0], *l1, *args, **kwargs):
                print("is being calle")
                return func[0](*l1, *args, **kwargs)

        return f


    class Options():
        def __init__(self, outer):
            print(outer)
            self.outer = outer
            for options in self.outer.pool:
                print("running")
                function_name = options[0].__name__
                print(function_name)
                exec("%s = %s" % (f'self.{function_name}', 'self.outer.factory(options)'))
