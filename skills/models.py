from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class SkillCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='🎯')
    description = models.TextField(blank=True)
    gradient_color = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Skill Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Skill(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    name = models.CharField(max_length=100)
    category = models.ForeignKey(SkillCategory, on_delete=models.SET_NULL, null=True, related_name='skills')
    description = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    SKILL_TYPE_CHOICES = [
        ('teach', 'Can Teach'),
        ('learn', 'Want to Learn'),
    ]
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_skills')
    skill_type = models.CharField(max_length=10, choices=SKILL_TYPE_CHOICES)
    level = models.CharField(max_length=15, choices=LEVEL_CHOICES, blank=True)
    description = models.TextField(blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'skill', 'skill_type')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_skill_type_display()} - {self.skill.name}"
