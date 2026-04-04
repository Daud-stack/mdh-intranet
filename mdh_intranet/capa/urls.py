from django.urls import path
from . import views

app_name = 'capa'

urlpatterns = [
    path('', views.capa_list, name='list'),
    path('create/', views.capa_create, name='create'),
    path('<int:pk>/', views.capa_detail, name='detail'),
    path('<int:pk>/update/<str:phase>/', views.capa_update_phase, name='update_phase'),
    path('<int:pk>/advance/', views.capa_advance, name='advance'),
    path('<int:pk>/comment/', views.capa_add_comment, name='add_comment'),
]
