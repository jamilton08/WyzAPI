from django.urls import path, include
from . import views


urlpatterns = [
    path('get/classes/', views.get_classrooms, name='get_teacher_classroom'),
    path('get/', views.get_test, name='get_tets'),
    ]
