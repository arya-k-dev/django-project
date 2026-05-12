from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    # Onboarding flow
    path('onboarding/step1/', views.onboarding_step1, name='onboarding_step1'),
    path('onboarding/step2/', views.onboarding_step2, name='onboarding_step2'),
    path('onboarding/step3/', views.onboarding_step3, name='onboarding_step3'),
    path('onboarding/skip/', views.skip_onboarding, name='skip_onboarding'),
]
