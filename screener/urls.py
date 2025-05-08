# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ... other URL patterns ...
    path('initiate/', views.upload_video, name='upload_video'),
    path('trim-step/<str:unique_link>/', views.trim_single_step, name='trim-step'),
    path('get_steps/<str:link>/', views.get_steps, name='get-steps'),
]