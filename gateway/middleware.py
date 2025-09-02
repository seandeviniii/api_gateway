import time
import json
import logging
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from .models import APIKey, RequestLog
from .utils import get_client_ip

logger = logging.getLogger('gateway')


class APIAuthenticationMiddleware(MiddlewareMixin):
    """Middleware for authenticating API requests using API keys."""
    
    def process_request(self, request):
        # Skip authentication for admin and health check endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/health/'):
            return None
        
        # Get API key from headers
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        
        if api_key and api_key.startswith('Bearer '):
            api_key = api_key[7:]  # Remove 'Bearer ' prefix
        
        if not api_key:
            return JsonResponse({
                'error': 'API key required',
                'message': 'Please provide a valid API key in the X-API-Key header or Authorization header'
            }, status=401)
        
        try:
            # Validate API key
            api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
            request.api_key = api_key_obj
            
            # Update last used timestamp
            api_key_obj.update_last_used()
            
        except APIKey.DoesNotExist:
            return JsonResponse({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or inactive'
            }, status=401)
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware for rate limiting requests per API key."""
    
    def process_request(self, request):
        # Skip rate limiting for admin and health check endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/health/'):
            return None
        
        if not hasattr(request, 'api_key'):
            return None
        
        api_key = request.api_key
        client_ip = get_client_ip(request)
        
        # Check per-minute rate limit
        minute_key = f"rate_limit:{api_key.key}:{client_ip}:minute:{int(time.time() // 60)}"
        minute_count = cache.get(minute_key, 0)
        
        if minute_count >= api_key.requests_per_minute:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Rate limit exceeded: {api_key.requests_per_minute} requests per minute',
                'retry_after': 60
            }, status=429)
        
        # Check per-hour rate limit
        hour_key = f"rate_limit:{api_key.key}:{client_ip}:hour:{int(time.time() // 3600)}"
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= api_key.requests_per_hour:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Rate limit exceeded: {api_key.requests_per_hour} requests per hour',
                'retry_after': 3600
            }, status=429)
        
        # Increment counters
        cache.set(minute_key, minute_count + 1, 60)
        cache.set(hour_key, hour_count + 1, 3600)
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware for logging API requests and responses."""
    
    def process_request(self, request):
        # Skip logging for admin and health check endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/health/'):
            return None
        
        # Store request start time
        request.start_time = time.time()
        
        # Store request data for logging
        request.log_data = {
            'method': request.method,
            'path': request.path,
            'query_params': request.GET.urlencode(),
            'headers': dict(request.headers),
            'body': self._get_request_body(request),
            'client_ip': get_client_ip(request),
            'user_agent': request.headers.get('User-Agent', ''),
        }
        
        return None
    
    def process_response(self, request, response):
        # Skip logging for admin and health check endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/health/'):
            return response
        
        if hasattr(request, 'start_time') and hasattr(request, 'log_data'):
            # Calculate response time
            response_time = (time.time() - request.start_time) * 1000  # Convert to milliseconds
            
            # Log the request
            self._log_request(request, response, response_time)
        
        return response
    
    def process_exception(self, request, exception):
        # Log exceptions
        if hasattr(request, 'start_time') and hasattr(request, 'log_data'):
            response_time = (time.time() - request.start_time) * 1000
            
            # Create error response
            error_response = JsonResponse({
                'error': 'Internal server error',
                'message': str(exception)
            }, status=500)
            
            self._log_request(request, error_response, response_time, exception=str(exception))
        
        return None
    
    def _get_request_body(self, request):
        """Extract request body safely."""
        try:
            if request.content_type == 'application/json':
                return json.dumps(request.data) if hasattr(request, 'data') else request.body.decode('utf-8')
            elif request.content_type == 'application/x-www-form-urlencoded':
                return request.POST.urlencode()
            else:
                return request.body.decode('utf-8')[:1000]  # Limit body size for logging
        except Exception:
            return None
    
    def _log_request(self, request, response, response_time, exception=None):
        """Log the request to database."""
        try:
            if hasattr(request, 'api_key'):
                log_entry = RequestLog.objects.create(
                    api_key=request.api_key,
                    method=request.log_data['method'],
                    path=request.log_data['path'],
                    query_params=request.log_data['query_params'],
                    headers=request.log_data['headers'],
                    body=request.log_data['body'],
                    status_code=response.status_code,
                    response_time=response_time,
                    client_ip=request.log_data['client_ip'],
                    user_agent=request.log_data['user_agent'],
                    error_message=exception,
                    is_error=exception is not None or response.status_code >= 400
                )
                
                # Log to console for debugging
                logger.info(
                    f"Request: {request.method} {request.path} - {response.status_code} "
                    f"({response_time:.2f}ms) - API Key: {request.api_key.name}"
                )
                
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
