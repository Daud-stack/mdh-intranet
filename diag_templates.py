import os
import django
from django.template.loader import get_template
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()

print(f"INSTALLED_APPS: {settings.INSTALLED_APPS}")
print(f"TEMPLATES: {settings.TEMPLATES}")

try:
    template = get_template('leave_management/leave_list.html')
    print(f"SUCCESS: Template found at {template.origin.name}")
except Exception as e:
    print(f"ERROR: {e}")

# Check app path
from django.apps import apps
app_config = apps.get_app_config('leave_management')
print(f"App Path: {app_config.path}")
print(f"Template dir exists: {os.path.exists(os.path.join(app_config.path, 'templates'))}")
print(f"Full template path: {os.path.join(app_config.path, 'templates', 'leave_management', 'leave_list.html')}")
print(f"File exists: {os.path.exists(os.path.join(app_config.path, 'templates', 'leave_management', 'leave_list.html'))}")
