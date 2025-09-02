from django.db import models
from django.utils import timezone
import uuid


class APIKey(models.Model):
    """Model for storing API keys and their associated metadata."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Human-readable name for the API key")
    key = models.CharField(max_length=64, unique=True, help_text="The actual API key")
    is_active = models.BooleanField(default=True, help_text="Whether this API key is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True, help_text="Last time this key was used")
    
    # Rate limiting settings
    requests_per_minute = models.IntegerField(default=60, help_text="Maximum requests per minute")
    requests_per_hour = models.IntegerField(default=1000, help_text="Maximum requests per hour")
    
    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.key[:8]}...)"
    
    def update_last_used(self):
        """Update the last_used timestamp."""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class RequestLog(models.Model):
    """Model for logging API requests for monitoring and debugging."""
    
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='request_logs')
    
    # Request details
    method = models.CharField(max_length=10, choices=HTTP_METHODS)
    path = models.CharField(max_length=500)
    query_params = models.TextField(blank=True, null=True)
    headers = models.JSONField(default=dict, blank=True)
    body = models.TextField(blank=True, null=True)
    
    # Response details
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    
    # Metadata
    client_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Service routing
    service_name = models.CharField(max_length=100, blank=True, null=True)
    downstream_url = models.URLField(blank=True, null=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    is_error = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['status_code']),
            models.Index(fields=['service_name']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} ({self.timestamp})"


class ServiceConfig(models.Model):
    """Model for configuring downstream services."""
    
    name = models.CharField(max_length=100, unique=True, help_text="Service name (e.g., user-service)")
    base_url = models.URLField(help_text="Base URL for the service")
    timeout = models.IntegerField(default=30, help_text="Request timeout in seconds")
    is_active = models.BooleanField(default=True, help_text="Whether this service is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Health check settings
    health_check_path = models.CharField(max_length=200, default="/health", help_text="Health check endpoint")
    health_check_interval = models.IntegerField(default=60, help_text="Health check interval in seconds")
    last_health_check = models.DateTimeField(null=True, blank=True)
    is_healthy = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Service Configuration"
        verbose_name_plural = "Service Configurations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.base_url})"
