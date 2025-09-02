# API Gateway Rate Limit Testing Script

This script tests the rate limiting functionality of your API gateway by making multiple requests to the product-service health check endpoint.

## Prerequisites

1. **API Gateway Running**: Make sure your Django API gateway is running (typically on `http://localhost:8000`)
2. **Product Service**: Ensure the product-service is accessible through the gateway
3. **API Key**: You need a valid API key from the admin panel

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r test_requirements.txt
   ```

## Usage

1. **Run the script**:
   ```bash
   python test_rate_limit.py
   ```

2. **Follow the prompts**:
   - Enter the API Gateway URL (default: `http://localhost:8000`)
   - Enter your API key
   - Choose test type:
     - **Option 1**: Standard rate limit test with configurable delays
     - **Option 2**: Burst test (rapid requests to test immediate rate limiting)
     - **Option 3**: Both tests

## Test Types

### Standard Rate Limit Test
- Makes requests with configurable delays between them
- Good for testing gradual rate limiting
- Default: 50 requests with 0.1s delay

### Burst Test
- Sends multiple requests in quick succession
- Tests immediate rate limiting behavior
- Default: 10 requests

## What the Script Tests

1. **Authentication**: Uses your API key in the `X-API-Key` header
2. **Rate Limiting**: Monitors for HTTP 429 (Too Many Requests) responses
3. **Performance**: Measures response times for successful requests
4. **Error Handling**: Tracks various error responses

## Expected Behavior

- **Successful requests** (200): ✅ Green checkmark
- **Rate limited requests** (429): 🚫 Red X (this is expected behavior!)
- **Error requests** (other status codes): ❌ Red X
- **Exceptions**: 💥 Explosion emoji

## Rate Limiting Detection

The script will detect when rate limiting kicks in:
- If you see `🚫 RATE LIMITED (429)` responses, your API gateway is working correctly
- The default rate limits are typically:
  - 60 requests per minute
  - 1000 requests per hour

## Example Output

```
🔐 API Gateway Rate Limit Tester
========================================
Enter API Gateway URL (default: http://localhost:8000): 
Enter your API key: abc123def456

📋 Test Options:
1. Standard rate limit test (with delays)
2. Burst test (rapid requests)
3. Both tests

Select test type (1/2/3, default: 1): 1
Enter total requests (default: 50): 100
Enter delay between requests in seconds (default: 0.1): 0.05

🚀 Starting Rate Limit Test
📊 Target: 100 requests
⏱️  Delay: 0.05s between requests
🔑 API Key: abc123de...
🌐 Gateway: http://localhost:8000
🎯 Endpoint: /api/proxy/product-service/health
============================================================
✅ Request 1: SUCCESS (200) - 45.23ms
✅ Request 2: SUCCESS (200) - 42.18ms
...
🚫 Request 65: RATE LIMITED (429) - 38.92ms
🚫 Request 66: RATE LIMITED (429) - 41.15ms
...
```

## Troubleshooting

1. **Connection refused**: Make sure your API gateway is running
2. **401 Unauthorized**: Check that your API key is valid
3. **404 Not Found**: Verify the product-service is configured and accessible
4. **No rate limiting**: Check your rate limit middleware configuration

## Customization

You can modify the script to:
- Test different endpoints
- Change request headers
- Add more sophisticated rate limiting tests
- Export results to CSV/JSON
- Test different HTTP methods
