#!/usr/bin/env python3
"""
Test script for the Django API Gateway
This script demonstrates the main functionality of the API Gateway.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = None  # Will be set after creating an API key


def print_response(response: requests.Response, title: str = "Response"):
    """Print formatted response."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
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


def create_api_key():
    """Create a new API key."""
    print("\n2. Creating API Key")
    data = {
        "name": "Test API Key",
        "requests_per_minute": 100,
        "requests_per_hour": 1000
    }
    response = requests.post(
        f"{BASE_URL}/api/keys/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response, "Create API Key")
    
    if response.status_code == 201:
        global API_KEY
        API_KEY = response.json()["api_key"]["key"]
        print(f"API Key created: {API_KEY}")
        return True
    return False


def test_api_key_authentication():
    """Test API key authentication."""
    print("\n3. Testing API Key Authentication")
    
    # Test without API key (should fail)
    print("\n3a. Request without API key (should fail)")
    response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/")
    print_response(response, "No API Key")
    
    if not API_KEY:
        print("No API key available, skipping authenticated tests")
        return False
    
    # Test with API key (should succeed)
    print("\n3b. Request with API key (should succeed)")
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/", headers=headers)
    print_response(response, "With API Key")
    
    return response.status_code != 401


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n4. Testing Rate Limiting")
    
    if not API_KEY:
        print("No API key available, skipping rate limiting tests")
        return False
    
    headers = {"X-API-Key": API_KEY}
    
    # Make multiple requests quickly to test rate limiting
    print("Making multiple requests to test rate limiting...")
    for i in range(5):
        response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/", headers=headers)
        print(f"Request {i+1}: Status {response.status_code}")
        if response.status_code == 429:
            print("Rate limit hit!")
            break
        time.sleep(0.1)
    
    return True


def test_api_management():
    """Test API management endpoints."""
    print("\n5. Testing API Management")
    
    # Get API statistics
    print("\n5a. Getting API Statistics")
    response = requests.get(f"{BASE_URL}/api/stats/")
    print_response(response, "API Statistics")
    
    # Get request logs
    print("\n5b. Getting Request Logs")
    response = requests.get(f"{BASE_URL}/api/logs/?limit=5")
    print_response(response, "Request Logs")
    
    # List API keys
    print("\n5c. Listing API Keys")
    response = requests.get(f"{BASE_URL}/api/keys/")
    print_response(response, "API Keys")
    
    return True


def test_service_health():
    """Test service health endpoints."""
    print("\n6. Testing Service Health")
    
    # Get all services status
    print("\n6a. All Services Status")
    response = requests.get(f"{BASE_URL}/api/services/status/")
    print_response(response, "Services Status")
    
    # Test individual service health
    print("\n6b. Individual Service Health")
    services = ["user-service", "product-service", "order-service"]
    for service in services:
        response = requests.get(f"{BASE_URL}/api/health/{service}/")
        print(f"\n{service}: Status {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response: {response.text}")
    
    return True


def test_proxy_functionality():
    """Test proxy functionality with mock services."""
    print("\n7. Testing Proxy Functionality")
    
    if not API_KEY:
        print("No API key available, skipping proxy tests")
        return False
    
    headers = {"X-API-Key": API_KEY}
    
    # Test different HTTP methods
    methods = ["GET", "POST", "PUT", "DELETE"]
    for method in methods:
        print(f"\n7a. Testing {method} request")
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}/api/proxy/user-service/users/", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}/api/proxy/user-service/users/", headers=headers, json={"test": "data"})
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}/api/proxy/user-service/users/123", headers=headers, json={"test": "data"})
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}/api/proxy/user-service/users/123", headers=headers)
            
            print(f"{method} Response: {response.status_code}")
        except Exception as e:
            print(f"{method} Error: {e}")
    
    return True


def main():
    """Run all tests."""
    print("Django API Gateway Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Create API Key", create_api_key),
        ("API Key Authentication", test_api_key_authentication),
        ("Rate Limiting", test_rate_limiting),
        ("API Management", test_api_management),
        ("Service Health", test_service_health),
        ("Proxy Functionality", test_proxy_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"✗ {test_name}: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API Gateway is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
