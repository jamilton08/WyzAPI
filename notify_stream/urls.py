from django.urls import path, include
from . import views


urlpatterns = [
    path('nfts/<int:last>/', views.GetUserNotifications.as_view(), name='get_nfts'),
    path('res/<int:last>/', views.GetUserResponses.as_view(), name = "get_res")

]
