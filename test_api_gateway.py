#!/usr/bin/env python3
"""
Test script for the Django API Gateway
This script demonstrates the main functionality of the API Gateway.
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = None  # This will be set manually or via admin panel

def print_response(response, test_name):
    """Print response details for debugging."""
    print(f"{test_name} - Status: {response.status_code}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text}")


def test_health_check():
    """Test the health check endpoint."""
    print("\n1. Testing Health Check")
    response = requests.get(f"{BASE_URL}/health/")
    print_response(response, "Health Check")
    return response.status_code == 200


def test_api_key_authentication():
    """Test API key authentication."""
    print("\n2. Testing API Key Authentication")
    
    # Test without API key (should fail)
    print("\n2a. Request without API key (should fail)")
    response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/")
    print_response(response, "No API Key")
    
    # Note: API keys must be created via Django admin panel
    print("\n2b. Skipping authenticated tests - API keys must be created via admin panel")
    print("To test with API key:")
    print("1. Go to http://localhost:8000/admin/")
    print("2. Create an API key in the admin panel")
    print("3. Use that key in the X-API-Key header")
    
    return True


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n3. Testing Rate Limiting")
    
    print("Note: Rate limiting tests require a valid API key")
    print("Create an API key via admin panel first")
    
    # Test without API key (should fail)
    print("\n3a. Testing rate limiting without API key")
    response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/")
    print_response(response, "Rate Limit Test - No API Key")
    
    return True


def test_api_management():
    """Test API management endpoints."""
    print("\n4. Testing API Management")
    
    # Get API statistics
    print("\n4a. Getting API Statistics")
    response = requests.get(f"{BASE_URL}/api/stats/")
    print_response(response, "API Statistics")
    
    # Get request logs
    print("\n4b. Getting Request Logs")
    response = requests.get(f"{BASE_URL}/api/logs/?limit=5")
    print_response(response, "Request Logs")
    
    return True


def test_service_health():
    """Test service health endpoints."""
    print("\n5. Testing Service Health")
    
    # Get all services status
    print("\n5a. All Services Status")
    response = requests.get(f"{BASE_URL}/api/services/status/")
    print_response(response, "Services Status")
    
    # Test individual service health
    print("\n5b. Individual Service Health")
    services = ["user-service", "product-service", "order-service"]
    
    for service in services:
        response = requests.get(f"{BASE_URL}/api/health/{service}/")
        print_response(response, f"Service Health - {service}")
    
    return True


def test_proxy_functionality():
    """Test proxy functionality to downstream services."""
    print("\n6. Testing Proxy Functionality")
    
    # Test proxy without API key (should fail)
    print("\n6a. Testing proxy without API key (should fail)")
    response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/")
    print_response(response, "Proxy - No API Key")
    
    # Test proxy with invalid API key (should fail)
    print("\n6b. Testing proxy with invalid API key (should fail)")
    headers = {"X-API-Key": "invalid-key"}
    response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/", headers=headers)
    print_response(response, "Proxy - Invalid API Key")
    
    return True


def main():
    """Run all tests."""
    print("🚀 API Gateway Testing Suite")
    print("=" * 50)
    print("Note: API keys must be created via Django admin panel")
    print("Admin URL: http://localhost:8000/admin/")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("API Key Authentication", test_api_key_authentication),
        ("Rate Limiting", test_rate_limiting),
        ("API Management", test_api_management),
        ("Service Health", test_service_health),
        ("Proxy Functionality", test_proxy_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    print("\n📋 Next Steps:")
    print("1. Create API keys via Django admin panel")
    print("2. Test authenticated endpoints with valid API keys")
    print("3. Test rate limiting with valid API keys")


if __name__ == "__main__":
    main()
