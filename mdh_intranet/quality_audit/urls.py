from django.urls import path
from . import views

app_name = 'quality_audit'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('template/<int:template_id>/start/', views.perform_audit, name='perform_audit'),
    path('submission/<int:submission_id>/', views.audit_detail, name='audit_detail'),
    path('submission/<int:submission_id>/export/', views.export_audit_pdf, name='export_pdf'),
    path('template/new/', views.template_create, name='template_create'),
    path('template/<int:template_id>/questions/', views.template_questions, name='template_questions'),
]
