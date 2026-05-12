from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile
import logging


logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LoginHistory


def record_activity(user, action, metadata=None):
    """Best-effort audit logging; product flows should not fail if logging is unavailable."""
    try:
        from admin_dashboard.models import ActivityLog
        ActivityLog.record(user=user, action=action, metadata=metadata)
    except Exception:
        logger.exception('Failed to record activity: %s', action)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0]  # get real IP if behind proxy
    else:
        ip = request.META.get('REMOTE_ADDR')

    device = request.META.get('HTTP_USER_AGENT', '')[:255]

    LoginHistory.objects.create(
        user=user,
        ip_address=ip,
        device=device
    )
    record_activity(user, 'login', {'ip_address': ip, 'device': device})


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    record_activity(user, 'logout')
