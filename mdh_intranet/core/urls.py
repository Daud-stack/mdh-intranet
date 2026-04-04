from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Audit Trail
    path('audit/', views.audit_log, name='audit_log'),
    path('audit/<int:log_id>/', views.audit_detail, name='audit_detail'),
    path('audit/export/csv/', views.export_audit_csv, name='audit_export_csv'),
    path('compliance/', views.compliance_hub, name='compliance_hub'),

    # Notifications
    path('notifications/', views.notification_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),

    # Approvals
    path('approvals/', views.approval_list, name='approvals'),
    path('approvals/create/', views.approval_create, name='approval_create'),
    path('approvals/<int:workflow_id>/', views.approval_detail, name='approval_detail'),

    # Global Search
    path('search/', views.global_search, name='search'),
    path('api/search/', views.api_search, name='api_search'),

    # SOP Acknowledgements
    path('acknowledge/<int:sop_id>/', views.sop_acknowledge, name='sop_acknowledge'),
    path('acknowledgements/', views.sop_acknowledgement_report, name='acknowledgement_report'),
]
