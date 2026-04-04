from django.urls import path
from . import views

app_name = 'incident_log'

urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.create_incident, name='create'),
    path('<int:pk>/', views.incident_detail, name='detail'),
    path('<int:pk>/update/', views.update_incident, name='update'),
    path('<int:pk>/delete/', views.delete_incident, name='delete'),
]
