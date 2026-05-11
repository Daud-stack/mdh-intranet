from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('journals/', views.journal_list, name='journal_list'),
    path('journals/create/', views.journal_create, name='journal_create'),
    path('ledger/<int:account_id>/', views.ledger_view, name='ledger'),
    path('reports/p-and-l/', views.profit_loss, name='profit_loss'),
    path('import/', views.import_wizard, name='import_wizard'),
]
