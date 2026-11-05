"""TMS URL Configuration - Master Router"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('accounts.dashboard_urls', namespace='dashboard')),
    path('students/', include('students.urls', namespace='students')),
    path('transport/', include('transport.urls', namespace='transport')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('operations/', include('operations.urls', namespace='operations')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('ai/', include('ai_predictor.urls', namespace='ai_predictor')),
    # Root redirect to dashboard
    path('', lambda request: __import__('django.shortcuts', fromlist=['redirect']).redirect('dashboard:home')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
