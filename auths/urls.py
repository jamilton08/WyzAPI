from django.urls import path, include
from . import views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<euid64>[0-9A-Za-z_\-]+)/',
        views.activate, name='activate'),
    path('users/',views.UserViewSet.as_view({'get': 'list'}), name='user_views'),
    path('my/info/',views.LoggedInUserViewSet.as_view({'get': 'retrieve'}), name='user_info'),
    path('add/phone/', views.add_phone, name='add_phone'),
    path('add/email/', views.add_email, name='add_email'),
    path('change/phone/', views.request_code, name='change_phone'),
    path('api/token/', views.ObtainTokenView.as_view(), name='token_obtain_view'),
    path('api/token/refresh/', views.RefreshCustom.as_view(), name='token_refresh'),
    path('bro/', views.bro, name='bro'),
    path('profile/pic/change', views.ProfileUpdate.as_view(), name='profile_pic_change'),
    path('get/involvements/<int:org>/', views.get_involvements, name="get_involvements"),
    path('reset/entity/', views.update_entity, name = "update_entity"),
    path('initialize/reset/', views.generate_forgotten_password_trans, name = "initialize_reset"),
    path('change/password/', views.password_reset, name = "password_change"),
    path('verify/token/<str:token>/', views.verify_token, name="get_involvements"),
]
