from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_update, name='asset_update'),
    path('assets/add/', views.asset_create, name='asset_create'),
    path('work-order/add/', views.work_order_create, name='work_order_create'),
    path('work-order/add/<int:asset_id>/', views.work_order_create, name='work_order_create_asset'),
    path('work-order/<int:pk>/', views.work_order_detail, name='work_order_detail'),
]
