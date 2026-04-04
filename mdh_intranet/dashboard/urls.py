from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='home'),
    path('schedule/', views.schedule, name='schedule'),
    path('settings/', views.settings_view, name='settings'),
]
