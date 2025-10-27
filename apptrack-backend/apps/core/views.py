"""Core views for the apptrack project."""
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.renderers import JSONRenderer


@api_view(['GET'])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def api_root(request, format=None):
    """API root view that lists all available endpoints."""
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    return Response({
        'users': {
            'list': f"{base_url}/api/v1/auth/users/",
            'register': f"{base_url}/api/v1/auth/register/",
            'login': f"{base_url}/api/v1/auth/login/",
            'refresh': f"{base_url}/api/v1/auth/refresh/",
        },
        'applications': {
            'list': f"{base_url}/api/v1/applications/",
            'create': f"{base_url}/api/v1/applications/",
        },
        'docs': {
            'swagger': f"{base_url}/api/docs/",
            'redoc': f"{base_url}/api/redoc/",
        },
        'health': {
            'check': f"{base_url}/health/"
        }
    })


from django.http import JsonResponse
from django.views import View

class HealthCheckView(View):
    """Health check endpoint that returns a JSON response."""
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status': 'ok'}, status=200)

# For backward compatibility
def health_check(request):
    return HealthCheckView.as_view()(request)
