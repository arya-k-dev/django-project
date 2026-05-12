from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from matching.models import ExchangeRequest
from .models import Rating
from .forms import RatingForm


@login_required
def rate_user(request, user_id):
    rated_user = get_object_or_404(User, id=user_id)

    # Find the completed exchange between current user and rated_user
    exchange = ExchangeRequest.objects.filter(
        Q(sender=request.user, receiver=rated_user) |
        Q(sender=rated_user, receiver=request.user),
        status='completed'
    ).first()

    if not exchange:
        messages.error(request, 'No completed exchange found with this user.')
        return redirect('dashboard')

    # Check if already rated
    already_rated = Rating.objects.filter(exchange_request=exchange, rater=request.user).exists()
    if already_rated:
        messages.info(request, 'You have already rated this exchange.')
        return redirect('profile_view', username=rated_user.username)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.exchange_request = exchange
            rating.rater = request.user
            rating.rated_user = rated_user
            rating.save()
            messages.success(request, f'Thank you for rating {rated_user.get_full_name() or rated_user.username}!')
            return redirect('profile_view', username=rated_user.username)
    else:
        form = RatingForm()

    return render(request, 'ratings/rate.html', {
        'form': form,
        'rated_user': rated_user,
        'exchange': exchange,
    })


@login_required
def my_ratings(request):
    received = Rating.objects.filter(rated_user=request.user).select_related('rater', 'exchange_request')
    given = Rating.objects.filter(rater=request.user).select_related('rated_user', 'exchange_request')
    return render(request, 'ratings/my_ratings.html', {'received': received, 'given': given})
