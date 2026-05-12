from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0  # don't show empty extra rows
    readonly_fields = ['sender', 'receiver', 'content', 'is_read', 'timestamp']
    can_delete = False
    ordering = ['timestamp']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'exchange_request', 'get_participants', 'message_count', 'created_at']
    search_fields = [
        'exchange_request__sender__username',
        'exchange_request__receiver__username'
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    inlines = [MessageInline]  # shows all messages inside the conversation

    def get_participants(self, obj):
        return ', '.join([u.username for u in obj.participants.all()])
    get_participants.short_description = 'Participants'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Total Messages'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'participants', 'messages'
        ).select_related('exchange_request')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'short_content', 'is_read', 'timestamp']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    list_editable = ['is_read']

    fieldsets = (
        ('Users', {
            'fields': ('conversation', 'sender', 'receiver')
        }),
        ('Message', {
            'fields': ('content', 'is_read')
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def short_content(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    short_content.short_description = 'Message'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sender', 'receiver', 'conversation'
        )