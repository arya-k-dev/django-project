from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """Audit trail for security-sensitive and product-significant actions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        username = self.user.username if self.user_id and self.user else 'system'
        return f'{username}: {self.action} at {self.timestamp}'

    @classmethod
    def record(cls, user=None, action='', metadata=None):
        """Small helper used by views/signals to keep audit writes consistent."""
        return cls.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            action=action,
            metadata=metadata or {},
        )
