from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = [
        'bio', 'avatar', 'location', 'availability',
        'linkedin_url', 'website_url', 'is_verified'
    ]


class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_location', 'get_verified', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'profile__is_verified', 'profile__availability']
    search_fields = ['username', 'email', 'profile__location']

    def get_location(self, obj):
        return obj.profile.location if hasattr(obj, 'profile') else '-'
    get_location.short_description = 'Location'

    def get_verified(self, obj):
        return obj.profile.is_verified if hasattr(obj, 'profile') else False
    get_verified.short_description = 'Verified'
    get_verified.boolean = True  # shows a green tick / red cross


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'availability', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'availability']
    search_fields = ['user__username', 'user__email', 'location']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_verified']  # toggle verified directly from list view
    ordering = ['-created_at']

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'bio', 'avatar', 'location', 'availability')
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'website_url')
        }),
        ('Status', {
            'fields': ('is_verified', 'created_at', 'updated_at')
        }),
    )


# Re-register User with our custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
from .models import LoginHistory

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address', 'short_device']
    list_filter = ['login_time']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'login_time', 'ip_address', 'device']
    ordering = ['-login_time']

    def short_device(self, obj):
        return obj.device[:60] + '...' if len(obj.device) > 60 else obj.device
    short_device.short_description = 'Device / Browser'

    def has_add_permission(self, request):
        return False  # admin cannot manually add login records