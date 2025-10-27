"""
Custom exceptions for the application.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class ApplicationError(APIException):
    """Base exception for application-specific errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('An error occurred.')
    default_code = 'application_error'


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('The requested resource was not found.')
    default_code = 'not_found'


class PermissionDeniedError(ApplicationError):
    """Raised when a user doesn't have permission to perform an action."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('You do not have permission to perform this action.')
    default_code = 'permission_denied'


class ValidationError(ValidationError):
    """Raised when invalid data is provided."""
    default_code = 'validation_error'


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # If the exception is a ValidationError, format the response
        if isinstance(exc, ValidationError):
            error_data = {
                'status': 'error',
                'code': getattr(exc, 'code', 'validation_error'),
                'message': _('Validation error'),
                'errors': {}
            }
            
            # Handle both dictionary and list-style validation errors
            if isinstance(exc.detail, dict):
                for field, errors in exc.detail.items():
                    if isinstance(errors, list):
                        error_data['errors'][field] = [str(error) for error in errors]
                    else:
                        error_data['errors'][field] = [str(errors)]
            elif isinstance(exc.detail, list):
                error_data['errors']['non_field_errors'] = [str(error) for error in exc.detail]
            else:
                error_data['errors']['non_field_errors'] = [str(exc.detail)]
                
            response.data = error_data
        
        # Handle APIException subclasses
        elif isinstance(exc, APIException):
            error_data = {
                'status': 'error',
                'code': getattr(exc, 'code', exc.default_code),
                'message': str(exc.detail) if exc.detail else str(exc),
            }
            
            # Add error details if available
            if hasattr(exc, 'get_full_details'):
                error_data['errors'] = exc.get_full_details()
                
            response.data = error_data
    
    return response
