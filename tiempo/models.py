from django.db import models

from .utilities import *
from perms.utilities import FieldGen, ParentPriorityGenerator
from .managers import CopyDateTimeManager
from organizations.models import Organization, OrganizationUser
from django.core.validators import MaxValueValidator
from task.time_master import TaskTimable

class AbstractDateModel(models.Model):
    start_date =models.DateField()
    end_date =models.DateField()


    class Meta:
        abstract = True


class AbstractTimeModel(models.Model):
    start_date =models.DateField()
    end_date =models.DateField()


    class Meta:
        abstract = True

class SchedulingModel(models.Model):
    include_or_exclude = models.BooleanField()

    @classmethod
    def create(cls, days_list):
        sm = cls.objects.create(include_or_exclude = True)


        for d in range(len(days_list)):
            if days_list[d] == 1:
                DaysOfWeek.objects.get(day_of_week = d).schedule_holding.add(sm)
        return sm

    def get_list(self):
        l = list()
        for d in range(7):
            if self.days_of_week.filter(day_of_week = d).exists():
                l.append(1)
            else:
                l.append(0)
        return l

    def match_list(self, other_list):
        l = list()
        for (this, other) in zip(self.get_list(), other_list):
            if this == 1 and other == 1:
                l.append(1)
            else:
                l.append(0)
        return l
class Scheduling(models.Model):
    object_schedule = models.OneToOneField(SchedulingModel, on_delete = models.CASCADE, related_name = '%(class)s_retainer')



class WyzDateModel(ParentPriorityGenerator, AbstractDateModel, Scheduling, models.Model):
    name = models.CharField(max_length = 100)
    organization = models.ForeignKey(Organization, on_delete = models.CASCADE, related_name ='date_models')
    parent = models.ForeignKey('self', on_delete = models.CASCADE, related_name ='date_child', blank = True, null = True)
    priority_parent = FieldGen("organization")
    @classmethod
    def create(cls, *args, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def get_org_parent_date(cls, organization):
        return cls.objects.filter(organization = organization,parent__isnull = True ).order_by("start_date")

    @classmethod
    def get_date_org_frame(cls, org, d):
        from django.db.models import Q, F, Func
        from datetime import date
        from django.db.models.functions import ExtractDay

        ##get in between datas by org
        q1 = Q(organization = org)
        q2 = Q(start_date__lte = d)
        q3 = Q(end_date__gte = d)

        c = cls.objects.filter(q1 & q2 & q3)

        current_date = c.annotate(remaining_from_start = ExtractDay(d- F('start_date'))).annotate(remaining_from_end = ExtractDay(F('end_date') - d)).annotate(dist_between_days = Func(F('remaining_from_end'), function='ABS') + Func( F('remaining_from_start'), function='ABS')).order_by('dist_between_days')
        return current_date


    @classmethod
    def get_current_org_frame(cls, org):
        from datetime import date
        today = date.today()
        return cls.get_date_org_frame(org, today)

    @classmethod
    def date_conflicts(cls, parent, start, end):
        all_dates = parent.date_child.order_by('start_date').all()
        if all_dates.count() == 0:
            return True
        for x in all_dates:
            in_remaining = (start > x.end_date and end > x.end_date)
            if x == all_dates.first() or x == all_dates.last() :
                if ((start < x.start_date) and (end < x.start_date)) or in_remaining:
                     if ((start < x.start_date) and (end < x.start_date)):
                         return True
                     pass
                else:
                    return False
            else:
                if  (start > after_end  and  end < x.start_date) or in_remaining:
                    print(after_end)
                    print(x.start_date)
                    pass
                else:
                    return False

            after_end = x.end_date
        return True


    def get_neighbor_time(self) :
         from datetime import date as d
         #with validation start date and end date must be both be after today to even ru\n this script
         neighbors = self.parent.date_child.order_by('start_date').all()
         neighbors_l = list(neighbors)
         counter = 0
         empt = list()

         for n in neighbors:
             if n == self:
                 if counter == 0:
                    empt.append(n.parent.start_date if n.parent.start_date > d.today() else d.today())
                 else:
                    empt.append(neighbors_l[counter - 1].end_date if neighbors_l[counter - 1].end_date > d.today() else d.today())

                 if (counter + 1) == neighbors.count():
                     empt.append(n.parent.end_date)
                 else:
                     empt.append(neighbors_l[counter + 1].start_date)
             counter += 1
         return empt


    def shift(self, new_start_date):
         #left = 0
         #right = 1
         delta = new_start_date - self.start_date
         self.start_date = self.start_date + delta
         self. end_date = self.end_date + delta
         self.save()

    def extend(self, nsd, esd):
        self.start_date = nsd
        self.end_date = esd
        self.save()

    @classmethod
    def unconflict_dates(cls, parent):
        from datetime import time
        all_dates = parent.date_child.order_by('start_date').all()

        if all_dates.count() == 0:
            return [[parent.start_date, parent.end_date]]

        empt_list = list()
        empt_list.append([parent.start_date, all_dates.first().start_date])
        for x in all_dates:
            available_times = list()
            if x == all_dates.first():
                pass
            else:
                available_times.append(after_end)
                available_times.append(x.start_date)
            empt_list.append(available_times)
            after_end = x.end_date
        empt_list.append([all_dates.last().end_date, parent.end_date])
        return list(filter(None, empt_list))





    def get_timeframe(self):
        if self.time_frames.count == 0 and self.parent is not None:
            return self.parent.get_timeframe()
        else:
            return self.time_frames

    def within_date(self, date):
        return (date >= self.start_date and date <= self.end_date)
    
    
    def get_neighbors_object(self):
        return self.__class__.objects.filter(parent = self.parent)
    
    def get_childs(self):
        return self.__class__.objects.filter(parent = self).order_by('start_date')
    
    def structurize(self, l, level, serializer):
        if len(l) < level:
            l.append(list())
        l[level -1].append(serializer(self).data)
        for child in self.get_childs():
            child.structurize(l,level+1, serializer)

            
        

class WyzTimeModel(Scheduling, ParentPriorityGenerator, TaskTimable, models.Model):
    name = models.CharField(max_length = 100)

    dates = models.ForeignKey(WyzDateModel, on_delete = models.CASCADE, related_name ='time_frames')
    start_time =models.TimeField()
    end_time =models.TimeField()
    priority_parent = FieldGen("dates")
    time_m = None

     ##determine date object based program
    @classmethod
    def get_coflict_instance(cls, dates_obj):
        return  dates_obj.time_frames.all().order_by('start_time')

    @classmethod
    def valid_time(cls, dates_obj, start, end):
            times = cls.get_coflict_instance(dates_obj)
            if times.count() == 0:
                return True
            for x in times.all():
                not_in_remaining = (start > x.end_time and end > x.end_time)
                if x == times.first() or x == times.last() :
                    if ((start < x.start_time) and (end < x.start_time)) or not_in_remaining:
                        if ((start < x.start_time) and (end < x.start_time)):
                            return True
                        pass
                    else:
                       return False
                else:
                    if not (start > after_end  and  end < x.start_time) or not_in_remaining:
                        return False

                after_end = x.end_time
            return True


    @classmethod
    def unconflict_times(cls, dates_obj):
        from datetime import time
        times = cls.get_coflict_instance(dates_obj)
        if times.count() == 0:
            return [[time.min, time.max]]
        empt_list = list()
        empt_list.append([time.min, times.first().start_time])
        for x in times.all():
            available_times = list()
            if x == times.first():
                pass
            else:
                available_times.append(after_end)
                available_times.append(x.start_time)
            empt_list.append(available_times)
            after_end = x.end_time
        empt_list.append([times.last().end_time, time.max])
        return list(filter(None, empt_list))

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def get_current_period(cls, org):
        from datetime import datetime as dt
        from django.db.models import Q
        current_date_obj = WyzDateModel.get_current_org_frame(org).first()
        print(current_date_obj, dt.now().time())
        all_times = cls.objects.filter(dates = current_date_obj)
        for i in all_times:
            print(i)
        f = all_times.filter(Q(start_time__lte= dt.now().time()) & Q(end_time__gte= dt.now().time()))
        return f.first() if f.count() > 0 else None

    def get_neighbor_time(self) :
         from datetime import date as d
         from datetime import time as t
         #with validation start date and end date must be both be after today to even ru\n this script
         neighbors = self.dates.time_frames.order_by('start_time').all()
         neighbors_l = list(neighbors)
         counter = 0
         empt = list()

         for n in neighbors:
             if n == self:
                 if counter == 0:
                    empt.append(t.min)
                 else:
                    empt.append(neighbors_l[counter - 1].end_time)

                 if (counter + 1) == neighbors.count():
                     empt.append(t.max)
                 else:
                     empt.append(neighbors_l[counter + 1].start_time)
             counter += 1
         return empt

    def move_time(self, new_start):
        from .utilities import seconds_convert
        start = seconds_convert(new_start)
        delta = start - seconds_convert(self.start_time)
        end = seconds_convert(self.end_time) + delta
        return time_convert(end)

    def within_time(self, time):
        return (time >= self.start_time and time <= self.end_date)

    def accepted_time_frame(self, dt):
        time = dt.time()
        date = dt.date()
        wk = date.weekday()
        return self.dates.within_date(date) and self.within_time() and self.object_schedule.filter(days_of_week = wk).exists()




class DateTimeCopyBoard(models.Model):
        org_user = models.OneToOneField(OrganizationUser, on_delete = models.CASCADE, related_name ='date_clipboard')
        isdate = models.IntegerField(
            validators=[
                MaxValueValidator(2)
            ]
         )
        created = models.DateTimeField(auto_now_add=True)
        object_pk = models.IntegerField()

        objects = CopyDateTimeManager()

        def get_instance(self):
            if self.isdate == 0:
                return WyzDateModel.objects.get(pk = self.object_pk)
            elif  self.isdate == 1:
                return WyzTimeModel.objects.get(pk = self.object_pk)
            elif self.isdate == 2:
                return WyzFloatModel.objects.get(pk = self.object_pk)




        def pastable_copy_details(self):
            mode = self.get_instance()
            if self.isdate ==   0:
                return diff_in_days(mode.start_date, mode.end_date)
            else:
                return seconds_convert(mode.end_time) - seconds_convert(mode.start_time)


        def paste(self, obj, start, clipboard):
            delta = self.pastable_copy_details()
            instance = self.get_instance()
            c_instance_sche = clipboard.object_schedule.get_list()
            p_instance_sche_list = obj.object_schedule.match_list(c_instance_sche)
            p_sche = SchedulingModel.create(p_instance_sche_list)
            p_sche.save()
            clipboard_type = clipboard.__class__
            if clipboard_type == WyzDateModel:
                print("is it here ")
                start_date, end_date = shift_to_today(delta, start)
                if not WyzDateModel.date_conflicts(obj, start_date, end_date):
                    pass
                    #will push for actions
                w = WyzDateModel.objects.create(parent = obj, start_date = start_date, end_date = end_date, organization = instance.organization, object_schedule = p_sche)
                w.save()
            elif clipboard_type == WyzTimeModel:
                start_time = seconds_convert(start)
                end_time = start_time + delta
                st_c = start
                et_c = time_convert(end_time)

                WyzTimeModel.objects.create(dates = obj, start_time = st_c, end_time = et_c, object_schedule = p_sche)

            elif clipboard_type == WyzFloatModel:
                start_time = seconds_convert(start)
                end_time = start_time + delta
                st_c = start
                et_c = time_convert(end_time)
                dur =  WyzFloatModel.convert_to_minutes(et_c, st_c)
                w = WyzFloatModel.objects.create(dates = obj, start_time = st_c, end_time = et_c, duration = dur, name = obj.name, organization = obj.organization, object_schedule = p_sche )
                w.save()




class WyzFloatModel(Scheduling, ParentPriorityGenerator, TaskTimable, models.Model):
    name = models.CharField(max_length = 100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.PositiveSmallIntegerField()
    organization = organization = models.ForeignKey(Organization, on_delete = models.CASCADE, related_name ='float_models')
    dates = models.ForeignKey(WyzDateModel, on_delete = models.CASCADE, related_name ='floating_models')
    priority_parent = FieldGen("dates")
    time_m = None

    @classmethod
    def get_end_time(cls, start_time, duration):
        from .utilities import time_convert, seconds_convert
        return time_convert(seconds_convert(start_time) + duration * 60)
    @classmethod
    def convert_to_minutes(cls, end_time, start_time):
        from .utilities import time_convert
        return (seconds_convert(end_time) - seconds_convert(start_time)) / 60

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.objects.create(**kwargs)

    def move_time(self, new_start):
        from .utilities import seconds_convert
        start = seconds_convert(new_start)
        delta = start - seconds_convert(self.start_time)
        end = seconds_convert(self.end_time) + delta
        return time_convert(end)

    def within_time(self, time):
        return (time >= self.start_time and time <= self.end_date)

    def accepted_time_frame(self, dt):
        time = dt.time()
        date = dt.date()
        wk = date.weekday()
        return self.dates.within_date(date) and self.within_time() and self.object_schedule.filter(days_of_week = wk).exists()




class DaysOfWeek(models.Model):
    name = models.CharField(max_length = 9, unique = True)
    day_of_week = models.IntegerField(unique = True)
    schedule_holding = models.ManyToManyField(SchedulingModel, related_name = "days_of_week")
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "day_of_week"], name='every day of the week should be unique')
            ]


class Holidays(models.Model):
    name = models.CharField()
    date = models.DateField()
    schedule_holding = models.ManyToManyField(SchedulingModel, related_name = "holidays")
    @classmethod
    def add_holidays(cls, country):
        import datetime as d
        import holidays
        year = (d.date.today() + d.timedelta(days = 365)).year
        for date, name in sorted(getattr(holidays, country)(years = year).items()):
            h = cls.objects.create(name = name, date = date)
            h.save()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "date"], name='every holiday has its own day')
            ]
