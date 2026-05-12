import csv
import logging
from collections import Counter

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDay, TruncWeek
from django.http import StreamingHttpResponse
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from matching.models import ExchangeRequest
from messaging.models import Message
from .models import ActivityLog
from .permissions import ForbiddenBasicAuthentication, ForbiddenSessionAuthentication, IsSkillSphereAdmin
from .serializers import ActivityLogSerializer, AdminUserSerializer


logger = logging.getLogger(__name__)
MAX_EXPORT_ROWS = 10000


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class Echo:
    """File-like adapter for StreamingHttpResponse CSV writers."""

    def write(self, value):
        return value


class AdminAPIView(APIView):
    """Base class that guarantees every endpoint checks server-side admin access."""

    authentication_classes = [ForbiddenSessionAuthentication, ForbiddenBasicAuthentication]
    permission_classes = [IsSkillSphereAdmin]

    def record_admin_action(self, request, action, metadata=None):
        try:
            ActivityLog.record(user=request.user, action=action, metadata=metadata)
        except Exception:
            logger.exception('Failed to record admin activity: %s', action)


def _date_filtered_queryset(queryset, field_name, request):
    start = _parse_date_param(request, 'start_date')
    end = _parse_date_param(request, 'end_date')

    if start and end and start > end:
        raise ValidationError({'date_range': 'start_date must be before or equal to end_date.'})

    if start:
        queryset = queryset.filter(**{f'{field_name}__date__gte': start})
    if end:
        queryset = queryset.filter(**{f'{field_name}__date__lte': end})
    return queryset


def _parse_date_param(request, name):
    raw_value = request.query_params.get(name)
    if raw_value in (None, ''):
        return None

    parsed = parse_date(raw_value)
    if parsed is None:
        raise ValidationError({name: 'Invalid date. Use YYYY-MM-DD.'})
    return parsed


def _profile_or_none(user):
    try:
        return user.profile
    except ObjectDoesNotExist:
        return None


def _mask_email(email):
    if not email or '@' not in email:
        return ''
    name, domain = email.split('@', 1)
    return f'{name[:2]}***@{domain}'


def _export_limit_response(row_count):
    if row_count > MAX_EXPORT_ROWS:
        return Response(
            {
                'detail': f'Export has {row_count} rows. Narrow filters to {MAX_EXPORT_ROWS} rows or fewer.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _paginate(request, queryset, serializer_class):
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


def _stream_csv(filename, header, rows):
    writer = csv.writer(Echo())

    def stream():
        yield writer.writerow(header)
        for row in rows:
            yield writer.writerow(row)

    response = StreamingHttpResponse(stream(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class UserListAPIView(AdminAPIView):
    """List users with pagination, search, and active-state filtering."""

    def get(self, request):
        queryset = User.objects.select_related('profile').order_by('-date_joined')

        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(email__icontains=search))

        active = request.query_params.get('active')
        if active in {'true', '1'}:
            queryset = queryset.filter(is_active=True)
        elif active in {'false', '0'}:
            queryset = queryset.filter(is_active=False)

        return _paginate(request, queryset, AdminUserSerializer)


class UserDetailAPIView(AdminAPIView):
    """Return one user's profile details."""

    def get(self, request, user_id):
        user = User.objects.select_related('profile').filter(id=user_id).first()
        if user is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminUserSerializer(user, context={'request': request}).data)


class UserActivationAPIView(AdminAPIView):
    """Soft activate/deactivate users through the is_active flag."""

    activate = True

    def post(self, request, user_id):
        user = User.objects.select_related('profile').filter(id=user_id).first()
        if user is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not self.activate:
            if user.id == request.user.id:
                return Response(
                    {'detail': 'Admins cannot deactivate their own account.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            profile = _profile_or_none(user)
            active_admin_count = User.objects.filter(
                is_active=True,
                profile__is_admin=True,
            ).count()
            if profile and profile.is_admin and user.is_active and active_admin_count <= 1:
                return Response(
                    {'detail': 'Cannot deactivate the last active admin.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user.is_active = self.activate
        user.save(update_fields=['is_active'])

        action = 'admin_user_activated' if self.activate else 'admin_user_deactivated'
        self.record_admin_action(request, action, {'target_user_id': user.id, 'target_username': user.username})

        return Response(AdminUserSerializer(user, context={'request': request}).data)


class UserDeactivateAPIView(UserActivationAPIView):
    activate = False


class ActivityLogListAPIView(AdminAPIView):
    """List audit logs with date, user, and action filters."""

    def get(self, request):
        queryset = ActivityLog.objects.select_related('user').order_by('-timestamp')
        queryset = _date_filtered_queryset(queryset, 'timestamp', request)

        user_id = request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        action = request.query_params.get('action', '').strip()
        if action:
            queryset = queryset.filter(action__icontains=action)

        return _paginate(request, queryset, ActivityLogSerializer)


class MatchAnalyticsAPIView(AdminAPIView):
    """Return match counts per day and per week."""

    def get(self, request):
        queryset = _date_filtered_queryset(ExchangeRequest.objects.all(), 'created_at', request)

        per_day = (
            queryset.annotate(period=TruncDay('created_at'))
            .values('period')
            .annotate(total=Count('id'))
            .order_by('period')
        )
        per_week = (
            queryset.annotate(period=TruncWeek('created_at'))
            .values('period')
            .annotate(total=Count('id'))
            .order_by('period')
        )

        return Response({
            'per_day': list(per_day),
            'per_week': list(per_week),
        })


class MostRequestedSkillsAPIView(AdminAPIView):
    """Rank skills using actual skill names stored on exchange requests."""

    def get(self, request):
        queryset = _date_filtered_queryset(ExchangeRequest.objects.all(), 'created_at', request)
        counter = Counter()

        for sender_skills, receiver_skills in queryset.values_list('sender_teach_skills', 'receiver_teach_skills'):
            counter.update(sender_skills or [])
            counter.update(receiver_skills or [])

        results = [
            {'name': skill_name, 'request_count': count}
            for skill_name, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:20]
        ]

        return Response({'results': results})


class AverageMatchScoreAPIView(AdminAPIView):
    """Return the average score generated by the matching system."""

    def get(self, request):
        queryset = _date_filtered_queryset(ExchangeRequest.objects.all(), 'created_at', request)
        data = queryset.aggregate(average_match_score=Avg('match_score'), total_matches=Count('id'))
        return Response(data)


class MessageAnalyticsAPIView(AdminAPIView):
    """Return total message count and messages grouped by day."""

    def get(self, request):
        queryset = _date_filtered_queryset(Message.objects.all(), 'timestamp', request)
        per_day = (
            queryset.annotate(period=TruncDay('timestamp'))
            .values('period')
            .annotate(total=Count('id'))
            .order_by('period')
        )
        return Response({
            'total': queryset.count(),
            'per_day': list(per_day),
        })


class UsersCSVExportAPIView(AdminAPIView):
    def get(self, request):
        queryset = User.objects.select_related('profile').order_by('id')
        row_count = queryset.count()
        limit_response = _export_limit_response(row_count)
        if limit_response:
            return limit_response

        def rows():
            for user in queryset.iterator():
                profile = _profile_or_none(user)
                yield [
                    user.id,
                    user.username,
                    _mask_email(user.email),
                    user.first_name,
                    user.last_name,
                    user.is_active,
                    getattr(profile, 'is_admin', False),
                    getattr(profile, 'location', ''),
                    user.date_joined.isoformat() if user.date_joined else '',
                    user.last_login.isoformat() if user.last_login else '',
                ]

        self.record_admin_action(request, 'admin_export_users', {'row_count': row_count})
        return _stream_csv(
            'users.csv',
            ['id', 'username', 'masked_email', 'first_name', 'last_name', 'is_active', 'is_admin', 'location', 'date_joined', 'last_login'],
            rows(),
        )


class MatchDataCSVExportAPIView(AdminAPIView):
    def get(self, request):
        queryset = ExchangeRequest.objects.select_related('sender', 'receiver').order_by('id')
        queryset = _date_filtered_queryset(queryset, 'created_at', request)
        row_count = queryset.count()
        limit_response = _export_limit_response(row_count)
        if limit_response:
            return limit_response

        def rows():
            for match in queryset.iterator():
                yield [
                    match.id,
                    match.sender.username,
                    match.receiver.username,
                    match.status,
                    match.match_score,
                    '; '.join(match.sender_teach_skills),
                    '; '.join(match.receiver_teach_skills),
                    match.created_at.isoformat() if match.created_at else '',
                    match.updated_at.isoformat() if match.updated_at else '',
                ]

        self.record_admin_action(request, 'admin_export_matches', {'row_count': row_count})
        return _stream_csv(
            'matches.csv',
            ['id', 'sender', 'receiver', 'status', 'match_score', 'sender_teach_skills', 'receiver_teach_skills', 'created_at', 'updated_at'],
            rows(),
        )


class ActivityLogsCSVExportAPIView(AdminAPIView):
    def get(self, request):
        queryset = ActivityLog.objects.select_related('user').order_by('id')
        queryset = _date_filtered_queryset(queryset, 'timestamp', request)
        row_count = queryset.count()
        limit_response = _export_limit_response(row_count)
        if limit_response:
            return limit_response

        def rows():
            for log in queryset.iterator():
                yield [
                    log.id,
                    log.user_id or '',
                    log.user.username if log.user else '',
                    log.action,
                    log.timestamp.isoformat() if log.timestamp else '',
                    '',
                ]

        self.record_admin_action(request, 'admin_export_activity_logs', {'row_count': row_count})
        return _stream_csv(
            'activity_logs.csv',
            ['id', 'user_id', 'username', 'action', 'timestamp', 'metadata_redacted'],
            rows(),
        )
