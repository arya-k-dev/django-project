from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import json
import logging
from .models import Conversation, Message


logger = logging.getLogger(__name__)


def record_activity(user, action, metadata=None):
    try:
        from admin_dashboard.models import ActivityLog
        ActivityLog.record(user=user, action=action, metadata=metadata)
    except Exception:
        logger.exception('Failed to record activity: %s', action)


@login_required
def inbox(request):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('messages', 'participants').order_by('-created_at')

    conv_data = []
    for conv in conversations:
        other = conv.participants.exclude(id=request.user.id).first()
        last_msg = conv.last_message()
        unread = conv.unread_count(request.user)
        conv_data.append({
            'conversation': conv,
            'other_user': other,
            'last_message': last_msg,
            'unread': unread,
        })

    conv_data.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else x['conversation'].created_at, reverse=True)

    return render(request, 'messaging/inbox.html', {'conv_data': conv_data})


@login_required
def conversation_view(request, conv_id):
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    other_user = conversation.participants.exclude(id=request.user.id).first()

    # Mark messages as read
    conversation.messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    msgs = conversation.messages.all().order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                receiver=other_user,
                content=content,
            )
            record_activity(request.user, 'message_sent', {
                'message_id': msg.id,
                'conversation_id': conversation.id,
                'receiver_id': other_user.id,
            })
        return redirect('conversation', conv_id=conv_id)

    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages_list': msgs,
        'exchange': conversation.exchange_request,
        'they_teach_you': (
            conversation.exchange_request.receiver_teach_skills
            if conversation.exchange_request.sender == request.user
            else conversation.exchange_request.sender_teach_skills
        ),
        'you_teach_them': (
            conversation.exchange_request.sender_teach_skills
            if conversation.exchange_request.sender == request.user
            else conversation.exchange_request.receiver_teach_skills
        ),
    }
    return render(request, 'messaging/conversation.html', context)


@login_required
def poll_messages(request, conv_id):
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    since = request.GET.get('since', None)

    msgs = conversation.messages.all().order_by('timestamp')
    
    if since:
        try:
            since_dt = parse_datetime(since)
            if since_dt is None:
                since_dt = timezone.datetime.fromisoformat(since.replace(' ', 'T'))
            if timezone.is_naive(since_dt):
                since_dt = timezone.make_aware(since_dt, timezone.get_current_timezone())
            msgs = msgs.filter(timestamp__gt=since_dt)
        except (ValueError, TypeError):
            # If parsing fails, return empty list
            msgs = msgs.none()

    conversation.messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    data = [{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender': m.sender.get_full_name() or m.sender.username,
        'content': m.content,
        'timestamp': m.timestamp.isoformat().replace('T', ' '),
        'is_mine': m.sender_id == request.user.id,
    } for m in msgs]

    return JsonResponse({'messages': data})


@login_required
@require_POST
def send_message_api(request, conv_id):
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    other_user = conversation.participants.exclude(id=request.user.id).first()
    if other_user is None:
        return JsonResponse({'error': 'Conversation has no recipient'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = data.get('content', '').strip()

    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        receiver=other_user,
        content=content,
    )
    record_activity(request.user, 'message_sent', {
        'message_id': msg.id,
        'conversation_id': conversation.id,
        'receiver_id': other_user.id,
        'source': 'api',
    })

    return JsonResponse({
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat().replace('T', ' '),
        'sender': request.user.get_full_name() or request.user.username,
        'is_mine': True,
    })
