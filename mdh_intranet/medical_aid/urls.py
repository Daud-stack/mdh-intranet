from django.urls import path
from . import views

app_name = 'medical_aid'

urlpatterns = [
    path('', views.request_list, name='list'),
    path('create/', views.create_request, name='create'),
    path('<int:pk>/', views.request_detail, name='detail'),
    path('<int:pk>/export/', views.export_excel, name='export_excel'),
    path('<int:pk>/send-email/', views.send_email, name='send_email'),
]
