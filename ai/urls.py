from django.urls import path
from . import views

urlpatterns = [
    path("generate/shape/", views.generate_dsl_view, name="generate-dsl"),
    path("generate/rubric/", views.generate_rubric, name="generate-rubric"),
    path('generate/assignment/', views.generate_assignment, name='generate_assignment'),
    path('generate/lessonplan/', views.generate_lessonplan, name='generate_lessonplan'),
    path('grade/files/', views.grade_files_view, name='grade_files'),
]