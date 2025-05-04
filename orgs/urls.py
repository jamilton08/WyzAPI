from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('create/', views.create_org, name='create_organization'),
    path('user/signee/create/', views.user_signee_create,name =  "user_signee_create"),
    path('user/invites/accept/', views.user_accept_and_get, name = 'user_accept_invite'),
    path('org/invites/<int:org_pk>/', views.org_invites_view),
    path('org/invites/accept/', views.org_accept_and_get, name = 'org_accept_invite'),
    path('org/signee/create/', views.org_signee_create, name = "org_signee_create"),
    path('get/all/orgs/', views.OrganizationList.as_view(), name = 'all_orgs'),
    path('add/permissions/', views.assign_perm, name = 'assign_permissions'),
    path('orgs/users/search/<int:last>/', views.GetOrgUsers.as_view(), name = 'orgs_users_search'),
    path('orgs/users/search/<int:last>/<str:search_term>/', views.GetOrgUsers.as_view(), name = 'orgs_users_search'),
    path("orgs/users/navigation/", views.navigational_org_user, name = 'navigating_org_user'),
    ]
