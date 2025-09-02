# Django API Gateway

A simplified API Gateway built with Django that serves as a proxy layer between clients and backend services. This solution provides authentication, rate limiting, request proxying, and comprehensive logging.

## Features

- **API Key Authentication**: Secure authentication using API keys
- **Rate Limiting**: Per-API key rate limiting with configurable limits
- **Request Proxying**: Efficient forwarding to downstream services
- **Request Logging**: Comprehensive logging for monitoring and debugging
- **Health Checks**: Service health monitoring
- **Admin Interface**: Django admin for managing API keys and viewing logs
- **Statistics**: API usage statistics and analytics

## Architecture

```
Client Request → API Gateway → Downstream Services
                ↓
            Authentication
                ↓
            Rate Limiting
                ↓
            Request Logging
                ↓
            Proxy to Service
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd api_gateway
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Set up sample data**
   ```bash
   python manage.py setup_gateway --all
   ```

8. **Run the server**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `REDIS_URL`: Redis connection URL for rate limiting
- `RATE_LIMIT_PER_MINUTE`: Default requests per minute
- `RATE_LIMIT_PER_HOUR`: Default requests per hour
- `USER_SERVICE_URL`: User service base URL
- `PRODUCT_SERVICE_URL`: Product service base URL
- `ORDER_SERVICE_URL`: Order service base URL

### Redis Setup

For rate limiting, you need Redis running:

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:alpine
```

## Usage

### API Key Authentication

All requests must include an API key in the header:

```bash
# Using X-API-Key header
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/proxy/user-service/users/

# Using Authorization header
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/proxy/user-service/users/
```

### Proxying Requests

The gateway proxies requests to downstream services using the pattern:
```
/api/proxy/{service-name}/{path}
```

Examples:
```bash
# Proxy to user service
GET /api/proxy/user-service/users/
POST /api/proxy/user-service/users/

# Proxy to product service
GET /api/proxy/product-service/products/
PUT /api/proxy/product-service/products/123

# Proxy to order service
GET /api/proxy/order-service/orders/
POST /api/proxy/order-service/orders/
```

### Health Checks

```bash
# Gateway health
GET /health/

# Service health
GET /api/health/user-service/
GET /api/services/status/
```

### API Management

```bash
# Get API statistics
GET /api/stats/

# Get request logs
GET /api/logs/
GET /api/logs/?service=user-service&limit=10

# Note: API keys are managed via Django admin panel only
# Admin URL: http://localhost:8000/admin/
```

## API Endpoints

### Proxy Endpoints
- `GET/POST/PUT/PATCH/DELETE /api/proxy/{service-name}/{path}` - Proxy requests to downstream services

### Health Check Endpoints
- `GET /health/` - Gateway health check
- `GET /api/health/{service-name}/` - Service health check
- `GET /api/services/status/` - All services status

### Management Endpoints
- `GET /api/stats/` - API usage statistics
- `GET /api/logs/` - Request logs

**Note:** API keys are managed exclusively through the Django admin panel at `/admin/`

## Rate Limiting

Rate limiting is applied per API key and IP address:

- **Per-minute limit**: Configurable per API key (default: 60 requests)
- **Per-hour limit**: Configurable per API key (default: 1000 requests)

When rate limit is exceeded, the API returns:
```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 60 requests per minute",
  "retry_after": 60
}
```

## Logging

All requests are logged with the following information:
- Request method, path, and headers
- Response status code and time
- API key used
- Client IP and user agent
- Service name and downstream URL
- Error messages (if any)

Logs are stored in the database and can be viewed in the Django admin interface.

## Admin Interface

Access the Django admin at `/admin/` to:
- **Manage API Keys**: Create, edit, and delete API keys
- **View Request Logs**: Monitor all API requests and responses
- **Configure Services**: Set up downstream service configurations
- **Monitor System Health**: Check service status and performance

### API Key Management

API keys can only be created and managed through the Django admin panel:

1. **Access Admin**: Go to `http://localhost:8000/admin/`
2. **Login**: Use your superuser credentials
3. **API Keys Section**: Navigate to "API Keys" under the Gateway app
4. **Create Key**: Click "Add API Key" and fill in:
   - **Name**: Descriptive name for the key
   - **Requests per minute**: Rate limit for this key (default: 60)
   - **Requests per hour**: Hourly rate limit (default: 1000)
5. **Save**: The system will generate a unique API key automatically
6. **Copy Key**: Copy the generated key for use in your applications

**Security Note**: API keys are only shown once upon creation. Store them securely!

## Development

### Running Tests
```bash
python manage.py test
```

### Creating API Keys

API keys can only be created through the Django admin panel:

```bash
# Access admin panel
http://localhost:8000/admin/

# Or use management command for sample keys
python manage.py setup_gateway --create-sample-keys
```

### Adding New Services

1. **Via Django Admin**: Go to `/admin/` and add a new ServiceConfig
2. **Via Management Command**: Add to the sample services in `setup_gateway.py`
3. **Via Environment Variables**: Add `{SERVICE_NAME}_SERVICE_URL` to `.env`

## Deployment

### Production Settings

1. Set `DEBUG=False` in environment variables
2. Configure a production database (PostgreSQL recommended)
3. Set up Redis for rate limiting
4. Configure proper CORS settings
5. Use a production WSGI server (Gunicorn)

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "api_gateway.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Monitoring

The API Gateway provides several monitoring endpoints:

- **Health checks**: Monitor service availability
- **Statistics**: Track API usage and performance
- **Request logs**: Debug issues and analyze traffic
- **Rate limiting**: Monitor rate limit usage

## Security Considerations

- API keys are stored securely in the database
- Rate limiting prevents abuse
- Sensitive headers are stripped before proxying
- All requests are logged for audit purposes
- CORS is properly configured

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
