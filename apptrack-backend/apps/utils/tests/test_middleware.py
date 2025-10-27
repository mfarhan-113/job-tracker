"""
Tests for the custom middleware.
"""
import json
from unittest.mock import Mock, patch
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from ..middleware import RequestResponseLoggingMiddleware, JWTAuthenticationMiddleware

User = get_user_model()


class TestRequestResponseLoggingMiddleware(TestCase):
    """Tests for RequestResponseLoggingMiddleware."""
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.factory = RequestFactory()
        self.middleware = RequestResponseLoggingMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.utils.middleware.logger')
    def test_process_request_skips_health_check(self, mock_logger):
        """Test that health check requests are not logged."""
        request = self.factory.get('/health')
        self.middleware.process_request(request)
        mock_logger.info.assert_not_called()
    
    @patch('apps.utils.middleware.logger')
    def test_process_request_logs_request(self, mock_logger):
        """Test that regular requests are logged."""
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        self.middleware.process_request(request)
        
        # Check that logger.info was called with the expected arguments
        args, kwargs = mock_logger.info.call_args
        self.assertEqual(args[0], 'Request: %s %s')
        self.assertEqual(args[1], 'GET')
        self.assertEqual(args[2], '/api/test/')
        self.assertIn('request', kwargs['extra'])
        self.assertEqual(kwargs['extra']['request']['method'], 'GET')
        self.assertEqual(kwargs['extra']['request']['path'], '/api/test/')
    
    @patch('apps.utils.middleware.logger')
    def test_process_response_logs_response(self, mock_logger):
        """Test that responses are logged with duration."""
        request = self.factory.get('/api/test/')
        request.start_time = 0  # Set a fixed start time for testing
        response = JsonResponse({'status': 'ok'})
        
        self.middleware.process_response(request, response)
        
        # Check that logger.info was called with the expected arguments
        args, kwargs = mock_logger.info.call_args
        self.assertEqual(args[0], 'Response: %s %s - %s (%.2fms)')
        self.assertEqual(args[1], 'GET')
        self.assertEqual(args[2], '/api/test/')
        self.assertEqual(args[3], 200)
        self.assertIn('response', kwargs['extra'])
        self.assertEqual(kwargs['extra']['response']['status_code'], 200)


class TestJWTAuthenticationMiddleware(TestCase):
    """Tests for JWTAuthenticationMiddleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
        self.middleware = JWTAuthenticationMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('rest_framework_simplejwt.authentication.JWTAuthentication.authenticate')
    def test_valid_jwt_token(self, mock_authenticate):
        """Test that a valid JWT token authenticates the user."""
        # Mock the JWT authentication
        mock_authenticate.return_value = (self.user, None)
        
        # Create a request with a JWT token
        request = self.factory.get(
            '/api/protected/',
            HTTP_AUTHORIZATION='Bearer valid.token.here'
        )
        
        # Process the request through the middleware
        self.middleware.process_request(request)
        
        # Check that the user was set on the request
        self.assertEqual(request.user, self.user)
    
    @patch('rest_framework_simplejwt.authentication.JWTAuthentication.authenticate')
    def test_invalid_jwt_token(self, mock_authenticate):
        """Test that an invalid JWT token doesn't authenticate the user."""
        # Mock the JWT authentication to return None
        mock_authenticate.return_value = None
        
        # Create a request with an invalid JWT token
        request = self.factory.get(
            '/api/protected/',
            HTTP_AUTHORIZATION='Bearer invalid.token.here'
        )
        
        # Process the request through the middleware
        self.middleware.process_request(request)
        
        # Check that the user is not authenticated
        self.assertFalse(hasattr(request, 'user') and request.user.is_authenticated)
    
    def test_no_authorization_header(self):
        """Test that requests without an Authorization header are handled."""
        # Create a request without an Authorization header
        request = self.factory.get('/api/public/')
        
        # Process the request through the middleware
        self.middleware.process_request(request)
        
        # Check that no user was set
        self.assertFalse(hasattr(request, 'user') and request.user.is_authenticated)
