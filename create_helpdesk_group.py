"""Create IT Helpdesk group."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from mdh_intranet.helpdesk.models import Ticket

group, created = Group.objects.get_or_create(name='IT Helpdesk')
if created:
    print(f"Created group: {group.name}")
else:
    print(f"Group already exists: {group.name}")

# Optional: Add permissions if needed
# ct = ContentType.objects.get_for_model(Ticket)
# perms = Permission.objects.filter(content_type=ct)
# for p in perms:
#     group.permissions.add(p)
# print("Added Ticket permissions to group")
