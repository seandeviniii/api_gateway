from django.urls import path, re_path
from . import views

urlpatterns = [
    # Proxy routes for downstream services
    re_path(r'^proxy/(?P<service_name>[^/]+)/(?P<path>.*)$', views.ProxyView.as_view(), name='proxy'),
    re_path(r'^proxy/(?P<service_name>[^/]+)/$', views.ProxyView.as_view(), name='proxy_root'),
    
    # Health check endpoints
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('health/<str:service_name>/', views.ServiceHealthView.as_view(), name='service_health'),
    path('services/status/', views.ServicesStatusView.as_view(), name='services_status'),
    
    # API management endpoints
    path('stats/', views.APIStatsView.as_view(), name='api_stats'),
    path('logs/', views.RequestLogsView.as_view(), name='request_logs'),
    
    # API key management
    path('keys/', views.APIKeyManagementView.as_view(), name='api_keys'),
    path('keys/<str:key_id>/', views.APIKeyManagementView.as_view(), name='api_key_detail'),
]
