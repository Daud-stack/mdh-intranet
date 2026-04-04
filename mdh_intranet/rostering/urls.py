from django.urls import path
from . import views

app_name = 'rostering'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('setup/', views.roster_setup, name='roster_setup'),
    path('my-shifts/', views.my_shifts, name='my_shifts'),
    path('swap-requests/', views.swap_requests, name='swap_requests'),
    path('setup/<int:pk>/manage/', views.manage_roster, name='manage_roster'),
]
