from django.urls import path, include
from . import views


urlpatterns = [
    path('create/assign/organization/', views.OrganizationAssignAddress.as_view(), name='create_assign_organization'),
    path('create/assign/user/', views.UserAssignAddress.as_view(), name='create_assign_user'),

]
