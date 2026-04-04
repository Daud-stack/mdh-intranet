from django.urls import path
from . import views

app_name = 'hr_management'

urlpatterns = [
    path('', views.hr_dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/clock-in/', views.clock_in, name='clock_in'),
    path('attendance/clock-out/', views.clock_out, name='clock_out'),
    path('performance/', views.performance_list, name='performance_list'),
    path('performance/create/<int:employee_id>/', views.performance_create, name='performance_create'),
    path('training/', views.training_list, name='training_list'),
    path('training/create/<int:employee_id>/', views.training_create, name='training_create'),
    path('hiring/', views.hiring_request_list, name='hiring_request_list'),
    path('hiring/add/', views.hiring_request_create, name='hiring_request_create'),
    path('hiring/<int:pk>/update/<str:status>/', views.hiring_request_status_update, name='hiring_request_status_update'),
]
