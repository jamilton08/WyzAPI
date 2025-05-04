from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    
    path('transact/assignments/user/<int:asignee_id>/', views.perm_transactional_exchange, name = 'perm_transactional'),
    ]
