from django.apps import AppConfig


class SessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sessions'
    label = 'session_booking'
    verbose_name = 'Session Booking'
