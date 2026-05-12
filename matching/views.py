from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging

from skills.models import Skill, SkillCategory, UserSkill
from .models import ExchangeRequest


logger = logging.getLogger(__name__)


def record_activity(user, action, metadata=None):
    try:
        from admin_dashboard.models import ActivityLog
        ActivityLog.record(user=user, action=action, metadata=metadata)
    except Exception:
        logger.exception('Failed to record activity: %s', action)


# ---------------------------------------
# MATCHING LOGIC
# ---------------------------------------

def compute_match_score(user, other_user):
    """
    Reciprocal matching algorithm
    """
    user_teach = set(UserSkill.objects.filter(user=user, skill_type='teach').values_list('skill_id', flat=True))
    user_learn = set(UserSkill.objects.filter(user=user, skill_type='learn').values_list('skill_id', flat=True))
    other_teach = set(UserSkill.objects.filter(user=other_user, skill_type='teach').values_list('skill_id', flat=True))
    other_learn = set(UserSkill.objects.filter(user=other_user, skill_type='learn').values_list('skill_id', flat=True))

    i_can_teach_them = user_teach & other_learn
    they_can_teach_me = other_teach & user_learn

    score = len(i_can_teach_them) * 2 + len(they_can_teach_me) * 2

    if i_can_teach_them and they_can_teach_me:
        score += 3

    return score, list(i_can_teach_them), list(they_can_teach_me)


def get_matches_for_user(user, limit=20):
    all_other_users = User.objects.exclude(id=user.id).filter(is_active=True)

    # Exclude already connected users
    connected_ids = ExchangeRequest.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).values_list('sender_id', 'receiver_id')

    excluded_ids = set()
    for s, r in connected_ids:
        excluded_ids.add(s)
        excluded_ids.add(r)
    excluded_ids.discard(user.id)

    candidates = all_other_users.exclude(id__in=excluded_ids)

    matches = []
    for other in candidates:
        score, i_teach_them, they_teach_me = compute_match_score(user, other)

        if score > 0:
            profile = getattr(other, 'profile', None)

            matches.append({
                'user': other,
                'profile': profile,
                'score': score,
                'i_teach_them': list(
                    UserSkill.objects.filter(
                        user=user,
                        skill_type='teach',
                        skill_id__in=i_teach_them
                    ).values_list('skill__name', flat=True)
                ),
                'they_teach_me': list(
                    UserSkill.objects.filter(
                        user=other,
                        skill_type='teach',
                        skill_id__in=they_teach_me
                    ).values_list('skill__name', flat=True)
                ),
            })

    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:limit]


# ---------------------------------------
# VIEWS
# ---------------------------------------

@login_required
def matches_view(request):
    matches = get_matches_for_user(request.user)

    category_id = request.GET.get('category') or ''
    availability = request.GET.get('availability') or ''
    sort = request.GET.get('sort') or '-score'

    if category_id and category_id.isdigit():
        category_skill_names = set(
            Skill.objects.filter(category_id=category_id).values_list('name', flat=True)
        )
        matches = [
            match for match in matches
            if category_skill_names.intersection(match['i_teach_them'] + match['they_teach_me'])
        ]

    if availability:
        matches = [
            match for match in matches
            if match.get('profile') and match['profile'].availability == availability
        ]

    if sort == 'score':
        matches = sorted(matches, key=lambda match: match['score'])
    else:
        matches = sorted(matches, key=lambda match: match['score'], reverse=True)

    received = ExchangeRequest.objects.filter(
        receiver=request.user,
        status='pending'
    ).order_by('-created_at')

    sent = ExchangeRequest.objects.filter(
        sender=request.user,
        status='pending'
    ).order_by('-created_at')

    context = {
        'matches': matches,
        'incoming_requests': received,
        'outgoing_requests': sent,
        'skill_categories': SkillCategory.objects.order_by('name'),
        'selected_category': category_id,
        'selected_availability': availability,
        'selected_sort': sort,
    }

    return render(request, 'matching/matches.html', context)


@login_required
@require_POST
def send_request(request, user_id):
    receiver = get_object_or_404(User, id=user_id)

    if receiver == request.user:
        messages.error(request, "You can't send a request to yourself.")
        return redirect('matches')

    existing = ExchangeRequest.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user)
    ).first()

    if existing:
        messages.warning(request, f'A request with {receiver.username} already exists.')
        return redirect('matches')

    score, i_teach, they_teach = compute_match_score(request.user, receiver)

    msg = request.POST.get('message', '')

    exchange_request = ExchangeRequest.objects.create(
        sender=request.user,
        receiver=receiver,
        message=msg,
        sender_teach_skills=list(
            UserSkill.objects.filter(
                user=request.user,
                skill_type='teach',
                skill_id__in=i_teach
            ).values_list('skill__name', flat=True)
        ),
        receiver_teach_skills=list(
            UserSkill.objects.filter(
                user=receiver,
                skill_type='teach',
                skill_id__in=they_teach
            ).values_list('skill__name', flat=True)
        ),
        match_score=score,
    )
    record_activity(request.user, 'match_request_sent', {
        'exchange_request_id': exchange_request.id,
        'receiver_id': receiver.id,
        'match_score': score,
    })

    messages.success(
        request,
        f'Request sent to {receiver.get_full_name() or receiver.username}!'
    )
    return redirect('matches')


@login_required
def requests_view(request):
    received = ExchangeRequest.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    sent = ExchangeRequest.objects.filter(
        sender=request.user
    ).order_by('-created_at')

    return render(request, 'matching/requests.html', {
        'received': received,
        'sent': sent
    })


@login_required
def respond_request(request, pk):
    exchange_req = get_object_or_404(
        ExchangeRequest,
        pk=pk,
        receiver=request.user
    )

    action = request.POST.get('action')

    if action == 'accept':
        exchange_req.status = 'accepted'
        exchange_req.save()

        # Create conversation
        from messaging.models import Conversation
        conv, _ = Conversation.objects.get_or_create(
            exchange_request=exchange_req
        )
        conv.participants.set([
            exchange_req.sender,
            exchange_req.receiver
        ])
        record_activity(request.user, 'match_request_accepted', {
            'exchange_request_id': exchange_req.id,
            'sender_id': exchange_req.sender_id,
        })

        messages.success(
            request,
            f"You accepted the request from {exchange_req.sender.username}!"
        )

    elif action == 'decline':
        exchange_req.status = 'declined'
        exchange_req.save()
        record_activity(request.user, 'match_request_declined', {
            'exchange_request_id': exchange_req.id,
            'sender_id': exchange_req.sender_id,
        })

        messages.info(
            request,
            f"Request from {exchange_req.sender.username} declined."
        )

    return redirect('requests')


@login_required
def mark_completed(request, pk):
    exchange_req = get_object_or_404(
        ExchangeRequest,
        pk=pk,
        status='accepted'
    )

    if request.user not in [exchange_req.sender, exchange_req.receiver]:
        messages.error(request, 'Unauthorized.')
        return redirect('requests')

    exchange_req.status = 'completed'
    exchange_req.save()
    record_activity(request.user, 'match_request_completed', {
        'exchange_request_id': exchange_req.id,
        'other_user_id': exchange_req.get_other_user(request.user).id,
    })

    messages.success(
        request,
        'Exchange marked as completed! Please rate your partner.'
    )

    return redirect(
        'rate_user',
        user_id=exchange_req.get_other_user(request.user).id
    )
@login_required
def send_connection_request(request, user_id):
    # Redirect to your existing logic
    return send_request(request, user_id)
@login_required
def accept_request(request, request_id):
    request.POST = request.POST.copy()
    request.POST['action'] = 'accept'
    return respond_request(request, request_id)


@login_required
def reject_request(request, request_id):
    request.POST = request.POST.copy()
    request.POST['action'] = 'decline'
    return respond_request(request, request_id)
@login_required
def decline_request(request, request_id):
    request.POST = request.POST.copy()
    request.POST['action'] = 'decline'
    return respond_request(request, request_id)
@login_required
def cancel_request(request, request_id):
    exchange_req = get_object_or_404(
        ExchangeRequest,
        pk=request_id,
        sender=request.user
    )

    if exchange_req.status == 'pending':
        exchange_id = exchange_req.id
        receiver_id = exchange_req.receiver_id
        exchange_req.delete()
        record_activity(request.user, 'match_request_cancelled', {
            'exchange_request_id': exchange_id,
            'receiver_id': receiver_id,
        })
        messages.info(request, "Request cancelled.")
    else:
        messages.warning(request, "You can only cancel pending requests.")

    return redirect('requests')
