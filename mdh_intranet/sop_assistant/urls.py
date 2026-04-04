from django.urls import path
from . import views

app_name = 'sop_assistant'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Wizard Steps
    path('start/', views.select_template, name='select_template'),
    path('draft/<int:draft_id>/metadata/', views.draft_metadata, name='draft_metadata'),
    path('draft/<int:draft_id>/content/', views.draft_content, name='draft_content'),
    path('draft/<int:draft_id>/icd/', views.draft_icd, name='draft_icd'),
    path('draft/<int:draft_id>/validate/', views.draft_validate, name='draft_validate'),
    path('draft/<int:draft_id>/preview/', views.draft_preview, name='draft_preview'),
    path('draft/<int:draft_id>/', views.draft_detail, name='draft_detail'),
    path('draft/<int:draft_id>/export/docx/', views.export_draft_docx, name='export_draft_docx'),
    path('draft/<int:draft_id>/export/pdf/', views.export_draft_pdf, name='export_draft_pdf'),

    # API Endpoints
    path('api/icd-search/', views.api_icd_search, name='api_icd_search'),
    path('api/autosave/<int:draft_id>/', views.api_autosave, name='api_autosave'),
    path('api/ai-suggest/<int:draft_id>/', views.api_ai_suggest, name='api_ai_suggest'),
    path('api/context/<int:draft_id>/', views.api_get_context, name='api_get_context'),
    path('api/validate/<int:draft_id>/', views.api_validate, name='api_validate'),
    path('api/icd-suggest/<int:draft_id>/', views.api_icd_suggest, name='api_icd_suggest'),
]
