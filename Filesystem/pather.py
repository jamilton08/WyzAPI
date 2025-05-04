

class PathGenerator(object):
    @classmethod
    def __valid_tuple(cls,tup):
        assert type(tup) == tuple, "needs to have tuples"
        assert len(tup) == 2, "tupple is not the size it should be"

    @classmethod
    def __has_field(cls,field,  val):
        assert hasattr(field, val), "must be a feild that returns a value"

    @classmethod
    def __valid_field_type(cls, t):
        assert t == int or t == str or t == float, "it can be a data type besides those"

    @classmethod
    def __valid_list_path(cls, path_pattern):
        assert type(path_pattern) == list, "if you will add values it needs to be a list"


    @classmethod
    def __check_for_feild(cls,instance, value):
        print(instance.__class__.__dict__)
        if value[0] in instance.__class__.__dict__:
            print("are you here bro")
            field = getattr(instance, value[0])
            cls.__has_field(field, value[1])
            append_val = getattr(field, value[1])
            t = type(append_val)
            cls.__valid_field_type(t)
            return append_val
        else:
            return value[0]
    @classmethod
    def pattern_gather(cls,instance, filename):
        pattern = instance.__class__.path_pattern
        cls.__valid_list_path(pattern)
        appender = ""
        for path in pattern:
            appender = f'{appender}/{cls.__check_for_feild(instance, path)}'
        return f'images/{appender}/{filename}'
