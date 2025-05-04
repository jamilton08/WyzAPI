from importlib import import_module as _i

def add_days_of_week():
    d = _i("tiempo.models").DaysOfWeek
    daysDict = list()
    daysDict.append({"name" : "Sunday", "day_of_week" : 0})
    daysDict.append({"name" : "Monday", "day_of_week" : 1})
    daysDict.append({"name" : "Tuesday", "day_of_week" : 2})
    daysDict.append({"name" : "Wednesday", "day_of_week" : 3})
    daysDict.append({"name" : "Thursday", "day_of_week" : 4})
    daysDict.append({"name" : "Friday", "day_of_week" : 5})
    daysDict.append({"name" : "Saturday", "day_of_week" : 6})
    for day in daysDict:
     new_day = d.objects.create(**day)
     new_day.save()


def update_holidays():
   _i("tiempo.models").Holidays.add_holidays("US")
