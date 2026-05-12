from django.contrib import admin
from .models import ExchangeRequest


@admin.register(ExchangeRequest)
class ExchangeRequestAdmin(admin.ModelAdmin):
    list_display = [
        'sender', 'receiver', 'status', 'match_score',
        'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['sender__username', 'receiver__username', 'message']
    readonly_fields = ['created_at', 'updated_at', 'match_score']
    list_editable = ['status']  # change status directly from list view
    ordering = ['-created_at']

    fieldsets = (
        ('Users', {
            'fields': ('sender', 'receiver')
        }),
        ('Exchange Details', {
            'fields': ('status', 'message', 'match_score')
        }),
        ('Skills Involved', {
            'fields': ('sender_teach_skills', 'receiver_teach_skills'),
            'classes': ('collapse',)  # collapsible section
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'receiver')