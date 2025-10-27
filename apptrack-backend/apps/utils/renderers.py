"""
Custom renderers for the application.
"""
from rest_framework import renderers
from rest_framework.utils import json


class CustomJSONRenderer(renderers.JSONRenderer):
    """
    Custom JSON renderer that wraps the response in a standard format.
    """
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        response_dict = {
            'status': 'success',
            'data': data,
        }
        
        # Check for errors in the response
        response = renderer_context.get('response') if renderer_context else None
        if response and 400 <= response.status_code < 600:
            response_dict = {
                'status': 'error',
                'code': getattr(response, 'code', 'error'),
                'message': data.get('detail') if isinstance(data, dict) else str(data),
                'errors': data.get('errors') if isinstance(data, dict) else None
            }
        
        return json.dumps(response_dict)


class SuccessJSONRenderer(renderers.JSONRenderer):
    """
    Renderer that wraps the response in a standard success format.
    """
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON with a success wrapper.
        """
        response_dict = {
            'status': 'success',
            'data': data,
        }
        
        return json.dumps(response_dict)


class ErrorJSONRenderer(renderers.JSONRenderer):
    """
    Renderer that wraps the response in a standard error format.
    """
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON with an error wrapper.
        """
        response = renderer_context.get('response') if renderer_context else None
        
        response_dict = {
            'status': 'error',
            'code': getattr(response, 'code', 'error') if response else 'error',
            'message': data.get('detail') if isinstance(data, dict) else str(data),
            'errors': data.get('errors') if isinstance(data, dict) else None
        }
        
        return json.dumps(response_dict)
