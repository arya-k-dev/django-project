from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    AVAILABILITY_CHOICES = [
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('evenings', 'Evenings'),
        ('flexible', 'Flexible'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='flexible')
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW FIELDS (add these)
    email_verified = models.BooleanField(default=False)
    response_rate = models.PositiveSmallIntegerField(default=0, help_text="Percentage (0-100)")
    available_slots = models.TextField(blank=True, help_text="e.g. 'Mon 7-9 PM, Wed 7-9 PM'")
    timeline_milestones = models.JSONField(default=list, blank=True, help_text='List of {"date": "...", "text": "..."}')

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def average_rating(self):
        from ratings.models import Rating
        ratings = Rating.objects.filter(rated_user=self.user)
        if ratings.exists():
            return round(ratings.aggregate(models.Avg('score'))['score__avg'], 1)
        return None

    @property
    def total_exchanges(self):
        from matching.models import ExchangeRequest
        return ExchangeRequest.objects.filter(
            models.Q(sender=self.user) | models.Q(receiver=self.user),
            status='completed'
        ).count()

class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-login_time']
        verbose_name_plural = 'Login Histories'

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"
