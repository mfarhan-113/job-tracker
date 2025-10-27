"""
URL configuration for the reminders app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'', views.ReminderViewSet, basename='reminder')

# The API URLs are now determined automatically by the router
app_name = 'reminders'
urlpatterns = [
    path('', include(router.urls)),
]
