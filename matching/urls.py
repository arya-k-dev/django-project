from django.urls import path
from . import views

urlpatterns = [
    path('', views.matches_view, name='matches'),
    path('send/<int:user_id>/', views.send_request, name='send_request'),
    path('requests/', views.requests_view, name='requests'),
    path('respond/<int:pk>/', views.respond_request, name='respond_request'),
    path('complete/<int:pk>/', views.mark_completed, name='mark_completed'),
    path('accept/<int:request_id>/', views.accept_request, name='accept_request'),
    path('decline/<int:request_id>/', views.decline_request, name='decline_request'),
    path('cancel/<int:request_id>/', views.cancel_request, name='cancel_request'),
]
