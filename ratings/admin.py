from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'rater', 'rated_user', 'score', 'teaching_quality',
        'communication', 'punctuality', 'created_at'
    ]
    list_filter = ['score', 'teaching_quality', 'communication', 'punctuality', 'created_at']
    search_fields = ['rater__username', 'rated_user__username', 'feedback']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Users', {
            'fields': ('exchange_request', 'rater', 'rated_user')
        }),
        ('Scores', {
            'fields': ('score', 'teaching_quality', 'communication', 'punctuality')
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'rater', 'rated_user', 'exchange_request'
        )