from django.contrib.auth.models import User
from django.db import models


class ExchangeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    sender_teach_skills = models.JSONField(default=list)
    receiver_teach_skills = models.JSONField(default=list)
    match_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.receiver.username} ({self.status})'

    def get_other_user(self, user):
        return self.receiver if self.sender == user else self.sender
