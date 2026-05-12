import json
import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from .models import Session, SessionReview

logger = logging.getLogger(__name__)


def _json_error(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status)


def _wants_json(request):
    return request.headers.get('Content-Type', '').startswith('application/json')


def _session_user_filter(user):
    return Q(sender=user) | Q(receiver=user)


def _parse_start_time(request, data):
    start_value = data.get('start_time') or data.get('scheduled_at')
    if not start_value:
        date_value = request.POST.get('date', '').strip()
        time_value = request.POST.get('time', '').strip()
        start_value = f'{date_value}T{time_value}' if date_value and time_value else ''

    start_time = parse_datetime(start_value)
    if start_time is None:
        return None
    if timezone.is_naive(start_time):
        start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
    return start_time


def _valid_duration(value):
    try:
        duration = int(value)
    except (TypeError, ValueError):
        return None
    return duration if duration in [choice[0] for choice in Session.DURATION_CHOICES] else None


def _session_dict(session, viewer):
    other = session.receiver if session.sender == viewer else session.sender
    return {
        'id': session.pk,
        'other_user': other.get_full_name() or other.username,
        'other_user_id': other.pk,
        'skill_offered': session.skill_offered,
        'skill_requested': session.skill_requested,
        'skill_wanted': session.skill_requested,
        'start_time': session.start_time.isoformat(),
        'scheduled_at': session.start_time.isoformat(),
        'duration': session.duration,
        'status': session.status,
        'status_label': session.get_status_display(),
        'phase': session.phase,
        'phase_label': session.phase_label,
        'meeting_link': session.meeting_link,
        'can_join_now': session.can_join_now,
        'notes': session.notes,
        'is_sender': session.sender_id == viewer.pk,
        'is_rated': session.is_rated,
        'created_at': session.created_at.isoformat(),
    }


def record_activity(user, action, metadata=None):
    try:
        from admin_dashboard.models import ActivityLog
        ActivityLog.record(user=user, action=action, metadata=metadata)
    except Exception:
        logger.exception('Failed to record activity: %s', action)


def _save_response(request, session, status):
    session.status = status
    update_fields = ['status', 'updated_at']
    if status == 'accepted':
        session.ensure_meeting_link(save=False)
        update_fields.append('meeting_link')
    session.save(update_fields=update_fields)
    record_activity(request.user, f'session_{status}', {'session_id': session.pk})

    if _wants_json(request):
        return JsonResponse({'ok': True, 'session': _session_dict(session, request.user)})

    success_messages = {
        'accepted': 'Session scheduled.',
        'rejected': 'Session rejected.',
        'cancelled': 'Session cancelled.',
        'missed': 'Session marked as missed.',
        'completed': 'Session completed.',
    }
    messages.success(request, success_messages.get(status, f'Session {status}.'))
    return redirect('sessions_dashboard')


@login_required
def create_session(request, user_id=None):
    receiver_id = user_id
    data = {}

    if _wants_json(request):
        try:
            data = json.loads(request.body.decode('utf-8') or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error('Invalid JSON body.')
        receiver_id = receiver_id or data.get('receiver_id')
    elif request.method == 'POST':
        data = request.POST

    receiver = get_object_or_404(User, pk=receiver_id)
    if receiver == request.user:
        if _wants_json(request):
            return _json_error('You cannot book a session with yourself.')
        messages.error(request, 'You cannot book a session with yourself.')
        return redirect('sessions_dashboard')

    if not Session.users_are_connected(request.user, receiver):
        message = 'You can only book sessions with connected users.'
        if _wants_json(request):
            return _json_error(message, status=403)
        messages.error(request, message)
        return redirect('profile_view', username=receiver.username)

    if request.method == 'GET':
        return render(request, 'sessions/session_form.html', {
            'receiver': receiver,
            'duration_choices': Session.DURATION_CHOICES,
        })

    start_time = _parse_start_time(request, data)
    duration = _valid_duration(data.get('duration'))
    skill_offered = (data.get('skill_offered') or '').strip()
    skill_requested = (data.get('skill_requested') or data.get('skill_wanted') or '').strip()
    notes = (data.get('notes') or '').strip()

    if start_time is None:
        return _json_error('Invalid date or time.') if _wants_json(request) else _form_error(request, receiver, 'Invalid date or time.')
    if start_time <= timezone.now():
        return _json_error('Session time must be in the future.') if _wants_json(request) else _form_error(request, receiver, 'Session time must be in the future.')
    if duration is None:
        return _json_error('Duration must be 30, 60, or 90 minutes.') if _wants_json(request) else _form_error(request, receiver, 'Duration must be 30, 60, or 90 minutes.')
    if not skill_offered or not skill_requested:
        return _json_error('Skill offered and skill requested are required.') if _wants_json(request) else _form_error(request, receiver, 'Skill offered and skill requested are required.')

    for participant in (request.user, receiver):
        if Session.check_overlap(participant, start_time, duration, statuses=['pending', 'accepted']):
            message = 'That time overlaps with an existing pending or accepted session.'
            return _json_error(message) if _wants_json(request) else _form_error(request, receiver, message)

    session = Session.objects.create(
        sender=request.user,
        receiver=receiver,
        skill_offered=skill_offered,
        skill_requested=skill_requested,
        start_time=start_time,
        duration=duration,
        notes=notes,
    )
    record_activity(request.user, 'session_created', {'session_id': session.pk, 'receiver_id': receiver.pk})

    if _wants_json(request):
        return JsonResponse({'ok': True, 'session': _session_dict(session, request.user)}, status=201)

    messages.success(request, 'Session request sent.')
    return redirect('sessions_dashboard')


def _form_error(request, receiver, message):
    messages.error(request, message)
    return render(request, 'sessions/session_form.html', {
        'receiver': receiver,
        'duration_choices': Session.DURATION_CHOICES,
    }, status=400)


@login_required
@require_POST
def accept_session(request, session_id):
    session = get_object_or_404(Session, pk=session_id, receiver=request.user)
    if session.status != 'pending':
        return _json_error('Only pending sessions can be accepted.') if _wants_json(request) else _form_error_redirect(request, 'Only pending sessions can be accepted.')

    if Session.check_overlap(request.user, session.start_time, session.duration, exclude_id=session.pk):
        return _json_error('Accepting would overlap with another session.') if _wants_json(request) else _form_error_redirect(request, 'Accepting would overlap with another session.')
    if Session.check_overlap(session.sender, session.start_time, session.duration, exclude_id=session.pk):
        return _json_error('The requester has another accepted session at that time.') if _wants_json(request) else _form_error_redirect(request, 'The requester has another accepted session at that time.')

    return _save_response(request, session, 'accepted')


@login_required
@require_POST
def reject_session(request, session_id):
    session = get_object_or_404(Session, pk=session_id, receiver=request.user)
    if session.status != 'pending':
        return _json_error('Only pending sessions can be rejected.') if _wants_json(request) else _form_error_redirect(request, 'Only pending sessions can be rejected.')
    return _save_response(request, session, 'rejected')


@login_required
@require_POST
def respond_session(request, session_id):
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _json_error('Invalid JSON body.')

    action = data.get('action')
    if action == 'accept':
        return accept_session(request, session_id)
    if action == 'reject':
        return reject_session(request, session_id)
    return _json_error("action must be 'accept' or 'reject'.")


@login_required
@require_POST
def cancel_session(request, session_id):
    session = get_object_or_404(Session, _session_user_filter(request.user), pk=session_id)
    if session.status not in ['pending', 'accepted']:
        message = 'Only pending or scheduled sessions can be cancelled.'
        return _json_error(message) if _wants_json(request) else _form_error_redirect(request, message)
    return _save_response(request, session, 'cancelled')


@login_required
@require_POST
def reschedule_session(request, session_id):
    session = get_object_or_404(Session, _session_user_filter(request.user), pk=session_id)
    if session.status != 'accepted':
        return _json_error('Only scheduled sessions can be rescheduled.') if _wants_json(request) else _form_error_redirect(request, 'Only scheduled sessions can be rescheduled.')

    data = request.POST
    start_time = _parse_start_time(request, data)
    duration = _valid_duration(data.get('duration'))
    meeting_link = (data.get('meeting_link') or '').strip()
    reason = (data.get('reason') or '').strip()

    if start_time is None:
        return _form_error_redirect(request, 'Invalid reschedule date or time.')
    if start_time <= timezone.now():
        return _form_error_redirect(request, 'Rescheduled time must be in the future.')
    if duration is None:
        return _form_error_redirect(request, 'Duration must be 30, 60, or 90 minutes.')

    for participant in (session.sender, session.receiver):
        if Session.check_overlap(participant, start_time, duration, exclude_id=session.pk, statuses=['pending', 'accepted']):
            return _form_error_redirect(request, 'That time overlaps with an existing pending or scheduled session.')

    session.start_time = start_time
    session.duration = duration
    if meeting_link:
        session.meeting_link = meeting_link
    else:
        session.ensure_meeting_link(save=False)
    if reason:
        session.notes = (session.notes + '\n' if session.notes else '') + f'Rescheduled: {reason}'
    session.save(update_fields=['start_time', 'duration', 'meeting_link', 'notes', 'updated_at'])
    record_activity(request.user, 'session_rescheduled', {'session_id': session.pk})
    messages.success(request, 'Session rescheduled.')
    return redirect('sessions_dashboard')


@login_required
@require_POST
def mark_completed(request, session_id):
    session = get_object_or_404(Session, _session_user_filter(request.user), pk=session_id)
    if session.status not in ['accepted', 'completed', 'missed']:
        return _json_error('Only scheduled sessions can be completed.') if _wants_json(request) else _form_error_redirect(request, 'Only scheduled sessions can be completed.')
    if session.status == 'accepted' and session.end_time() > timezone.now():
        return _json_error('You can complete a session after it ends.') if _wants_json(request) else _form_error_redirect(request, 'You can complete a session after it ends.')

    if session.status != 'completed':
        session.status = 'completed'
        session.save(update_fields=['status', 'updated_at'])
        record_activity(request.user, 'session_completed', {'session_id': session.pk})

    if _wants_json(request):
        return JsonResponse({'ok': True, 'session': _session_dict(session, request.user)})

    messages.success(request, 'Session marked as completed.')
    return redirect('sessions_dashboard')


complete_session = mark_completed


@login_required
@require_POST
def mark_missed(request, session_id):
    session = get_object_or_404(Session, _session_user_filter(request.user), pk=session_id)
    if session.status != 'accepted':
        return _json_error('Only scheduled sessions can be marked missed.') if _wants_json(request) else _form_error_redirect(request, 'Only scheduled sessions can be marked missed.')
    if session.end_time() > timezone.now():
        return _json_error('You can mark a session missed only after it ends.') if _wants_json(request) else _form_error_redirect(request, 'You can mark a session missed only after it ends.')
    return _save_response(request, session, 'missed')


@login_required
@require_POST
def rate_session(request, session_id):
    session = get_object_or_404(Session, _session_user_filter(request.user), pk=session_id)

    if session.status != 'completed':
        return _json_error('You can rate only after the session is completed.') if _wants_json(request) else _form_error_redirect(request, 'You can rate only after the session is completed.')
    if session.reviews.filter(reviewer=request.user).exists():
        return _json_error('This session has already been rated.') if _wants_json(request) else _form_error_redirect(request, 'This session has already been rated.')

    try:
        rating = int(request.POST.get('rating'))
    except (TypeError, ValueError):
        rating = 0

    if rating < 1 or rating > 5:
        return _json_error('Rating must be between 1 and 5.') if _wants_json(request) else _form_error_redirect(request, 'Rating must be between 1 and 5.')

    feedback = request.POST.get('feedback', '').strip()
    SessionReview.objects.create(session=session, reviewer=request.user, rating=rating, feedback=feedback)

    if not session.is_rated:
        session.rating = rating
        session.feedback = feedback
        session.is_rated = True
        session.save(update_fields=['rating', 'feedback', 'is_rated', 'updated_at'])
    record_activity(request.user, 'session_rated', {'session_id': session.pk, 'rating': rating})

    if _wants_json(request):
        return JsonResponse({'ok': True, 'session': _session_dict(session, request.user)})

    messages.success(request, 'Review submitted.')
    return redirect('sessions_dashboard')


def _form_error_redirect(request, message):
    messages.error(request, message)
    return redirect('sessions_dashboard')


@login_required
def list_sessions(request):
    sessions = Session.objects.filter(_session_user_filter(request.user)).select_related('sender', 'receiver').order_by('-start_time')

    status_filter = request.GET.get('status', '')
    if status_filter:
        statuses = [status.strip() for status in status_filter.split(',') if status.strip()]
        sessions = sessions.filter(status__in=statuses)

    return JsonResponse({'ok': True, 'sessions': [_session_dict(session, request.user) for session in sessions]})


@login_required
def booked_slots(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    if not Session.users_are_connected(request.user, other):
        return _json_error('Not connected.', 403)

    sessions = Session.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user) | Q(sender=other) | Q(receiver=other),
        status__in=['pending', 'accepted'],
        start_time__gte=timezone.now(),
    ).values('start_time', 'duration')

    return JsonResponse({
        'ok': True,
        'booked_slots': [
            {
                'start': session['start_time'].isoformat(),
                'end': (session['start_time'] + timedelta(minutes=session['duration'])).isoformat(),
            }
            for session in sessions
        ],
    })


def _conversation_url_for(user, other):
    try:
        from messaging.models import Conversation

        conversation = Conversation.objects.filter(participants=user).filter(participants=other).first()
        if conversation:
            return reverse('conversation', kwargs={'conv_id': conversation.pk})
    except Exception:
        logger.exception('Failed to resolve conversation link')
    return reverse('inbox')


def _countdown_text(session):
    now = timezone.now()
    if session.status == 'pending':
        return 'Awaiting response'
    if session.status not in ['accepted']:
        return ''
    if now < session.start_time:
        delta = session.start_time - now
        total_minutes = max(1, int(delta.total_seconds() // 60))
        hours, minutes = divmod(total_minutes, 60)
        if hours:
            return f'Starts in {hours}h {minutes}m'
        return f'Starts in {minutes}m'
    if session.start_time <= now <= session.end_time():
        delta = session.end_time() - now
        total_minutes = max(1, int(delta.total_seconds() // 60))
        return f'Live now - {total_minutes}m left'
    return 'Session time has passed'


def _prepare_session_for_dashboard(session, user):
    other = session.receiver if session.sender == user else session.sender
    phase = session.phase
    session.other_user = other
    session.other_name = other.get_full_name() or other.username
    session.conversation_url = _conversation_url_for(user, other)
    session.countdown_text = _countdown_text(session)
    session.has_user_review = session.reviews.filter(reviewer=user).exists()
    session.can_accept = session.status == 'pending' and session.receiver_id == user.pk
    session.can_reject = session.can_accept
    session.can_cancel = (
        (session.status == 'pending' and session.sender_id == user.pk)
        or (session.status == 'accepted' and phase == 'upcoming' and user.pk in [session.sender_id, session.receiver_id])
    )
    session.can_reschedule = session.status == 'accepted' and phase == 'upcoming'
    session.can_join = session.can_join_now
    session.can_complete = session.status == 'accepted' and session.end_time() <= timezone.now()
    session.can_mark_missed = session.status == 'accepted' and session.end_time() <= timezone.now()
    session.can_review = session.status == 'completed' and not session.has_user_review
    if phase in ['upcoming', 'pending']:
        session.filter_phase = 'upcoming'
    elif phase == 'live_now':
        session.filter_phase = 'live'
    elif phase == 'completed':
        session.filter_phase = 'completed'
    elif phase in ['cancelled', 'rejected']:
        session.filter_phase = 'cancelled'
    else:
        session.filter_phase = 'missed'
    return session


@login_required
def sessions_dashboard(request):
    incoming = list(
        Session.objects.filter(receiver=request.user)
        .select_related('sender', 'receiver')
        .prefetch_related('reviews')
        .order_by('-created_at')
    )
    outgoing = list(
        Session.objects.filter(sender=request.user)
        .select_related('sender', 'receiver')
        .prefetch_related('reviews')
        .order_by('-created_at')
    )
    all_sessions = []
    seen = set()
    for session in incoming + outgoing:
        if session.pk in seen:
            continue
        seen.add(session.pk)
        all_sessions.append(_prepare_session_for_dashboard(session, request.user))

    incoming = [_prepare_session_for_dashboard(session, request.user) for session in incoming]
    outgoing = [_prepare_session_for_dashboard(session, request.user) for session in outgoing]

    return render(request, 'sessions/sessions_dashboard.html', {
        'incoming_sessions': incoming,
        'outgoing_sessions': outgoing,
        'all_sessions': all_sessions,
        'upcoming_count': len([s for s in all_sessions if s.filter_phase == 'upcoming']),
        'live_count': len([s for s in all_sessions if s.filter_phase == 'live']),
        'completed_count': len([s for s in all_sessions if s.filter_phase == 'completed']),
        'cancelled_count': len([s for s in all_sessions if s.filter_phase == 'cancelled']),
    })
