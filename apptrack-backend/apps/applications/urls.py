"""
URLs for the applications app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'applications', views.ApplicationViewSet, basename='application')

# Nested routers for attachments and reminders
applications_router = DefaultRouter()
applications_router.register(
    r'attachments',
    views.AttachmentViewSet,
    basename='application-attachment'
)
applications_router.register(
    r'reminders',
    views.ReminderViewSet,
    basename='application-reminder'
)

app_name = 'applications'

urlpatterns = [
    # Main application endpoints
    path('', include(router.urls)),
    
    # Nested endpoints for application-specific resources
    path(
        'applications/<uuid:application_pk>/',
        include(applications_router.urls)
    ),
    
    # Additional application actions
    path(
        'applications/<uuid:pk>/timeline/',
        views.ApplicationViewSet.as_view({'get': 'timeline'}),
        name='application-timeline'
    ),
    path(
        'applications/<uuid:pk>/status/',
        views.ApplicationViewSet.as_view({'patch': 'update_status'}),
        name='application-update-status'
    ),
]
