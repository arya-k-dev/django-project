from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conv_id>/', views.conversation_view, name='conversation'),
    path('<int:conv_id>/poll/', views.poll_messages, name='poll_messages'),
    path('<int:conv_id>/send/', views.send_message_api, name='send_message_api'),
]
