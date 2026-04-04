from django.urls import path
from . import views

app_name = 'leave_management'

urlpatterns = [
    path('', views.leave_list, name='leave_list'),
    path('apply/', views.leave_create, name='leave_create'),
    path('<int:pk>/', views.leave_detail, name='leave_detail'),
    path('<int:pk>/approve/', views.leave_approve, name='leave_approve'),
]
