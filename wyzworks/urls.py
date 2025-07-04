from django.urls import path, include
from . import views


urlpatterns = [
    path('share/folder/', views.upload_folder_s3, name='upload_folder_s3'),
    path('get/folder/<slug:link>/', views.retrieve_or_submit_folder, name='folder-s3-get'),
    path("submit-via-exchange/<uuid:exchange_uuid>/", views.update_submission_name, name="submit-via-exchange"),
    path("forms/init/", views.init_form, name="init_form"),
    path("forms/view/", views.view_form, name="view_form"),
    path("forms/content/", views.form_content, name="form_content"),
    path('forms/manage/<str:token>/', views.manage_form,name='manage_form'),
    path('forms/link/file/', views.link_form_file, name='link_form_file'),

   # path('api/editor-state/', views.SaveEditorStateAPIView.as_view(), name='editor_state'),
    #path('api/editor-state/get/<slug:folder_id>/', views.RetrieveEditorStateAPIView.as_view(), name='editor_state_get'),

 

]
