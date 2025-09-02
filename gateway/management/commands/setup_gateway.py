from django.core.management.base import BaseCommand
from django.conf import settings
from gateway.models import APIKey, ServiceConfig
from gateway.utils import generate_api_key


class Command(BaseCommand):
    help = 'Set up the API Gateway with sample API keys and service configurations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-keys',
            action='store_true',
            help='Create sample API keys',
        )
        parser.add_argument(
            '--create-sample-services',
            action='store_true',
            help='Create sample service configurations',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create all sample data',
        )
    
    def handle(self, *args, **options):
        if options['all'] or options['create_sample_keys']:
            self.create_sample_api_keys()
        
        if options['all'] or options['create_sample_services']:
            self.create_sample_services()
        
        if not any([options['all'], options['create_sample_keys'], options['create_sample_services']]):
            self.stdout.write(
                self.style.WARNING(
                    'No options specified. Use --help to see available options.'
                )
            )
    
    def create_sample_api_keys(self):
        """Create sample API keys."""
        self.stdout.write('Creating sample API keys...')
        
        sample_keys = [
            {
                'name': 'Development API Key',
                'requests_per_minute': 100,
                'requests_per_hour': 1000,
            },
            {
                'name': 'Production API Key',
                'requests_per_minute': 60,
                'requests_per_hour': 500,
            },
            {
                'name': 'Testing API Key',
                'requests_per_minute': 200,
                'requests_per_hour': 2000,
            },
        ]
        
        created_count = 0
        for key_data in sample_keys:
            api_key, created = APIKey.objects.get_or_create(
                name=key_data['name'],
                defaults={
                    'key': generate_api_key(),
                    'requests_per_minute': key_data['requests_per_minute'],
                    'requests_per_hour': key_data['requests_per_hour'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created API key: {api_key.name} - {api_key.key}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'API key already exists: {api_key.name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} new API keys')
        )
    
    def create_sample_services(self):
        """Create sample service configurations."""
        self.stdout.write('Creating sample service configurations...')
        
        sample_services = [
            {
                'name': 'user-service',
                'base_url': 'http://localhost:8001',
                'timeout': 30,
                'health_check_path': '/health',
            },
            {
                'name': 'product-service',
                'base_url': 'http://localhost:8002',
                'timeout': 30,
                'health_check_path': '/health',
            },
            {
                'name': 'order-service',
                'base_url': 'http://localhost:8003',
                'timeout': 30,
                'health_check_path': '/health',
            },
        ]
        
        created_count = 0
        for service_data in sample_services:
            service, created = ServiceConfig.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'base_url': service_data['base_url'],
                    'timeout': service_data['timeout'],
                    'health_check_path': service_data['health_check_path'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created service: {service.name} - {service.base_url}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Service already exists: {service.name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} new service configurations')
        )
