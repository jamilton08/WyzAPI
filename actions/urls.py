from django.urls import path, include
from . import views


urlpatterns = [
    path('respond/', views.respond_action, name='action_respond'),
    path('get/needed/responses/<int:org>/', views.get_needed_responses, name="needed_responses"),
]
