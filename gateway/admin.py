from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms
from .models import APIKey, RequestLog, ServiceConfig
from .utils import generate_api_key


class APIKeyAdminForm(forms.ModelForm):
    """Custom form for APIKey admin with helpful help text."""
    
    class Meta:
        model = APIKey
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Only for new instances
            self.fields['key'].help_text = "API key will be auto-generated. You can modify it if needed."


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    form = APIKeyAdminForm
    list_display = ['name', 'key_display', 'is_active', 'requests_per_minute', 'requests_per_hour', 'last_used', 'created_at']
    list_filter = ['is_active', 'created_at', 'last_used']
    search_fields = ['name', 'key']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_used']
    ordering = ['-created_at']
    
    def get_changeform_initial_data(self, request):
        """Auto-generate API key when adding a new API key."""
        initial = super().get_changeform_initial_data(request)
        if not initial.get('key'):
            initial['key'] = generate_api_key()
        return initial
    
    def key_display(self, obj):
        """Display only first 8 characters of the API key for security."""
        return f"{obj.key[:8]}..."
    key_display.short_description = "API Key"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'status_code', 'api_key_name', 'service_name', 'response_time', 'timestamp', 'is_error']
    list_filter = ['method', 'status_code', 'service_name', 'is_error', 'timestamp']
    search_fields = ['path', 'api_key__name', 'service_name', 'client_ip']
    readonly_fields = ['id', 'timestamp', 'response_time', 'headers_display', 'body_display']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def api_key_name(self, obj):
        """Display API key name with link to admin."""
        if obj.api_key:
            url = reverse('admin:gateway_apikey_change', args=[obj.api_key.id])
            return format_html('<a href="{}">{}</a>', url, obj.api_key.name)
        return '-'
    api_key_name.short_description = 'API Key'
    
    def headers_display(self, obj):
        """Display headers in a readable format."""
        if obj.headers:
            return format_html('<pre>{}</pre>', str(obj.headers))
        return '-'
    headers_display.short_description = 'Headers'
    
    def body_display(self, obj):
        """Display request body in a readable format."""
        if obj.body:
            return format_html('<pre>{}</pre>', obj.body[:500] + '...' if len(obj.body) > 500 else obj.body)
        return '-'
    body_display.short_description = 'Request Body'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('api_key')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ServiceConfig)
class ServiceConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_url', 'is_active', 'is_healthy', 'timeout', 'last_health_check']
    list_filter = ['is_active', 'is_healthy', 'created_at']
    search_fields = ['name', 'base_url']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_health_check']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'base_url', 'timeout', 'is_active')
        }),
        ('Health Check', {
            'fields': ('health_check_path', 'health_check_interval', 'is_healthy', 'last_health_check')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
