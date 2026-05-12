from django.db import models
from django.contrib.auth.models import User
from matching.models import ExchangeRequest


class Rating(models.Model):
    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    feedback = models.TextField(blank=True)
    teaching_quality = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    communication = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    punctuality = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exchange_request', 'rater')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rater.username} rated {self.rated_user.username}: {self.score}/5"
