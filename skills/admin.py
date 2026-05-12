from django.contrib import admin
from .models import SkillCategory, Skill, UserSkill


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'description', 'skill_count']
    search_fields = ['name', 'description']
    ordering = ['name']

    def skill_count(self, obj):
        return obj.skills.count()
    skill_count.short_description = 'Total Skills'


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'category']
    search_fields = ['name', 'description']
    list_editable = ['is_approved']  # approve/unapprove directly from list
    readonly_fields = ['created_at']
    ordering = ['name']

    fieldsets = (
        ('Skill Info', {
            'fields': ('name', 'category', 'description')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'skill', 'skill_type', 'level',
        'years_experience', 'created_at'
    ]
    list_filter = ['skill_type', 'level', 'skill__category']
    search_fields = ['user__username', 'skill__name', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('User & Skill', {
            'fields': ('user', 'skill', 'skill_type')
        }),
        ('Proficiency', {
            'fields': ('level', 'years_experience', 'description')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'skill', 'skill__category')