from django.urls import path, include
from . import views


urlpatterns = [
    path('create/', views.create_session, name='create_session'),
    path('add/user/', views.add_user_to_session, name='add_to_session'),
    path('sign/overlap', views.sign_overlap, name="overlaps_sign")
]
