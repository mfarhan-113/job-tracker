"""
URL configuration for apptrack project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="AppTrack API",
        default_version='v1',
        description="API for tracking job and scholarship applications",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def health_check(request):
    """Health check endpoint for load balancers and monitoring"""
    return JsonResponse({"status": "ok"})

# Public endpoints that don't require authentication
urlpatterns = [
    # Health check
    path('api/health/', health_check, name='health-check'),

    path('api/users/', include('apps.users.urls', namespace='users')),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Root
    path('api/', include('apps.core.urls')),  # API root
    
    # API Documentation
    re_path(r'^api/docs/swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/docs/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Direct health check endpoint (bypasses all authentication)
    path('health/', lambda r: JsonResponse({'status': 'ok'}, status=200)),
    
    # API health check (might still require authentication)
    path('api/health/', include('apps.core.urls')),  # Health check endpoint
]

# API v1 endpoints (require authentication)
api_v1_patterns = [
    # API v1
    path('', include('apps.core.urls')),  # API root
    path('auth/', include(('apps.users.urls', 'users'), namespace='users')),
    path('applications/', include(('apps.applications.urls', 'applications'), namespace='applications')),
    path('reminders/', include(('apps.reminders.urls', 'reminders'), namespace='reminders')),
]

# Include v1 API patterns under /api/v1/
urlpatterns += [
    path('api/v1/', include((api_v1_patterns, 'v1'), namespace='v1')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
