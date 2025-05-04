from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('create/dates/objects/', views.create_dates, name='create_dates'),
    path('create/times/objects/', views.create_times, name='create_times'),
    path('create/floats/objects/', views.create_floats, name='create_floats'),
    path('date/time/copy/', views.copy_datetime, name='datetime_copy'),
    path('date/time/paste/', views.paste_datetime, name='datetime_paste'),
    path('check/dates/<int:pk>/', views.get_available_dates),
    path('shift/dates/', views.shift_date),
    path('expand/dates/', views.expand_date),
    path('shift/time/', views.shift_time),
    path('expand/time/', views.expand_time),
    path('shift/float/', views.shift_float),
    path('expand/float/', views.expand_float),
    path('delete/dates/<int:date_pk>/', views.delete_date),
    path('get/dates/<int:obj_place>/', views.get_date),

]
