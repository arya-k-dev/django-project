from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
import logging

from .forms import LoginForm, ProfileUpdateForm, SignUpForm
from .models import UserProfile


logger = logging.getLogger(__name__)


def record_activity(user, action, metadata=None):
    try:
        from admin_dashboard.models import ActivityLog
        ActivityLog.record(user=user, action=action, metadata=metadata)
    except Exception:
        logger.exception('Failed to record activity: %s', action)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}. Let's set up your profile.")
            return redirect('onboarding_step1')
    else:
        form = SignUpForm()

    features = [
        'Smart reciprocal matching algorithm',
        'Built-in messaging between partners',
        'Community rating and review system',
        'Always free - no premium tiers',
    ]
    return render(request, 'accounts/signup.html', {'form': form, 'features': features})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}.')
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_setup(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            record_activity(request.user, 'profile_update', {'source': 'profile_setup'})
            messages.success(request, 'Profile updated successfully.')
            return redirect('skill_add')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/profile_setup.html', {'form': form})


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            record_activity(request.user, 'profile_update', {'source': 'profile_edit'})
            messages.success(request, 'Profile updated.')
            return redirect('profile_view', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=profile_user)

    from matching.models import ExchangeRequest
    from ratings.models import Rating
    from skills.models import UserSkill

    teach_skills = UserSkill.objects.filter(user=profile_user, skill_type='teach').select_related('skill')
    learn_skills = UserSkill.objects.filter(user=profile_user, skill_type='learn').select_related('skill')
    ratings = Rating.objects.filter(rated_user=profile_user).select_related('rater').order_by('-created_at')[:5]

    connection_status = None
    conversation = None
    if request.user.is_authenticated and request.user != profile_user:
        exchange_request = ExchangeRequest.objects.filter(
            Q(sender=request.user, receiver=profile_user) |
            Q(sender=profile_user, receiver=request.user)
        ).first()
        if exchange_request:
            connection_status = exchange_request.status
            if exchange_request.status == 'accepted':
                conversation = getattr(exchange_request, 'conversation', None)

    return render(request, 'accounts/profile_view.html', {
        'profile_user': profile_user,
        'profile': profile,
        'teach_skills': teach_skills,
        'learn_skills': learn_skills,
        'ratings': ratings,
        'connection_status': connection_status,
        'conversation': conversation,
        'is_own_profile': request.user == profile_user,
    })


@login_required
def onboarding_step1(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            record_activity(request.user, 'profile_update', {'source': 'onboarding_step1'})
            messages.success(request, "Profile updated. Now let's add your skills.")
            return redirect('onboarding_step2')
        else:
            # Debug: Print form errors to help identify issues
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                print(f"Field {field}: {errors}")
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/onboarding_step1.html', {
        'form': form,
        'step': 1,
        'total_steps': 3,
    })


def _save_onboarding_skill(request, skill_type):
    from skills.forms import UserSkillForm
    from skills.models import UserSkill

    data = request.POST.copy()
    data['skill_type'] = skill_type
    form = UserSkillForm(data)
    if not form.is_valid():
        return form, False

    user_skill = form.save(commit=False)
    user_skill.user = request.user
    user_skill.skill_type = skill_type

    if UserSkill.objects.filter(
        user=request.user,
        skill=user_skill.skill,
        skill_type=skill_type,
    ).exists():
        label = 'teaching skill' if skill_type == 'teach' else 'learning goal'
        messages.warning(request, f'That {label} is already on your profile.')
        return form, False

    user_skill.save()
    return form, True


@login_required
def onboarding_step2(request):
    from skills.forms import UserSkillForm
    from skills.models import UserSkill

    if request.method == 'POST':
        form, saved = _save_onboarding_skill(request, 'teach')
        if saved:
            messages.success(request, "Teaching skill added. Let's add what you want to learn.")
            return redirect('onboarding_step3')
    else:
        form = UserSkillForm(initial={'skill_type': 'teach'})

    teach_skills = UserSkill.objects.filter(user=request.user, skill_type='teach').select_related('skill')
    return render(request, 'accounts/onboarding_step2.html', {
        'form': form,
        'teach_skills': teach_skills,
        'step': 2,
        'total_steps': 3,
    })


@login_required
def onboarding_step3(request):
    from skills.forms import UserSkillForm
    from skills.models import UserSkill

    if request.method == 'POST':
        form, saved = _save_onboarding_skill(request, 'learn')
        if saved:
            messages.success(request, 'Learning goal added. Setup complete.')
            return redirect('dashboard')
    else:
        form = UserSkillForm(initial={'skill_type': 'learn'})

    learn_skills = UserSkill.objects.filter(user=request.user, skill_type='learn').select_related('skill')
    return render(request, 'accounts/onboarding_step3.html', {
        'form': form,
        'learn_skills': learn_skills,
        'step': 3,
        'total_steps': 3,
    })


@login_required
def skip_onboarding(request):
    messages.info(request, 'You can complete your profile anytime from settings.')
    return redirect('dashboard')
