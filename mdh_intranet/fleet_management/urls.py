from django.urls import path
from . import views

app_name = 'fleet_management'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('trip/start/', views.start_trip, name='start_trip'),
    path('trip/<int:pk>/end/', views.end_trip, name='end_trip'),
    path('fuel/log/', views.log_fuel, name='log_fuel'),
]
