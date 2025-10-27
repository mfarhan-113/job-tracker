"""
Custom middleware for the application.
"""
import time
import json
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests and responses.
    """
    
    def process_request(self, request):
        """
        Process the request and log its details.
        
        Args:
            request: The HTTP request object
            
        Returns:
            None: Always returns None to continue processing the request
        """
        # Skip logging for health checks and other noisy endpoints
        if any(path in request.path for path in ['/health', '/favicon.ico']):
            return None
            
        # Store the start time for the request
        request.start_time = time.time()
        
        # Log the request
        logger.info(
            'Request: %s %s',
            request.method,
            request.get_full_path(),
            extra={
                'request': {
                    'method': request.method,
                    'path': request.get_full_path(),
                    'query_params': dict(request.GET),
                    'headers': dict(request.headers),
                    'user': str(request.user) if hasattr(request, 'user') else None,
                },
            },
        )
        
        # Log request body for non-GET requests
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            try:
                body = json.loads(request.body) if request.body else {}
                logger.debug(
                    'Request body: %s',
                    body,
                    extra={'request_body': body}
                )
            except json.JSONDecodeError:
                logger.debug('Request body (non-JSON): %s', request.body)
        
        return None
    
    def process_response(self, request, response):
        """
        Process the response and log its details.
        
        Args:
            request: The HTTP request object
            response: The HTTP response object
            
        Returns:
            HttpResponse: The response object
        """
        # Skip logging for health checks and other noisy endpoints
        if any(path in request.path for path in ['/health', '/favicon.ico']):
            return response
        
        # Calculate the request duration
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # Log the response
        logger.info(
            'Response: %s %s - %s (%.2fms)',
            request.method,
            request.get_full_path(),
            response.status_code,
            duration * 1000,
            extra={
                'response': {
                    'status_code': response.status_code,
                    'headers': dict(response.items()),
                    'duration': duration,
                },
            },
        )
        
        # Log response content for error responses
        if response.status_code >= 400:
            try:
                content = json.loads(response.content) if hasattr(response, 'content') else {}
                logger.error(
                    'Error response: %s',
                    content,
                    extra={'response_content': content}
                )
            except (json.JSONDecodeError, AttributeError):
                logger.error('Error response (non-JSON): %s', response.content)
        
        return response


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to handle JWT authentication.
    This ensures that the user is set on the request object for all views.
    """
    def process_request(self, request):
        """Process the request and set the user from JWT if available."""
        # Skip if the user is already authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return None
            
        # Get the JWT token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
            from rest_framework_simplejwt.authentication import JWTAuthentication
            
            try:
                # Authenticate the user using the JWT token
                jwt_auth = JWTAuthentication()
                auth = jwt_auth.authenticate(request)
                
                if auth is not None:
                    # Set the user on the request
                    request.user = auth[0]
            except Exception as e:
                logger.warning('JWT authentication failed: %s', str(e))
        
        return None
