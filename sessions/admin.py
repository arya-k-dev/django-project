from django.contrib import admin
from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'skill_offered', 'skill_requested', 'start_time', 'duration', 'status', 'is_rated', 'created_at')
    list_filter = ('status', 'duration', 'is_rated')
    search_fields = ('sender__username', 'receiver__username', 'skill_offered', 'skill_requested')
    ordering = ('-start_time',)
    readonly_fields = ('created_at', 'updated_at')
