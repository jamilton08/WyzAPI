from django.urls import path
from . import views

urlpatterns = [
    path("generate/shape/", views.generate_dsl_view, name="generate-dsl"),
    path("generate/rubric/", views.generate_rubric, name="generate-rubric"),

]