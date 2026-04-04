from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('sops/', include('sop_manual.urls')),
    path('incidents/', include('incident_log.urls')),
    path('icd11/', include('icd11_tools.urls')),
    path('documents/', include('documents.urls')),
    path('projects/', include('projects.urls')),
    path('feedback/', include('feedback.urls')),
    path('sop-assistant/', include('sop_assistant.urls')),
]
