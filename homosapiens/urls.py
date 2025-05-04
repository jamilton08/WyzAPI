from django.urls import path, include
from . import views


urlpatterns = [
    path('org/invites/reciever/', views.reciever_invite, name='org_invites_reciever'),
    path('reciever/requests/org/', views.reciever_request, name='reciver_request_to_orgs'),
    path('org/invites/overwatch/', views.overwatch_invite, name='org_invites_overwatch'),
    path('overwatch/requests/org/', views.overwatch_request, name='overwatch_request_to_orgs'),
    path('reciever/accept/', views.reciever_accept, name='reciever_accepts'),
    path('org/reciever/accept/', views.reciver_org_accept, name='org_reciever_accepts'),
    path('overwatch/accept/', views.overwatch_accept, name='overwatch_accepts'),
    path('org/overwatch/accept/', views.overwatch_org_accept, name='org_overwatch_accepts'),
    path('search/<int:last>/<str:search_term>/', views.GetSearchedUsers.as_view(), name='search_users'),
    path('get/recievers/watchers', views.GetRecieversOverwatchers.as_view(), name='recievers_overwatchers'), 
    path('get/watchers/recievers', views.GetOverwatchersRecievers.as_view(), name='watchers_recievers'),
     
    ]
