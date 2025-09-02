import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .proxy import proxy_service
from .models import APIKey, RequestLog, ServiceConfig
from .utils import generate_api_key

logger = logging.getLogger('gateway')


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def proxy_view(request, service_name, path=''):
    """Generic proxy view that forwards requests to downstream services."""
    return proxy_service.proxy_request(request, service_name, path)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for the API Gateway."""
    return Response({
        'status': 'healthy',
        'service': 'api-gateway',
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def service_health(request, service_name):
    """Health check for a specific downstream service."""
    is_healthy, message = proxy_service.health_check(service_name)
    
    return Response({
        'service': service_name,
        'healthy': is_healthy,
        'message': message
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def services_status(request):
    """Get status of all configured services."""
    services = []
    
    # Get services from database
    db_services = ServiceConfig.objects.filter(is_active=True)
    for service in db_services:
        is_healthy, message = proxy_service.health_check(service.name)
        services.append({
            'name': service.name,
            'base_url': service.base_url,
            'healthy': is_healthy,
            'message': message,
            'last_health_check': service.last_health_check
        })
    
    return Response({
        'services': services,
        'total': len(services)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_stats(request):
    """Get API usage statistics."""
    try:
        # Get basic stats
        total_requests = RequestLog.objects.count()
        error_requests = RequestLog.objects.filter(is_error=True).count()
        
        # Get recent requests (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        yesterday = timezone.now() - timedelta(days=1)
        recent_requests = RequestLog.objects.filter(timestamp__gte=yesterday).count()
        
        # Get top services
        from django.db.models import Count
        top_services = RequestLog.objects.values('service_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Get average response time
        from django.db.models import Avg
        avg_response_time = RequestLog.objects.aggregate(
            avg_time=Avg('response_time')
        )['avg_time'] or 0
        
        return Response({
            'total_requests': total_requests,
            'error_requests': error_requests,
            'success_rate': ((total_requests - error_requests) / total_requests * 100) if total_requests > 0 else 0,
            'recent_requests_24h': recent_requests,
            'average_response_time_ms': round(avg_response_time, 2),
            'top_services': list(top_services)
        })
        
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return Response({
            'error': 'Failed to get statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def request_logs(request):
    """Get recent request logs."""
    try:
        # Get query parameters
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        service_name = request.GET.get('service')
        status_code = request.GET.get('status_code')
        
        # Build query
        queryset = RequestLog.objects.select_related('api_key').order_by('-timestamp')
        
        if service_name:
            queryset = queryset.filter(service_name=service_name)
        
        if status_code:
            queryset = queryset.filter(status_code=status_code)
        
        # Paginate
        logs = queryset[offset:offset + limit]
        
        # Serialize logs
        log_data = []
        for log in logs:
            log_data.append({
                'id': str(log.id),
                'method': log.method,
                'path': log.path,
                'status_code': log.status_code,
                'response_time_ms': log.response_time,
                'service_name': log.service_name,
                'api_key_name': log.api_key.name if log.api_key else None,
                'client_ip': log.client_ip,
                'timestamp': log.timestamp.isoformat(),
                'is_error': log.is_error
            })
        
        return Response({
            'logs': log_data,
            'total': queryset.count(),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting request logs: {e}")
        return Response({
            'error': 'Failed to get request logs'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class APIKeyManagementView(View):
    """View for managing API keys."""
    
    def get(self, request):
        """List all API keys."""
        try:
            api_keys = APIKey.objects.all()
            keys_data = []
            
            for key in api_keys:
                keys_data.append({
                    'id': str(key.id),
                    'name': key.name,
                    'key_preview': f"{key.key[:8]}...",
                    'is_active': key.is_active,
                    'requests_per_minute': key.requests_per_minute,
                    'requests_per_hour': key.requests_per_hour,
                    'created_at': key.created_at.isoformat(),
                    'last_used': key.last_used.isoformat() if key.last_used else None
                })
            
            return JsonResponse({
                'api_keys': keys_data,
                'total': len(keys_data)
            })
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return JsonResponse({
                'error': 'Failed to list API keys'
            }, status=500)
    
    def post(self, request):
        """Create a new API key."""
        try:
            data = json.loads(request.body)
            name = data.get('name')
            
            if not name:
                return JsonResponse({
                    'error': 'Name is required'
                }, status=400)
            
            # Generate API key
            api_key_value = generate_api_key()
            
            # Create API key object
            api_key = APIKey.objects.create(
                name=name,
                key=api_key_value,
                requests_per_minute=data.get('requests_per_minute', 60),
                requests_per_hour=data.get('requests_per_hour', 1000)
            )
            
            return JsonResponse({
                'message': 'API key created successfully',
                'api_key': {
                    'id': str(api_key.id),
                    'name': api_key.name,
                    'key': api_key.key,  # Only show full key on creation
                    'requests_per_minute': api_key.requests_per_minute,
                    'requests_per_hour': api_key.requests_per_hour,
                    'created_at': api_key.created_at.isoformat()
                }
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return JsonResponse({
                'error': 'Failed to create API key'
            }, status=500)
    
    def delete(self, request, key_id):
        """Delete an API key."""
        try:
            api_key = APIKey.objects.get(id=key_id)
            api_key.delete()
            
            return JsonResponse({
                'message': 'API key deleted successfully'
            })
            
        except APIKey.DoesNotExist:
            return JsonResponse({
                'error': 'API key not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return JsonResponse({
                'error': 'Failed to delete API key'
            }, status=500)
