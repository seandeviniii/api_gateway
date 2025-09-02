import json
import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .proxy import proxy_service
from .models import APIKey, RequestLog, ServiceConfig
from .utils import generate_api_key

logger = logging.getLogger('gateway')


class ProxyView(APIView):
    """Generic proxy view that forwards requests to downstream services."""
    permission_classes = [AllowAny]
    
    def dispatch(self, request, *args, **kwargs):
        """Handle all HTTP methods for proxying."""
        return proxy_service.proxy_request(request, kwargs.get('service_name'), kwargs.get('path', ''))


class HealthCheckView(APIView):
    """Health check endpoint for the API Gateway."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'api-gateway',
            'version': '1.0.0'
        })


class ServiceHealthView(APIView):
    """Health check for a specific downstream service."""
    permission_classes = [AllowAny]
    
    def get(self, request, service_name):
        is_healthy, message = proxy_service.health_check(service_name)
        
        return Response({
            'service': service_name,
            'healthy': is_healthy,
            'message': message
        })


class ServicesStatusView(APIView):
    """Get status of all configured services."""
    permission_classes = [AllowAny]
    
    def get(self, request):
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


class APIStatsView(APIView):
    """Get API usage statistics."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get basic stats
            total_requests = RequestLog.objects.count()
            error_requests = RequestLog.objects.filter(is_error=True).count()
            
            # Get recent requests (last 24 hours)
            yesterday = timezone.now() - timedelta(days=1)
            recent_requests = RequestLog.objects.filter(timestamp__gte=yesterday).count()
            
            # Get top services
            top_services = RequestLog.objects.values('service_name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # Get average response time
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


class RequestLogsView(APIView):
    """Get recent request logs."""
    permission_classes = [AllowAny]
    
    def get(self, request):
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


class APIKeyManagementView(APIView):
    """View for managing API keys."""
    permission_classes = [AllowAny]
    
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
            
            return Response({
                'api_keys': keys_data,
                'total': len(keys_data)
            })
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return Response({
                'error': 'Failed to list API keys'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new API key."""
        try:
            name = request.data.get('name')
            
            if not name:
                return Response({
                    'error': 'Name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate API key
            api_key_value = generate_api_key()
            
            # Create API key object
            api_key = APIKey.objects.create(
                name=name,
                key=api_key_value,
                requests_per_minute=request.data.get('requests_per_minute', 60),
                requests_per_hour=request.data.get('requests_per_hour', 1000)
            )
            
            return Response({
                'message': 'API key created successfully',
                'api_key': {
                    'id': str(api_key.id),
                    'name': api_key.name,
                    'key': api_key.key,  # Only show full key on creation
                    'requests_per_minute': api_key.requests_per_minute,
                    'requests_per_hour': api_key.requests_per_hour,
                    'created_at': api_key.created_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return Response({
                'error': 'Failed to create API key'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, key_id):
        """Delete an API key."""
        try:
            api_key = APIKey.objects.get(id=key_id)
            api_key.delete()
            
            return Response({
                'message': 'API key deleted successfully'
            })
            
        except APIKey.DoesNotExist:
            return Response({
                'error': 'API key not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return Response({
                'error': 'Failed to delete API key'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
