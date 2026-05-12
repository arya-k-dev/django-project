from django.contrib.auth.models import User
from django.db import models

from matching.models import ExchangeRequest


class Conversation(models.Model):
    exchange_request = models.OneToOneField(
        ExchangeRequest,
        on_delete=models.CASCADE,
        related_name='conversation',
    )
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Conversation: {self.exchange_request}'

    def last_message(self):
        return self.messages.order_by('-timestamp').first()

    def unread_count(self, user):
        return self.messages.filter(receiver=user, is_read=False).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.sender.username} -> {self.receiver.username}: {self.content[:40]}'
