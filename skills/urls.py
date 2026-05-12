from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.skill_add, name='skill_add'),
    path('edit/<int:pk>/', views.skill_edit, name='skill_edit'),
    path('manage/', views.skill_manage, name='skill_manage'),
    path('delete/<int:pk>/', views.skill_delete, name='skill_delete'),
    path('api/search/', views.skill_search_api, name='skill_search_api'),
    path('api/create/', views.skill_create_api, name='skill_create_api'),
    path('skills/', views.skill_list, name='skill_list'),
]
