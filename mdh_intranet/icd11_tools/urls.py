from . import views, api_views

app_name = 'icd11_tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('code/<int:pk>/', views.code_detail, name='detail'),
    path('api/search/', api_views.search_icd_codes, name='api_search'),
]
