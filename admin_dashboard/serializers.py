from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import UserProfile
from matching.models import ExchangeRequest
from messaging.models import Message
from .models import ActivityLog


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'bio',
            'avatar',
            'location',
            'availability',
            'linkedin_url',
            'website_url',
            'is_verified',
            'is_admin',
            'email_verified',
            'response_rate',
            'available_slots',
            'timeline_milestones',
            'average_rating',
            'total_exchanges',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'date_joined',
            'last_login',
            'profile',
        ]
        read_only_fields = fields


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'username', 'user_email', 'action', 'timestamp', 'metadata']
        read_only_fields = fields


class ExchangeRequestReportSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = ExchangeRequest
        fields = [
            'id',
            'sender',
            'sender_username',
            'receiver',
            'receiver_username',
            'status',
            'match_score',
            'sender_teach_skills',
            'receiver_teach_skills',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class MessageStatsSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender_username', 'receiver_username', 'timestamp', 'is_read']
        read_only_fields = fields
