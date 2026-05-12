import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ratings.models import Rating
from .forms import UserSkillForm
from .models import Skill, SkillCategory, UserSkill


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    categories = SkillCategory.objects.annotate(active_skill_count=Count('skills', filter=Q(skills__is_approved=True))).all()[:8]
    testimonials = (
        Rating.objects.exclude(feedback='')
        .select_related('rater', 'rated_user')
        .order_by('-created_at')[:6]
    )

    return render(request, 'home.html', {
        'categories': categories,
        'total_users': User.objects.count(),
        'total_skills': Skill.objects.count(),
        'testimonials': testimonials,
    })


def _category_icon_class(category_name):
    name = category_name.lower()
    if 'art' in name or 'design' in name:
        return 'fa-palette'
    if 'business' in name:
        return 'fa-briefcase'
    if 'cook' in name or 'food' in name:
        return 'fa-utensils'
    if 'craft' in name:
        return 'fa-scissors'
    if 'language' in name:
        return 'fa-language'
    if 'music' in name:
        return 'fa-music'
    if 'sport' in name or 'fitness' in name:
        return 'fa-dumbbell'
    if 'tech' in name or 'code' in name or 'program' in name:
        return 'fa-laptop-code'
    return 'fa-layer-group'


def category_detail(request, slug):
    from matching.models import ExchangeRequest

    category = get_object_or_404(SkillCategory, slug=slug)
    search = request.GET.get('q', '').strip()
    level = request.GET.get('level', '').strip()
    role = request.GET.get('role', '').strip()

    skills = Skill.objects.filter(category=category, is_approved=True).annotate(
        mentor_count=Count('user_skills', filter=Q(user_skills__skill_type='teach'), distinct=True),
        learner_count=Count('user_skills', filter=Q(user_skills__skill_type='learn'), distinct=True),
        activity_count=Count('user_skills', distinct=True),
    )
    if search:
        skills = skills.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if level:
        skills = skills.filter(user_skills__level=level).distinct()
    if role == 'mentor':
        skills = skills.filter(user_skills__skill_type='teach').distinct()
    elif role == 'learner':
        skills = skills.filter(user_skills__skill_type='learn').distinct()

    skills = skills.order_by('-activity_count', 'name')

    user_skills = UserSkill.objects.filter(skill__category=category).select_related('user', 'skill', 'user__profile')
    if search:
        user_skills = user_skills.filter(Q(skill__name__icontains=search) | Q(user__username__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search))
    if level:
        user_skills = user_skills.filter(level=level)
    if role == 'mentor':
        user_skills = user_skills.filter(skill_type='teach')
    elif role == 'learner':
        user_skills = user_skills.filter(skill_type='learn')

    users = User.objects.filter(id__in=user_skills.values('user_id'), is_active=True).distinct()[:8]
    user_cards = []
    for profile_user in users:
        relevant = UserSkill.objects.filter(user=profile_user, skill__category=category).select_related('skill')
        offered = list(relevant.filter(skill_type='teach').values_list('skill__name', flat=True)[:4])
        wanted = list(relevant.filter(skill_type='learn').values_list('skill__name', flat=True)[:4])
        user_cards.append({
            'user': profile_user,
            'profile': getattr(profile_user, 'profile', None),
            'offered': offered,
            'wanted': wanted,
            'credibility': min(100, (len(offered) * 18) + (len(wanted) * 10) + 42),
        })

    category_user_ids = list(UserSkill.objects.filter(skill__category=category).values_list('user_id', flat=True).distinct())
    active_exchanges = ExchangeRequest.objects.filter(
        Q(sender_id__in=category_user_ids) | Q(receiver_id__in=category_user_ids),
        status__in=['accepted', 'completed'],
    ).distinct().count()

    teach_skills = list(
        UserSkill.objects.filter(skill__category=category, skill_type='teach')
        .values_list('skill__name', flat=True)
        .annotate(total=Count('id'))
        .order_by('-total', 'skill__name')[:6]
    )
    learn_skills = list(
        UserSkill.objects.filter(skill__category=category, skill_type='learn')
        .values_list('skill__name', flat=True)
        .annotate(total=Count('id'))
        .order_by('-total', 'skill__name')[:6]
    )
    exchange_chips = [
        {'teach': teach, 'learn': learn}
        for teach, learn in zip(teach_skills, learn_skills)
        if teach != learn
    ][:6]
    if not exchange_chips:
        trending_names = list(skills.values_list('name', flat=True)[:6])
        exchange_chips = [
            {'teach': name, 'learn': trending_names[index + 1]}
            for index, name in enumerate(trending_names[:-1])
        ][:4]

    context = {
        'category': category,
        'category_icon_class': _category_icon_class(category.name),
        'skills': skills[:12],
        'user_cards': user_cards,
        'exchange_chips': exchange_chips,
        'active_exchanges': active_exchanges,
        'mentor_count': UserSkill.objects.filter(skill__category=category, skill_type='teach').values('user').distinct().count(),
        'learner_count': UserSkill.objects.filter(skill__category=category, skill_type='learn').values('user').distinct().count(),
        'skill_count': Skill.objects.filter(category=category, is_approved=True).count(),
        'selected_search': search,
        'selected_level': level,
        'selected_role': role,
    }
    return render(request, 'skills/category_detail.html', context)


@login_required
def dashboard(request):
    from matching.models import ExchangeRequest
    from matching.views import get_matches_for_user
    from messaging.models import Message
    from sessions.models import Session

    user = request.user
    teach_skills = UserSkill.objects.filter(user=user, skill_type='teach').select_related('skill')
    learn_skills = UserSkill.objects.filter(user=user, skill_type='learn').select_related('skill')

    received_all = ExchangeRequest.objects.filter(receiver=user).order_by('-created_at')
    pending_requests = received_all.filter(status='pending')
    received_requests = received_all[:5]
    sent_requests = ExchangeRequest.objects.filter(sender=user).order_by('-created_at')[:5]
    active_exchanges = ExchangeRequest.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status='accepted',
    ).select_related('sender', 'receiver')

    for exchange in active_exchanges:
        exchange.other_user = exchange.get_other_user(user)

    # Sessions
    from django.utils import timezone
    upcoming_sessions = Session.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status='accepted',
        start_time__gte=timezone.now(),
    ).select_related('sender', 'receiver').order_by('start_time')[:4]

    pending_sessions_count = Session.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status='pending',
    ).count()

    context = {
        'teach_skills': teach_skills,
        'learn_skills': learn_skills,
        'matches': get_matches_for_user(user, limit=5),
        'pending_requests': pending_requests,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'active_exchanges': active_exchanges,
        'unread_messages': Message.objects.filter(receiver=user, is_read=False).count(),
        'upcoming_sessions': upcoming_sessions,
        'pending_sessions_count': pending_sessions_count,
    }
    return render(request, 'dashboard.html', context)


@login_required
def skill_add(request):
    if request.method == 'POST':
        form = UserSkillForm(request.POST)
        if form.is_valid():
            user_skill = form.save(commit=False)
            user_skill.user = request.user

            duplicate = UserSkill.objects.filter(
                user=request.user,
                skill=user_skill.skill,
                skill_type=user_skill.skill_type,
            ).exists()
            if duplicate:
                messages.warning(request, 'You already have this skill listed.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Skill already exists.'}, status=409)
            else:
                user_skill.save()
                messages.success(request, f'Skill "{user_skill.skill.name}" added.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Skill added.'})
            return redirect('skill_manage')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = UserSkillForm(initial={'skill_type': 'teach'})

    categories = SkillCategory.objects.prefetch_related('skills').all()
    return render(request, 'skills/skill_add.html', {'form': form, 'categories': categories})


@login_required
def skill_edit(request, pk):
    user_skill = get_object_or_404(UserSkill, pk=pk, user=request.user)

    if request.method == 'POST':
        form = UserSkillForm(request.POST, instance=user_skill)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.user = request.user

            duplicate = UserSkill.objects.filter(
                user=request.user,
                skill=updated.skill,
                skill_type=updated.skill_type,
            ).exclude(pk=user_skill.pk).exists()
            if duplicate:
                form.add_error(None, 'You already have this skill listed.')
            else:
                updated.save()
                messages.success(request, f'Skill "{updated.skill.name}" updated.')
                return redirect('skill_manage')
    else:
        form = UserSkillForm(instance=user_skill)

    return render(request, 'skills/skill_edit.html', {
        'form': form,
        'user_skill': user_skill,
    })


@login_required
def skill_manage(request):
    teach_skills = UserSkill.objects.filter(
        user=request.user,
        skill_type='teach',
    ).select_related('skill', 'skill__category')
    learn_skills = UserSkill.objects.filter(
        user=request.user,
        skill_type='learn',
    ).select_related('skill', 'skill__category')
    return render(request, 'skills/skill_manage.html', {
        'teach_skills': teach_skills,
        'learn_skills': learn_skills,
    })


@login_required
def skill_delete(request, pk):
    user_skill = get_object_or_404(UserSkill, pk=pk, user=request.user)
    if request.method == 'POST':
        skill_name = user_skill.skill.name
        user_skill.delete()
        messages.success(request, f'Skill "{skill_name}" removed.')
    return redirect('skill_manage')


def skill_search_api(request):
    query = request.GET.get('q', '').strip()
    skills = Skill.objects.filter(is_approved=True)
    if query:
        skills = skills.filter(name__icontains=query)

    data = [
        {'id': skill.id, 'name': skill.name, 'category': skill.category.name if skill.category else ''}
        for skill in skills.select_related('category').order_by('name')[:10]
    ]
    return JsonResponse({'skills': data})


@require_POST
def skill_create_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    category_id = data.get('category_id') or None
    if not name:
        return JsonResponse({'error': 'Name required'}, status=400)

    skill = Skill.objects.filter(name__iexact=name).first()
    created = False
    if not skill:
        skill = Skill.objects.create(name=name, category_id=category_id)
        created = True

    return JsonResponse({'id': skill.id, 'name': skill.name, 'created': created})


@login_required
def skill_list(request):
    return redirect('skill_add')
