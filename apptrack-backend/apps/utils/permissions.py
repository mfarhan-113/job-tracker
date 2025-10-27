"""
Custom permission classes for the application.
"""
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    message = _('You do not have permission to perform this action.')

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    Read only for non-admin users.
    """
    message = _('You do not have permission to perform this action.')

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users.
        return request.user and request.user.is_staff


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    """
    message = _('You do not have permission to access this resource.')

    def has_object_permission(self, request, view, obj):
        # Only the owner has access
        return obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to view or edit it.
    """
    message = _('You do not have permission to access this resource.')

    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
            
        # Owners have full access to their own objects
        return obj.user == request.user
