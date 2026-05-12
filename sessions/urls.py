from django.urls import path
from . import views

urlpatterns = [
    path('', views.sessions_dashboard, name='sessions_dashboard'),

    path('session/create/<int:user_id>/', views.create_session, name='create_session'),
    path('session/accept/<int:session_id>/', views.accept_session, name='accept_session'),
    path('session/reject/<int:session_id>/', views.reject_session, name='reject_session'),
    path('session/cancel/<int:session_id>/', views.cancel_session, name='cancel_session'),
    path('session/reschedule/<int:session_id>/', views.reschedule_session, name='reschedule_session'),
    path('session/complete/<int:session_id>/', views.mark_completed, name='mark_completed'),
    path('session/missed/<int:session_id>/', views.mark_missed, name='mark_missed'),
    path('session/rate/<int:session_id>/', views.rate_session, name='rate_session'),

    # Compatibility endpoints for the existing chat/profile booking modal.
    path('api/create/',                views.create_session,     name='session_create'),
    path('api/<int:session_id>/respond/', views.respond_session, name='session_respond'),
    path('api/<int:session_id>/cancel/', views.cancel_session,   name='session_cancel'),
    path('api/<int:session_id>/reschedule/', views.reschedule_session, name='session_reschedule'),
    path('api/<int:session_id>/complete/', views.mark_completed, name='session_complete'),
    path('api/<int:session_id>/missed/', views.mark_missed, name='session_missed'),
    path('api/list/',                  views.list_sessions,      name='session_list'),
    path('api/slots/<int:user_id>/',   views.booked_slots,       name='session_booked_slots'),
]
