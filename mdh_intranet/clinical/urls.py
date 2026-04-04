from django.urls import path
from . import views

app_name = 'clinical'

urlpatterns = [
    path('', views.clinical_dashboard, name='dashboard'),
    
    # Patient Management
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_pk>/vitals/', views.log_vitals, name='log_vitals'),
    path('patients/<int:patient_pk>/allergies/', views.manage_allergies, name='manage_allergies'),
    
    # Consultations
    path('patients/<int:patient_id>/consult/', views.consultation_create, name='consultation_create'),
    path('consultations/my/', views.my_consultations, name='my_consultations'),
    path('consultations/history/', views.consultation_history, name='consultation_history'),
    path('consultations/<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('consultations/<int:pk>/pdf/', views.download_consultation_pdf, name='consultation_pdf'),
    
    # Prescriptions
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/<int:pk>/pdf/', views.download_prescription_pdf, name='prescription_pdf'),
    path('prescriptions/check-interactions/', views.check_drug_interactions, name='check_interactions'),
    path('prescriptions/<int:pk>/dispense/', views.dispense_prescription, name='dispense_prescription'),
    path('pharmacy/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    
    # Lab Requests
    path('lab/', views.lab_dashboard, name='lab_dashboard'),
    path('lab/<int:pk>/', views.lab_request_detail, name='lab_request_detail'),
    path('lab/<int:pk>/update/', views.update_lab_status, name='update_lab_status'),
    path('lab/<int:pk>/pdf/', views.download_lab_request_pdf, name='lab_request_pdf'),
    
    # Imaging
    path('imaging/', views.imaging_dashboard, name='imaging_dashboard'),
    path('imaging/<int:pk>/', views.imaging_request_detail, name='imaging_request_detail'),
    path('imaging/<int:pk>/update/', views.update_imaging_status, name='update_imaging_status'),
    
    # Operating Theatre
    path('theatre/', views.theatre_dashboard, name='theatre_dashboard'),
    path('theatre/<int:pk>/', views.theatre_booking_detail, name='theatre_booking_detail'),
    path('theatre/<int:pk>/update/', views.update_theatre_status, name='update_theatre_status'),
    
    # Nursing & Handover
    path('nursing/', views.nursing_dashboard, name='nursing_dashboard'),
    path('patients/<int:patient_id>/nursing-note/', views.log_nursing_note, name='log_nursing_note'),
    path('patients/<int:patient_id>/fluid-balance/', views.log_fluid_balance, name='log_fluid_balance'),
    path('nursing/handover/', views.handover_create, name='handover_create'),
    path('nursing/handover/<int:pk>/', views.handover_detail, name='handover_detail'),
    path('management/', views.clinical_manager_dashboard, name='manager_dashboard'),
]
