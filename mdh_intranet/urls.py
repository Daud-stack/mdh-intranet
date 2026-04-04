"""
URL configuration for mdh_intranet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mdh_intranet.dashboard.urls')),
    path('sops/', include('mdh_intranet.sop_manual.urls')),
    path('sop-assistant/', include('mdh_intranet.sop_assistant.urls')),
    path('core/', include('mdh_intranet.core.urls')),
    path('incidents/', include('mdh_intranet.incident_log.urls')),
    path('helpdesk/', include('mdh_intranet.helpdesk.urls')),
    path('icd11/', include('mdh_intranet.icd11_tools.urls')),
    path('documents/', include('mdh_intranet.documents.urls')),
    path('projects/', include('mdh_intranet.projects.urls')),
    path('feedback/', include('mdh_intranet.feedback.urls')),
    path('maintenance/', include('mdh_intranet.maintenance.urls')),
    path('stock/', include('mdh_intranet.stock_management.urls')),
    path('users/', include('mdh_intranet.user_management.urls')),
    path('medical-aid/', include('mdh_intranet.medical_aid.urls')),
    path('leave/', include('mdh_intranet.leave_management.urls')),
    path('capa/', include('mdh_intranet.capa.urls')),
    path('hr/', include('mdh_intranet.hr_management.urls')),
    path('rostering/', include('mdh_intranet.rostering.urls')),
    path('fleet/', include('mdh_intranet.fleet_management.urls')),
    path('training/', include('mdh_intranet.training_compliance.urls')),
    path('audit/', include('mdh_intranet.quality_audit.urls')),
    path('clinical/', include('mdh_intranet.clinical.urls')),
    path('analytics/', include('mdh_intranet.analytics.urls')),
    # Django's built-in authentication URLs (login, logout, password reset)
    path('accounts/', include('django.contrib.auth.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
