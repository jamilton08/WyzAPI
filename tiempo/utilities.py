import datetime as d

def diff_in_days(date1, date2):
    if date2 < date1:
        raise TypeError("not good, miust be the other way around")
    return date2 - date1

def shift_to_today(date_delta, chosen_day):
    if chosen_day < d.date.today():
        return date.today(), date.today() + date_delta
    else:
        return chosen_day, chosen_day + date_delta

def seconds_convert(tiempo):
    if not type(tiempo) == d.time:
        raise TypeError("this must be something that time field or something.. come check")
    return ((tiempo.hour) * (60**2)) + (tiempo.minute*60) + tiempo.second

def time_convert(seconds):
        hours = int(seconds / (60**2))
        seconds = seconds % (60**2)
        minutes = int(seconds / 60)
        seconds = seconds % 60

        return d.time(hours, minutes, seconds)

def get_total_available_days(date_obj):

    before_today_s = bool(date_obj.start_date < d.date.today())
    after_today_s = bool(date_obj.start_date > d.date.today())
    before_today_e = bool(date_obj.end_date < d.date.today())
    after_today_e = bool(date_obj.end_date > d.date.today())
    if  before_today_s and before_today_e:
        return 0
    elif after_today_s and after_today_e:
        return diff_in_days(date_obj.start_date, date_obj.end_date).days
    else:
        return diff_in_days(d.date.today(), date_obj.end_date).days


def get_remaining_days(parent):
    from .models import WyzDateModel
    total = 0
    for days in WyzDateModel.unconflict_dates(parent):
        if days[0] < d.date.today()  and days[1]< d.date.today():
            total+= 0
        elif days[0] < d.date.today():
            total += diff_in_days(d.date.today(), days[1]).days
        else:
            total += diff_in_days(days[0], days[1]).days
    return total


def get_acceptable_index(days_obj, new_sche):
    from .models import DaysOfWeek
    s = list()
    for i in range(7):
        if new_sche[i] == 1 and not days_obj.object_schedule.days_of_week.filter(day_of_week = i).exists():
            s.append(DaysOfWeek.objects.get(day_of_week = i).name)
    return s


def date_clash(d1, d2):
    x1 = d1.start_date
    y1 = d1.end_date
    x2 = d2.start_date
    y2 = d2.end_date

    c1 = (x1 >= x2 and x1 <= y2)
    c2 = (y1 >= x2 and y1 <= y2)
    c3 = (x2 >= x1 and x2 <= y1)
    c4 = (y2 >= x1 and y2 <= y1)

    return (c1 or c2 or c3 or c4 )

def matches_days(t1,t2):
    s1 = t1.object_schedule
    s2 = t2.object_schedule
    return s1.days_of_week.filter(pk__in = s2.days_of_week.all()).exists()
