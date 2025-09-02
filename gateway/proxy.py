import json
import logging
import requests
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .utils import build_downstream_url, sanitize_headers, get_service_config

logger = logging.getLogger('gateway')


class ProxyService:
    """Service for proxying requests to downstream services."""
    
    def __init__(self):
        self.session = requests.Session()
    
    def proxy_request(self, request, service_name, path=''):
        """Proxy a request to a downstream service."""
        try:
            # Get service configuration
            service_config = get_service_config(service_name)
            if not service_config:
                return JsonResponse({
                    'error': 'Service not found',
                    'message': f'Service "{service_name}" is not configured'
                }, status=404)
            
            # Check if service is healthy
            if not service_config.get('is_healthy', True):
                return JsonResponse({
                    'error': 'Service unavailable',
                    'message': f'Service "{service_name}" is currently unavailable'
                }, status=503)
            
            # Build the target URL
            target_url = build_downstream_url(service_name, path)
            
            # Prepare headers
            headers = sanitize_headers(dict(request.headers))
            headers['X-Forwarded-For'] = request.META.get('REMOTE_ADDR', '')
            headers['X-Forwarded-Proto'] = request.scheme
            headers['X-Forwarded-Host'] = request.get_host()
            
            # Prepare request data
            request_data = {
                'method': request.method,
                'url': target_url,
                'headers': headers,
                'timeout': service_config.get('timeout', 30),
                'allow_redirects': False,
            }
            
            # Add body for non-GET requests
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type == 'application/json':
                    try:
                        request_data['json'] = json.loads(request.body)
                    except json.JSONDecodeError:
                        request_data['data'] = request.body
                else:
                    request_data['data'] = request.body
            
            # Add query parameters
            if request.GET:
                request_data['params'] = dict(request.GET)
            
            # Make the request
            logger.info(f"Proxying {request.method} {request.path} to {target_url}")
            response = self.session.request(**request_data)
            
            # Create Django response
            django_response = HttpResponse(
                content=response.content,
                status=response.status_code,
                content_type=response.headers.get('content-type', 'application/json')
            )
            
            # Copy response headers (excluding some headers)
            excluded_headers = {
                'content-encoding', 'content-length', 'transfer-encoding',
                'connection', 'keep-alive', 'proxy-authenticate',
                'proxy-authorization', 'te', 'trailers', 'upgrade'
            }
            
            for key, value in response.headers.items():
                if key.lower() not in excluded_headers:
                    django_response[key] = value
            
            # Store service information for logging
            request.service_name = service_name
            request.downstream_url = target_url
            
            return django_response
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while proxying to {service_name}")
            return JsonResponse({
                'error': 'Request timeout',
                'message': f'Request to {service_name} timed out'
            }, status=504)
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while proxying to {service_name}")
            return JsonResponse({
                'error': 'Service unavailable',
                'message': f'Unable to connect to {service_name}'
            }, status=503)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while proxying to {service_name}: {e}")
            return JsonResponse({
                'error': 'Proxy error',
                'message': f'Error while proxying request to {service_name}'
            }, status=502)
            
        except Exception as e:
            logger.error(f"Unexpected error while proxying to {service_name}: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }, status=500)
    
    def health_check(self, service_name):
        """Perform a health check on a downstream service."""
        try:
            service_config = get_service_config(service_name)
            if not service_config:
                return False, "Service not configured"
            
            health_url = f"{service_config['base_url']}/health"
            response = self.session.get(health_url, timeout=5)
            
            return response.status_code == 200, f"Status: {response.status_code}"
            
        except Exception as e:
            return False, str(e)


# Global proxy service instance
proxy_service = ProxyService()
