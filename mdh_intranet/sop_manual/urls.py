from django.urls import path
from . import views

app_name = 'sop_manual'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.sop_list, name='list'),
    path('category/<int:category_id>/', views.sop_list, name='category_list'),
    path('sop/<int:pk>/', views.sop_detail, name='detail'),
    path('sop/<int:pk>/view-online/', views.sop_office_viewer, name='office_viewer'),
    path('sop/<int:pk>/embed/', views.sop_office_embed, name='embed'),
    path('sop/create/', views.sop_create, name='create'),
    path('sop/<int:pk>/edit/', views.sop_edit, name='edit'),
    path('sop/<int:pk>/export/docx/', views.export_sop_docx, name='export_docx'),
    path('sop/<int:pk>/export/pdf/', views.export_sop_pdf, name='export_pdf'),
    path('assistant/', views.sop_assistant, name='assistant'),
    path('assistant/generate/', views.sop_assistant_generate, name='assistant_generate'),
    path('assistant/save/', views.sop_assistant_save, name='assistant_save'),
]
