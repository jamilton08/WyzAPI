from rest_framework import serializers
from django.contrib.auth.models import User
from .models import WyzDateModel, WyzTimeModel, DateTimeCopyBoard, WyzFloatModel
import datetime as d

class CreateWyzDateSerializer(serializers.ModelSerializer):

    include_or_exclude = serializers.BooleanField()
    days = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=1))


    def validate(self, data):
        start = data['start_date']
        end = data['end_date']

        if end <  start:
            raise serializers.ValidationError("end time should be greater then start time")
        if start < d.date.today():
            raise serializers.ValidationError("you can create this for the past")
        try:
            parent = data['parent']
            if not start >= parent.start_date or not end <= parent.end_date:
                raise serializers.ValidationError("you most be within the borders of the parent")
            if not self.Meta.model.date_conflicts(parent, start, end):
                raise serializers.ValidationError("conflict with a certain date")
        except KeyError:
            pass
        if len(data['days']) != 7:
            raise serializers.ValidationError("can only create for 6 dayss")

        return super(CreateWyzDateSerializer, self).validate(data)

    def create(self):
        from .models import SchedulingModel, DaysOfWeek

        i= self.validated_data.pop('include_or_exclude')
        e = self.validated_data.pop('days')

        sm = SchedulingModel.objects.create(include_or_exclude = i)

        self.validated_data.update({'object_schedule' : sm})

        for d in range(len(e)):
            if e[d] == 1:
                DaysOfWeek.objects.get(day_of_week = d).schedule_holding.add(sm)


        return self.Meta.model.create(**self.validated_data)

    class Meta:
        model = WyzDateModel
        exclude = ('object_schedule', )

class CreateWyzTimeSerializer(serializers.ModelSerializer):
    days = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=1))

    def validate(self, data):
        from .utilities import get_acceptable_index
        start = data['start_time']
        end = data['end_time']
        dates = data['dates']
        l = get_acceptable_index(dates, data['days'])

        if end <  start:
            raise serializers.ValidationError("end time should be greater then start time")

        if not self.Meta.model.valid_time(dates, start, end):
            raise serializers.ValidationError("time must be between hours that arent taken")

        if len(data['days']) != 7:
            raise serializers.ValidationError("can only create for 7 dayss")
        empt = ""
        if bool(l):
            for i in range(len(l)):
                if i != len(l) - 1:
                    empt += f' {l[i]},'
                else:
                    empt += f' {l[i]}'
            raise serializers.ValidationError(f'{empt} days, cant be chosen')


        return super(CreateWyzTimeSerializer, self).validate(data)

    def create(self):
        from .models import SchedulingModel, DaysOfWeek

        e = self.validated_data.pop('days')

        sm = SchedulingModel.objects.create(include_or_exclude = True)

        self.validated_data.update({'object_schedule' : sm})

        for d in range(len(e)):
            if e[d] == 1:
                DaysOfWeek.objects.get(day_of_week = d).schedule_holding.add(sm)
        return self.Meta.model.create(**self.validated_data)

    class Meta:
        model = WyzTimeModel
        exclude = ('object_schedule', )



class CopyDateTimeSerializer(serializers.ModelSerializer):

    def create(self):
        return self.Meta.model.objects.create(**self.validated_data)

    class Meta:
        model = DateTimeCopyBoard
        fields = '__all__'


class PasteDateTimeSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self.clipboard = kwargs.pop('clipboard')
        super(PasteDateTimeSerializer, self).__init__(*args, **kwargs)

        if self.clipboard.isdate == 0:
            self.fields.update({'start': serializers.DateField()})
        else:
            self.fields.update({'start': serializers.TimeField()})
        print(self.fields)

    object_pk = serializers.IntegerField()


    def validate(self, data):
        from .utilities import get_total_available_days as gta, diff_in_days as dia, get_remaining_days as grd, shift_to_today as stt\
        , seconds_convert as sc, time_convert as tp
        date_obj = WyzDateModel.objects.get(pk = data['object_pk'])

        if self.clipboard.isdate == 0:
            delta = dia(self.clipboard.get_instance().start_date, self.clipboard.get_instance().end_date )
            if data['start'] < d.date.today():
                raise serializers.ValidationError("you cant start from tnbe past, is already defined")
            if data['start'] > date_obj.start_date and data['start'] > date_obj.end_date:
                raise serializers.ValidationError("bro you messed up right here too cause this in the past")
            if gta(date_obj) < delta.days:
                raise serializers.ValidationError("copied object should not have more day then parent after today, should extend")
            if delta.days > grd(date_obj):
                raise serializers.ValidationError("you dont have enough spac to fit this object, you might need to expand")
            start, end = stt(delta, data['start'])
            if not WyzDateModel.date_conflicts(date_obj, start, end ):
                raise serializers.ValidationError('you might have to shift a few objects around to fit this one in')

        if self.clipboard.isdate == 1:
            delta = self.clipboard.pastable_copy_details()
            start = data['start']
            if not WyzTimeModel.valid_time(date_obj, start, tp(sc(start) + delta)) :
                raise serializers.ValidationError("is clashing with other times")
        return super(PasteDateTimeSerializer, self).validate(data)


    def paste(self):
        obj = WyzDateModel.objects.get(pk = self.validated_data['object_pk'])
        start = self.validated_data['start']
        self.clipboard.paste(obj, start, self.clipboard.get_instance())

    class Meta:
        fields = '__all__'


class DateShiftSerializer(serializers.Serializer):
    new_start_date = serializers.DateField()
    object_pk = serializers.IntegerField()

    def validate(self, data):
        from .utilities import diff_in_days
        dm = WyzDateModel.objects.get(pk = data['object_pk'])
        borders = dm.get_neighbor_time()

        if dm.start_day < d.date.today():
            raise serializers.ValidationError("could not shift something with things in the past, consider extenting it ")
        if data['new_start_date'] < d.date.today():
            raise serializers.ValidationError("could not shift before the past ")
        if data['new_start_date'] < borders[0] or (diff_in_days(dm.start_date, dm.end_date) + data['new_start_date']) > border[1]:
            raise serializers.ValidationError("your doing over boundaries, must delete or move neighbor dateframess")
        if dm.parent is not None:
            if data['new_start_date'] <  dm.parent.start_date:
                raise serializers.ValidationError("could not go past parent start time restrictions")
            if (diff_in_days(dm.start_date, dm.end_date) + data['new_start_date']) > dm.parent.end_date:
                raise serializers.ValidationError("could not go past parent end  time restrictions")

    def update(self):
        d = WyzDateModel.objects.get(pk = self.validated_data['object_pk'])
        d.shift(self.validated_data['new_start_date'])


class TimeShiftSerializer(serializers.Serializer):
    new_start_time = serializers.TimeField()
    object_pk = serializers.IntegerField()

    def validate(self, data):
        dm = WyzTimeModel.objects.get(pk = data['object_pk'])
        borders = dm.get_neighbor_time()
        start = data['new_start_time']
        end = dm.move_time(start)

        if start < borders[0]:
            raise serializers.ValidationError("could not go before you for neighbor to the left ")
        if end > borders[1]:
            raise serializers.ValidationError("could not shift before the past ")
        return super(TimeShiftSerializer, self).validate(data)

    def update(self):
        start = self.validated_data['new_start_time']
        d = WyzTimeModel.objects.get(pk = self.validated_data['object_pk'])
        end = d.move_time(start)
        d.start_time = start
        d.end_time = end
        d.save()

class FloatShiftSerializer(serializers.Serializer):
    new_start_time = serializers.TimeField()
    object_pk = serializers.IntegerField()

    def update(self):
        start = self.validated_data['new_start_time']
        d = WyzFloatModel.objects.get(pk = self.validated_data['object_pk'])
        end = d.move_time(start)
        d.start_time = start
        d.end_time = end
        d.save()


class DateExtendSerializer(serializers.Serializer):
    new_start_date = serializers.DateField()
    object_pk = serializers.IntegerField()
    new_end_date = serializers.DateField()

    def validate(self, data):
        from .utilities import diff_in_days
        dm = WyzDateModel.objects.get(pk = data['object_pk'])

        if data['new_start_date'] < d.date.today():
            raise serializers.ValidationError("could not extend past today ")
        if dm.end_date < d.date.today():
            serializers.ValidationError("you cant work with something thats in the past")
        if dm.parent is not None:
            borders = dm.get_neighbor_time()
            if data['new_start_date'] < borders[0]:
                raise serializers.ValidationError(f'cant go behind the date  of {borders[0]}')
            if data['new_end_date'] > borders[1]:
                raise serializers.ValidationError(f'cant go beyond the date  of {borders[1]}')
        return super(DateExtendSerializer, self).validate(data)


    def update(self):
        data = self.validated_data
        d = WyzDateModel.objects.get(pk = data['object_pk'])
        d.extend(data['new_start_date'], data['new_end_date'])


class TimeExpandSerializer(serializers.Serializer):
    new_start_time = serializers.TimeField()
    object_pk = serializers.IntegerField()
    new_end_time = serializers.TimeField()

    def validate(self, data):
        dm = WyzTimeModel.objects.get(pk = data['object_pk'])
        borders = dm.get_neighbor_time()
        start = data['new_start_time']
        end =   data['new_end_time']

        if start < borders[0]:
            raise serializers.ValidationError("could not go before you for neighbor to the left ")
        if end > borders[1]:
            raise serializers.ValidationError("could not shift before the past ")
        return super(TimeExpandSerializer, self).validate(data)

    def update(self):
        start = self.validated_data['new_start_time']
        d = WyzTimeModel.objects.get(pk = self.validated_data['object_pk'])
        end = self.validated_data['new_end_time']
        d.start_time = start
        d.end_time = end
        d.save()

class FloatExpandSerializer(serializers.Serializer):
    new_start_time = serializers.TimeField()
    object_pk = serializers.IntegerField()
    new_end_time = serializers.TimeField()

    def update(self):
        start = self.validated_data['new_start_time']
        d = WyzFloatModel.objects.get(pk = self.validated_data['object_pk'])
        end = self.validated_data['new_end_time']
        d.start_time = start
        d.end_time = end
        d.save()


class CreateWyzFloatSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)


        # Instantiate the superclass normally
        super(CreateWyzFloatSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            remove = list(fields)



            for field_name in remove:

                self.fields.pop(field_name)

    days = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=1))

    @classmethod
    def remove_unused_feild(cls, data):
        field_set = set(cls.Meta.fields)
        data_set = set()
        for key in data:
            data_set.add(key)
        return field_set - data_set

    def validate(self, data):
        print(data)
        from .utilities import get_acceptable_index, time_convert, seconds_convert


        start = data['start_time']
        if 'duration' in data:
            end = time_convert(seconds_convert(data['start_time']) + data['duration'] * 60)
        else:
            end = data['end_time']
        dates = data['dates']
        l = get_acceptable_index(dates, data['days'])

        if end <  start:
            raise serializers.ValidationError("end time should be greater then start time")

        if len(data['days']) != 7:
            raise serializers.ValidationError("can only create for 7 dayss")
        empt = ""
        if bool(l):
            for i in range(len(l)):
                if i != len(l) - 1:
                    empt += f' {l[i]},'
                else:
                    empt += f' {l[i]}'
            raise serializers.ValidationError(f'{empt} days, cant be chosen')
        return super(CreateWyzFloatSerializer, self).validate(data)

    def create(self):
        from .models import SchedulingModel, DaysOfWeek
        d = self.validated_data

        e = d.pop('days')

        sm = SchedulingModel.objects.create(include_or_exclude = True)

        d.update({'object_schedule' : sm})

        if 'duration' in d:
            d.update({'end_time': self.Meta.model.get_end_time(d['start_time'], d['duration'])})
        else:
            d.update({'duration': self.Meta.model.convert_to_minutes(d['end_time'], d['start_time'])})

        for f in range(len(e)):
            if e[f] == 1:
                DaysOfWeek.objects.get(day_of_week = f).schedule_holding.add(sm)
        return self.Meta.model.create(**d)


    class Meta:
        model = WyzFloatModel
        fields = ('start_time', 'end_time', 'duration', 'dates', 'organization', 'name', 'days' )

#class CreateScheduleSerializer(serializers.Serializer):

class WyzDateModelSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(format="%m/%d/%Y")
    end_date = serializers.DateField(format="%m/%d/%Y")

    days_configuration = serializers.SerializerMethodField('config')


    
    def config(self, bro):
        l = list()
        for i in range(7):
            l.append(int(bro.object_schedule.days_of_week.filter(day_of_week = i).exists()))
            print(bro.object_schedule.days_of_week.filter(day_of_week = i))
        return l

    class Meta:
        model = WyzDateModel
        fields = ('start_date', 'end_date', 'name', 'pk', 'days_configuration' )

class WyzTimeModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = WyzTimeModel
        fields = '__all__'

class WyzFloatModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = WyzFloatModel;
        fields = '__all__'
