"""
Core service layer — helper functions for audit logging,
sending notifications (in-app + email), and creating approval workflows.
"""
import json
import logging
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import AuditLog, Notification, ApprovalWorkflow, ApprovalStep

logger = logging.getLogger(__name__)


# ─── AUDIT HELPERS ──────────────────────────────────────────────

def log_action(user, action, obj=None, changes=None, description='',
               module='', ip_address=None):
    """
    Create an audit log entry.

    Usage:
        log_action(request.user, 'create', sop, description='Created new SOP')
        log_action(request.user, 'update', ticket,
                   changes={'status': {'old': 'Open', 'new': 'Closed'}})
    """
    ct = None
    oid = None
    obj_repr = ''

    if obj is not None:
        ct = ContentType.objects.get_for_model(obj)
        oid = obj.pk
        obj_repr = str(obj)[:300]

    if not module and obj is not None:
        module = obj._meta.app_label

    return AuditLog.objects.create(
        user=user,
        action=action,
        content_type=ct,
        object_id=oid,
        object_repr=obj_repr,
        changes_json=json.dumps(changes or {}),
        module=module,
        description=description,
        ip_address=ip_address,
    )


def get_client_ip(request):
    """Extract real client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def track_model_changes(old_instance, new_instance, fields=None):
    """
    Compare two model instances and return a dict of changed fields.

    Usage:
        old = SOP.objects.get(pk=1)  # before edit
        ... (user edits) ...
        changes = track_model_changes(old, new_sop, ['title', 'status', 'content'])
    """
    if fields is None:
        fields = [f.name for f in new_instance._meta.fields
                  if f.name not in ('id', 'pk', 'created_at', 'updated_at')]

    changes = {}
    for field in fields:
        old_val = str(getattr(old_instance, field, ''))
        new_val = str(getattr(new_instance, field, ''))
        if old_val != new_val:
            # Truncate long values for readability
            changes[field] = {
                'old': old_val[:500],
                'new': new_val[:500],
            }
    return changes


# ─── EMAIL HELPERS ──────────────────────────────────────────────

def send_notification_email(recipient, title, message='', link='',
                            notification_type='system', priority='normal'):
    """
    Send an HTML-formatted notification email.
    Only sends if SMTP is configured (EMAIL_HOST is set).
    Fails silently to never block the main workflow.

    Usage:
        send_notification_email(user, 'Your leave was approved',
                                message='Enjoy your break!',
                                link='/leave/123/')
    """
    if not getattr(settings, 'EMAIL_HOST', ''):
        return False

    # Skip if user has no email address
    email = getattr(recipient, 'email', None)
    if not email:
        return False

    # Build colour and icon from type
    type_colors = {
        'approval': '#f59e0b', 'approved': '#10b981', 'rejected': '#ef4444',
        'sop_update': '#3b82f6', 'sop_review': '#f59e0b',
        'acknowledge': '#6366f1', 'incident': '#ef4444',
        'ticket': '#3b82f6', 'leave': '#10b981',
        'system': '#6b7280', 'mention': '#6366f1',
    }
    accent_color = type_colors.get(notification_type, '#3b82f6')

    # Priority markers
    priority_badges = {
        'urgent': '🔴 URGENT',
        'high': '🟠 HIGH PRIORITY',
        'normal': '',
        'low': '',
    }
    priority_badge = priority_badges.get(priority, '')

    # Build full URL for the link
    site_name = 'OpsHub'
    full_link = ''
    if link:
        # In production this should use SITE_URL setting
        base = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        full_link = f"{base}{link}" if link.startswith('/') else link

    # HTML email body
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background:#f0f4f8; font-family:'Segoe UI',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8; padding:20px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background:linear-gradient(135deg, {accent_color}, #1d4ed8); padding:28px 32px; text-align:center;">
                            <h1 style="margin:0; color:#ffffff; font-size:20px; font-weight:700; letter-spacing:-0.5px;">
                                🏥 {site_name}
                            </h1>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding:32px;">
                            {f'<span style="display:inline-block;background:#fef3c7;color:#92400e;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:16px;">{priority_badge}</span><br><br>' if priority_badge else ''}
                            <h2 style="margin:0 0 16px; color:#0f172a; font-size:18px; font-weight:600;">
                                {title}
                            </h2>
                            {f'<p style="margin:0 0 24px; color:#475569; font-size:15px; line-height:1.6;">{message}</p>' if message else ''}
                            {f'<a href="{full_link}" style="display:inline-block;background:{accent_color};color:#ffffff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">View Details →</a>' if full_link else ''}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px 32px; background:#f8fafc; border-top:1px solid #e2e8f0; text-align:center;">
                            <p style="margin:0; color:#94a3b8; font-size:12px;">
                                This is an automated notification from {site_name}.<br>
                                You received this because you are a registered user.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    plain_message = strip_tags(f"{title}\n\n{message}\n\n{full_link or ''}")

    try:
        send_mail(
            subject=f"[OpsHub] {title}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to send notification email to {email}: {e}")
        return False


# ─── NOTIFICATION HELPERS ───────────────────────────────────────

def notify(recipient, title, notification_type='system', message='',
           link='', priority='normal', icon='fas fa-bell', obj=None,
           send_email=False):
    """
    Send an in-app notification to a user.
    Optionally sends an email notification as well.

    Usage:
        notify(user, 'Your leave was approved', 'approved',
               link='/leave/123/', priority='high', send_email=True)
    """
    ct = None
    oid = None
    if obj is not None:
        ct = ContentType.objects.get_for_model(obj)
        oid = obj.pk

    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        link=link,
        icon=icon,
        content_type=ct,
        object_id=oid,
    )

    # Send email for high-priority or when explicitly requested
    if send_email or priority in ('high', 'urgent'):
        send_notification_email(
            recipient, title, message=message, link=link,
            notification_type=notification_type, priority=priority,
        )

    return notification


def notify_group(users, title, notification_type='system', **kwargs):
    """Send the same notification to multiple users."""
    notifications = []
    for user in users:
        notifications.append(notify(user, title, notification_type, **kwargs))
    return notifications


def notify_admins(title, notification_type='system', **kwargs):
    """Send notification to all superusers."""
    admins = User.objects.filter(is_superuser=True, is_active=True)
    return notify_group(admins, title, notification_type, **kwargs)


# ─── APPROVAL WORKFLOW HELPERS ──────────────────────────────────

def create_approval_workflow(obj, submitted_by, approvers, module='', notes=''):
    """
    Create a multi-step approval workflow attached to any object.

    Args:
        obj: The model instance to approve (SOP, leave request, etc.)
        submitted_by: The user submitting for approval
        approvers: list of dicts [{'user': User, 'role': 'Department Head'}, ...]
        module: Module name for filtering
        notes: Optional submission notes

    Returns:
        ApprovalWorkflow instance

    Usage:
        workflow = create_approval_workflow(
            obj=sop,
            submitted_by=request.user,
            approvers=[
                {'user': dept_head, 'role': 'Department Head'},
                {'user': quality_officer, 'role': 'Quality Officer'},
            ],
            module='sop_manual',
        )
        workflow.submit()
    """
    ct = ContentType.objects.get_for_model(obj)

    workflow = ApprovalWorkflow.objects.create(
        content_type=ct,
        object_id=obj.pk,
        object_repr=str(obj)[:300],
        submitted_by=submitted_by,
        total_steps=len(approvers),
        module=module,
        notes=notes,
    )

    for i, approver_info in enumerate(approvers, start=1):
        ApprovalStep.objects.create(
            workflow=workflow,
            order=i,
            approver=approver_info['user'],
            role_label=approver_info.get('role', ''),
        )

    return workflow
