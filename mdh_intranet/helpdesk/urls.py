from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.create_ticket, name='create'),
    path('<int:pk>/', views.ticket_detail, name='detail'),
]
