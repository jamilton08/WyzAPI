from threading import Lock
from time import sleep
from .models import TaskAbstractModel, TaskCall

current_tasks = list()
dispatch_5 = dict()
dispatch_5['attendance'] = list()
dispatch_2 = dict()
dispatch_2['attendance'] = list()
dispatch_1 = dict()
dispatch_1['attendance'] = list()
dispatch_s = dict()
dispatch_s['attendance'] = list()

r_task = dict()


# REVIEW: the point of this file is to take list every 10 minutes, 5 minmutes, 2 minutes and 1 minute and pass down the
# XXX: Tthe task until it becomes executable at a specific time
#this will onclude a queryset of current current_tasks

def task_d_5(lock):
    from .managers import TimeDetectQuery
    obj = TimeDetectQuery()
    # function to print cube of given num
    while True:
        with lock:
             for method in dir(TimeDetectQuery):
                 # NOTE: will look for all dispatch instances
                 if method.split("_")[1] == "dispatch":
                     name = method.split("_")[0]
                     print(name)
                     # NOTE: ill get the model
                     tam = TaskAbstractModel.objects.get(name = name)
                     res = tam.responsibility.model_class()
                     dep = dep.dependecy.model_class()
                     dispatch_5[method] = list(chain(getattr(obj, f'dispatch_{method}')(res, dep), dispatch_5[method]))
        sleep(60*10)

def task_d_2(lock):
    current_eval = None
    while true:
        with lock:
            now = datetime.now().time()
            for key, value in dispatch_5.items():
                for task_needed in value:
                    current_eval = task_needed.get_time()[0]
                    if current_eval.hour == now.hour:
                        m = current_eval.minute - now.minute
                        if  m == 0:
                            dispath_5[key].remove(task_needed)
                            dispath_s[key].append(task_needed)
                        elif  m > 0 and m <= 2:
                            dispath_5[key].remove(task_needed)
                            dispath_1[key].append(task_needed)
                        elif  m > 0 and m <= 5:
                            dispath_5[key].remove(task_needed)
                            dispath_2[key].append(task_needed)
        sleep(60 * 5)
def task_d_1(lock):
    current_eval = None
    while true:
        with lock:
            now = datetime.now().time()
            for key, value in dispatch_2.items():
                for task_needed in value:
                    current_eval = task_needed.get_time()[0]
                    if current_eval.hour == now.hour:
                        m = current_eval.minute - now.minute
                        if  m == 0:
                            dispath_2[key].remove(task_needed)
                            dispath_s[key].append(task_needed)
                        elif  m > 0 and m <= 2:
                            dispath_2[key].remove(task_needed)
                            dispath_1[key].append(task_needed)
        sleep(60 * 2)

def task_d_1(lock):
    current_eval = None
    while true:
        with lock:
            now = datetime.now().time()
            for key, value in dispatch_1.items():
                for task_needed in value:
                    current_eval = task_needed.get_time()[0]
                    if current_eval.hour == now.hour:
                        m = current_eval.minute - now.minute
                        if  m == 0:
                            dispath_1[key].remove(task_needed)
                            dispath_s[key].append(task_needed)
        sleep(60)

#at this point if reacheced time the task
def task_d_s(lock):
    while true:
        with lock:
            for key, value in dispatch_s.items():
                for task in value:
                    users, obj = TaskCall.get_resolve_pool(key, task)
                    dispath_1[key].remove(task)
                    ## NOTE: r task is where what need to be resolved will be and they have to be resolved in order to be removed
                    r_task[f'{obj.__class__.name}_{obj.pk}'] = [users, obj]

        sleep(5)


def task1(lock):
    # function to print cube of given num
    while True:
        with lock:
            print("first task running wass good")
        sleep(5)


def task2(lock):
    # function to print cube of given num
    while True:
        with lock:
            print("second task running wass good")
        sleep(5)
