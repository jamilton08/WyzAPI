class TaskTimable(object):
    time_m = None

    def _get_parent_instance(self):
        if self.time_m is not None:
            return getattr(self, self.time_m)
        else:
             return None


    def _sentinel(self):
        return getattr(self._get_parent_instance(), "time_m" )== None 


    def get_top_level(self):
        if self._sentinel():
            return self._get_parent_instance()
        else:
            return self._get_parent_instance().get_top_level()

    @classmethod
    def no_parent_perm_name(cls, instance):
        return f'{instance.__class__.__name__}_{instance.name}'


    @classmethod
    def has_parents(cls, instance):
        return bool(cls in instance.__class__.__bases__)

    @classmethod
    def is_top_level(cls, instance):
        return not hasattr(instance, "time_m")

    def get_time(self):
        time = self.get_top_level()
        times = list()
        times.append(time.start_time)
        times.append(time.end_time)
        return times
