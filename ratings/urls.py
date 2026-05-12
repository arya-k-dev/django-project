from django.urls import path
from . import views

urlpatterns = [
    path('rate/<int:user_id>/', views.rate_user, name='rate_user'),
    path('my-ratings/', views.my_ratings, name='my_ratings'),
]
