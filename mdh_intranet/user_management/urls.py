from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.user_create, name='user_create'),
    path('<int:pk>/', views.user_detail, name='user_detail'),
    path('<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('<int:pk>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
]
