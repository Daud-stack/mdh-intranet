from django.urls import path
from . import views

app_name = 'training_compliance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('log/', views.log_certification, name='log_certification'),
    path('directory/', views.course_directory, name='course_directory'),
]
