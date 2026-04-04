from django.urls import path
from . import views
from . import wopi

app_name = 'documents'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload'),
    path('<int:pk>/', views.document_detail, name='detail'),
    path('<int:pk>/download/', views.download_document, name='download'),
    path('<int:pk>/delete/', views.delete_document, name='delete'),
    path('<int:pk>/view/', views.view_word_document, name='view_word'),
    path('<int:pk>/edit/', views.edit_word_document, name='edit_word'),
    path('<int:pk>/save/', views.save_word_document, name='save_word'),
    path('<int:pk>/content/', views.get_document_content, name='get_content'),
    path('sop/create/', views.create_sop, name='create_sop'),
    
    # Collabora / WOPI routes
    path('collabora/<int:doc_id>/', views.collabora_editor, name='collabora_editor'),
    path('office-viewer/<int:doc_id>/', views.office_web_viewer, name='office_web_viewer'),
    path('wopi/files/<int:file_id>', wopi.check_file_info, name='wopi_check_file_info'),
    path('wopi/files/<int:file_id>/contents', wopi.file_contents, name='wopi_get_file'),
]


