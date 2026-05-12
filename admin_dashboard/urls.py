from django.urls import path

from . import views


urlpatterns = [
    path('users/', views.UserListAPIView.as_view(), name='admin_dashboard_users'),
    path('users/<int:user_id>/', views.UserDetailAPIView.as_view(), name='admin_dashboard_user_detail'),
    path('users/<int:user_id>/activate/', views.UserActivationAPIView.as_view(), name='admin_dashboard_user_activate'),
    path('users/<int:user_id>/deactivate/', views.UserDeactivateAPIView.as_view(), name='admin_dashboard_user_deactivate'),
    path('activity-logs/', views.ActivityLogListAPIView.as_view(), name='admin_dashboard_activity_logs'),
    path('analytics/matches/', views.MatchAnalyticsAPIView.as_view(), name='admin_dashboard_match_analytics'),
    path('analytics/skills/', views.MostRequestedSkillsAPIView.as_view(), name='admin_dashboard_skill_analytics'),
    path('analytics/match-score/', views.AverageMatchScoreAPIView.as_view(), name='admin_dashboard_match_score_analytics'),
    path('analytics/messages/', views.MessageAnalyticsAPIView.as_view(), name='admin_dashboard_message_analytics'),
    path('reports/users.csv', views.UsersCSVExportAPIView.as_view(), name='admin_dashboard_users_csv'),
    path('reports/matches.csv', views.MatchDataCSVExportAPIView.as_view(), name='admin_dashboard_matches_csv'),
    path('reports/activity-logs.csv', views.ActivityLogsCSVExportAPIView.as_view(), name='admin_dashboard_activity_logs_csv'),
]
