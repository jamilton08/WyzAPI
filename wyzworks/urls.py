from django.urls import path, include
from . import views


urlpatterns = [
    path('share/folder/', views.upload_folder_s3, name='upload_folder_s3'),
    path('get/folder/<slug:link>/', views.retrieve_or_submit_folder, name='folder-s3-get'),
    path("submit-via-exchange/<uuid:exchange_uuid>/", views.update_submission_name, name="submit-via-exchange"),
   # path('api/editor-state/', views.SaveEditorStateAPIView.as_view(), name='editor_state'),
    #path('api/editor-state/get/<slug:folder_id>/', views.RetrieveEditorStateAPIView.as_view(), name='editor_state_get'),

 

]
