from django.urls import path
from . import views

app_name = 'stock_management'

urlpatterns = [
    path('', views.index, name='index'),
    path('stock/', views.stock_list, name='stock_list'),
    path('requisition/create/', views.create_requisition, name='create_requisition'),
    path('requisition/my/', views.my_requisitions, name='my_requisitions'),
    path('requisition/<int:pk>/', views.requisition_detail, name='requisition_detail'),
    path('requisition/<int:pk>/approve/', views.approve_requisition, name='approve_requisition'),
    path('approvals/pending/', views.pending_approvals, name='pending_approvals'),
]
