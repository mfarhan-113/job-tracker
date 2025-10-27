"""
Custom permissions for the apptrack project.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named 'owner'.
        return obj.owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named 'owner'.
        return obj.owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Global permission to only allow admin users to edit objects.
    Read permissions are allowed to any request.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users.
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to access it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Allow all read-only methods for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Allow full access to admin users
        if request.user and request.user.is_staff:
            return True
            
        # Allow write access to the owner
        return obj.owner == request.user
