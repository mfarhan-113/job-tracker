"""
URLs for the core app.
"""
from django.urls import path
from .views import HealthCheckView, api_root

app_name = 'core'

urlpatterns = [
    # Health check endpoint (public)
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # API Root (requires authentication)
    path('', api_root, name='api-root'),
]
