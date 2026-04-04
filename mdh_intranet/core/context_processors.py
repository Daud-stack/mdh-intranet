"""
Template context processors for core infrastructure.
Makes notification counts and other global data available in every template.
"""
from .models import Notification


def notifications(request):
    """Add unread notification count to every template context."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        # Get latest 5 unread for the dropdown
        latest_notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]
        return {
            'unread_notification_count': unread_count,
            'latest_notifications': latest_notifications,
            'user_profile': request.user.profile,
            'display_name': request.user.get_full_name() or request.user.username,
        }
    return {
        'unread_notification_count': 0,
        'latest_notifications': [],
    }
