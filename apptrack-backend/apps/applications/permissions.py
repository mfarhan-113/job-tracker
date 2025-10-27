"""
Custom permissions for the applications app.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `owner` attribute or is related to an Application.
    """
    def has_object_permission(self, request, view, obj):
        # Handle direct ownership (e.g., Application model)
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # Handle related objects (e.g., Attachment, Reminder)
        if hasattr(obj, 'application'):
            return obj.application.owner == request.user
            
        # Handle cases where we might be checking against an Application instance directly
        if hasattr(obj, 'application_id'):
            from .models import Application
            try:
                app = Application.objects.get(pk=obj.application_id)
                return app.owner == request.user
            except Application.DoesNotExist:
                return False
                
        return False


class IsApplicationOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an application to access related objects.
    """
    def has_permission(self, request, view):
        # Get the application ID from the URL
        application_id = view.kwargs.get('application_pk')
        if not application_id:
            return False
            
        # Check if the application exists and is owned by the user
        from .models import Application
        return Application.objects.filter(
            id=application_id,
            owner=request.user
        ).exists()

    def has_object_permission(self, request, view, obj):
        # For object-level permissions, check if the object's application is owned by the user
        if hasattr(obj, 'application'):
            return obj.application.owner == request.user
        return False
