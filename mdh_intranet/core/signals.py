from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from .middleware import get_current_user, get_current_ip
from .services import log_action, track_model_changes
import json

# List of apps/models to automatically audit
AUDIT_WHITELIST = [
    'sop_manual.SOP',
    'incident_log.Incident',
    'capa.CAPARecord',
    'leave_management.LeaveRequest',
    'projects.Project',
    'helpdesk.Ticket',
    'documents.Document',
    'quality_audit.AuditTemplate',
    'quality_audit.AuditSubmission',
]

def is_auditable(instance):
    label = f"{instance._meta.app_label}.{instance._meta.model_name.capitalize()}"
    # Check both case variations if needed, but usually app.Model
    return f"{instance._meta.app_label}.{instance.__class__.__name__}" in AUDIT_WHITELIST

@receiver(post_save)
def audit_save(sender, instance, created, **kwargs):
    if not is_auditable(instance):
        return

    user = get_current_user()
    ip = get_current_ip()
    
    action = 'create' if created else 'update'
    
    # For updates, we try to get changes if the instance has _old_instance (set in pre_save)
    changes = {}
    if not created and hasattr(instance, '_old_instance'):
        changes = track_model_changes(instance._old_instance, instance)
    
    log_action(
        user=user,
        action=action,
        obj=instance,
        changes=changes,
        description=f"{'Created' if created else 'Updated'} {instance._meta.verbose_name}: {str(instance)}",
        ip_address=ip
    )

@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Capture the state of the instance before it's saved to calculate diffs."""
    if not is_auditable(instance):
        return
        
    if instance.pk:
        try:
            instance._old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_instance = None

@receiver(post_delete)
def audit_delete(sender, instance, **kwargs):
    if not is_auditable(instance):
        return

    user = get_current_user()
    ip = get_current_ip()
    
    log_action(
        user=user,
        action='delete',
        obj=instance,
        description=f"Deleted {instance._meta.verbose_name}: {str(instance)}",
        ip_address=ip
    )

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(user, 'login', description=f"User {user.username} logged in", module='auth', ip_address=get_current_ip())

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_action(user, 'logout', description=f"User {user.username} logged out", module='auth', ip_address=get_current_ip())
