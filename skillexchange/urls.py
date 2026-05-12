from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from skills import views as skill_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', skill_views.home, name='home'),
    path('categories/<slug:slug>/', skill_views.category_detail, name='category_detail'),
    path('dashboard/', skill_views.dashboard, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('skills/', include('skills.urls')),
    path('matching/', include('matching.urls')),
    path('messages/', include('messaging.urls')),
    path('ratings/', include('ratings.urls')),
    path('admin-dashboard/', include('admin_dashboard.urls')),
    path('sessions/', include('sessions.urls')),
]

if settings.STATICFILES_DIRS:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
