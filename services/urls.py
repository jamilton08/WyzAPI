from django.urls import path, include
from . import views


urlpatterns = [
    path('create/', views.create_service, name='create_service'),
    path('<int:org_pk>/', views.get_org_services, name='org_services'),
    path('add/to/service/', views.add_to_service, name = "user_to_service")

]
