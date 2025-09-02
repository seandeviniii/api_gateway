import secrets
import string
from django.conf import settings


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_api_key(length=32):
    """Generate a secure API key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_service_config(service_name):
    """Get configuration for a downstream service."""
    # First try to get from database
    try:
        from .models import ServiceConfig
        service_config = ServiceConfig.objects.get(name=service_name, is_active=True)
        return {
            'base_url': service_config.base_url,
            'timeout': service_config.timeout,
            'is_healthy': service_config.is_healthy,
        }
    except ServiceConfig.DoesNotExist:
        pass
    
    # Fallback to settings
    return settings.DOWNSTREAM_SERVICES.get(service_name, {})


def build_downstream_url(service_name, path):
    """Build the full URL for a downstream service."""
    service_config = get_service_config(service_name)
    base_url = service_config.get('base_url', '')
    
    if not base_url:
        raise ValueError(f"No configuration found for service: {service_name}")
    
    # Ensure base_url doesn't end with slash
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # Ensure path starts with slash
    if not path.startswith('/'):
        path = '/' + path
    
    return f"{base_url}{path}"


def sanitize_headers(headers):
    """Remove sensitive headers before forwarding to downstream services."""
    sensitive_headers = {
        'authorization',
        'x-api-key',
        'cookie',
        'host',
        'content-length',
        'transfer-encoding',
    }
    
    return {k: v for k, v in headers.items() if k.lower() not in sensitive_headers}


def format_response_time(response_time):
    """Format response time for display."""
    if response_time < 1000:
        return f"{response_time:.2f}ms"
    else:
        return f"{response_time/1000:.2f}s"
