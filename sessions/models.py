from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed'),
    ]

    DURATION_CHOICES = [
        (30, '30 minutes'),
        (60, '1 hour'),
        (90, '1.5 hours'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_sessions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_sessions')

    skill_offered = models.CharField(max_length=100)
    skill_requested = models.CharField(max_length=100)

    start_time = models.DateTimeField()
    duration = models.IntegerField(choices=DURATION_CHOICES, help_text='Duration in minutes')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    meeting_link = models.URLField(blank=True, null=True)

    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_rated = models.BooleanField(default=False)

    # Existing chat/profile booking modals submit notes; keep the field so the
    # current UI remains compatible.
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['sender', 'status'], name='sessions_se_sender__idx'),
            models.Index(fields=['receiver', 'status'], name='sessions_se_receive_idx'),
            models.Index(fields=['start_time'], name='sessions_se_start_t_7b6b46_idx'),
        ]

    def __str__(self):
        return (
            f'{self.sender.username} -> {self.receiver.username} '
            f'@ {self.start_time:%Y-%m-%d %H:%M} ({self.get_status_display()})'
        )

    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration)

    @property
    def join_available_at(self):
        return self.start_time - timedelta(minutes=10)

    @property
    def jitsi_link(self):
        return f'https://meet.jit.si/skillsphere-session-{self.pk}'

    def ensure_meeting_link(self, save=True):
        if not self.meeting_link:
            self.meeting_link = self.jitsi_link
            if save and self.pk:
                self.save(update_fields=['meeting_link', 'updated_at'])
        return self.meeting_link

    @property
    def scheduled_at(self):
        return self.start_time

    @property
    def skill_wanted(self):
        return self.skill_requested

    @property
    def is_past(self):
        return self.start_time < timezone.now()

    @property
    def phase(self):
        now = timezone.now()
        if self.status == 'rejected':
            return 'rejected'
        if self.status == 'cancelled':
            return 'cancelled'
        if self.status == 'pending':
            return 'pending'
        if self.status == 'completed':
            return 'completed'
        if self.status == 'missed':
            return 'missed'
        if now < self.start_time:
            return 'upcoming'
        if self.start_time <= now <= self.end_time():
            return 'live_now'
        return 'missed'

    @property
    def phase_label(self):
        labels = {
            'pending': 'Pending',
            'upcoming': 'Scheduled',
            'live_now': 'Live Now',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'missed': 'Missed',
            'rejected': 'Rejected',
        }
        return labels.get(self.phase, self.get_status_display())

    @property
    def can_join_now(self):
        now = timezone.now()
        return self.status == 'accepted' and self.join_available_at <= now <= self.end_time()

    @property
    def is_active_status(self):
        return self.status in ['pending', 'accepted']

    def overlaps_with(self, other_session):
        """Return True when this session's time window overlaps another."""
        return self.start_time < other_session.end_time() and other_session.start_time < self.end_time()

    @classmethod
    def users_are_connected(cls, user_a, user_b):
        """
        Users can book sessions only after an accepted exchange request or an
        existing conversation connects them.
        """
        from django.db.models import Q
        from matching.models import ExchangeRequest
        from messaging.models import Conversation

        has_accepted_request = ExchangeRequest.objects.filter(
            Q(sender=user_a, receiver=user_b) | Q(sender=user_b, receiver=user_a),
            status='accepted',
        ).exists()
        if has_accepted_request:
            return True

        return Conversation.objects.filter(participants=user_a).filter(participants=user_b).exists()

    @classmethod
    def check_overlap(cls, user, start_time, duration, exclude_id=None, statuses=None):
        """Return True if `user` has a session in the same time window."""
        from django.db.models import Q

        statuses = statuses or ['pending', 'accepted']
        end = start_time + timedelta(minutes=duration)
        sessions = cls.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status__in=statuses,
            start_time__lt=end,
        ).exclude(pk=exclude_id or 0)

        return any(session.end_time() > start_time for session in sessions)


class SessionReview(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_reviews')
    rating = models.PositiveSmallIntegerField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['session', 'reviewer'], name='unique_session_review_per_user'),
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='session_review_rating_1_5',
            ),
        ]

    def __str__(self):
        return f'{self.reviewer.username} rated session {self.session_id}: {self.rating}'
