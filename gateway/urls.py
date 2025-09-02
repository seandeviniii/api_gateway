from django.urls import path, re_path
from . import views

urlpatterns = [
    # Proxy routes for downstream services
    re_path(r'^proxy/(?P<service_name>[^/]+)/(?P<path>.*)$', views.proxy_view, name='proxy'),
    re_path(r'^proxy/(?P<service_name>[^/]+)/$', views.proxy_view, name='proxy_root'),
    
    # Health check endpoints
    path('health/', views.health_check, name='health_check'),
    path('health/<str:service_name>/', views.service_health, name='service_health'),
    path('services/status/', views.services_status, name='services_status'),
    
    # API management endpoints
    path('stats/', views.api_stats, name='api_stats'),
    path('logs/', views.request_logs, name='request_logs'),
    
    # API key management
    path('keys/', views.APIKeyManagementView.as_view(), name='api_keys'),
    path('keys/<str:key_id>/', views.APIKeyManagementView.as_view(), name='api_key_detail'),
]
