#!/usr/bin/env python3
"""
Rate Limit Testing Script for Product Service

This script tests the rate limiting functionality of the API gateway
by making multiple requests to the product-service health check endpoint.
"""

import requests
import time
import sys
from typing import Optional


class RateLimitTester:
    def __init__(self, api_gateway_url: str, api_key: str):
        """
        Initialize the rate limit tester.
        
        Args:
            api_gateway_url: Base URL of the API gateway (e.g., http://localhost:8000)
            api_key: API key to use for authentication
        """
        self.api_gateway_url = api_gateway_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        self.request_count = 0
        self.success_count = 0
        self.rate_limited_count = 0
        self.error_count = 0
    
    def make_request(self) -> dict:
        """
        Make a single request to the product-service health endpoint.
        
        Returns:
            dict: Response information including status, headers, and timing
        """
        url = f"{self.api_gateway_url}/api/proxy/product-service/health"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=10)
            end_time = time.time()
            
            self.request_count += 1
            
            result = {
                'request_number': self.request_count,
                'status_code': response.status_code,
                'response_time': round((end_time - start_time) * 1000, 2),  # ms
                'headers': dict(response.headers),
                'body': response.text,
                'timestamp': time.strftime('%H:%M:%S')
            }
            
            if response.status_code == 200:
                self.success_count += 1
                print(f"✅ Request {self.request_count}: SUCCESS ({response.status_code}) - {result['response_time']}ms")
            elif response.status_code == 429:  # Too Many Requests
                self.rate_limited_count += 1
                print(f"🚫 Request {self.request_count}: RATE LIMITED ({response.status_code}) - {result['response_time']}ms")
            else:
                self.error_count += 1
                print(f"❌ Request {self.request_count}: ERROR ({response.status_code}) - {result['response_time']}ms")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.request_count += 1
            self.error_count += 1
            print(f"💥 Request {self.request_count}: EXCEPTION - {str(e)}")
            return {
                'request_number': self.request_count,
                'status_code': None,
                'response_time': None,
                'error': str(e),
                'timestamp': time.strftime('%H:%M:%S')
            }
    
    def test_rate_limit(self, total_requests: int, delay: float = 0.1) -> None:
        """
        Test rate limiting by making multiple requests.
        
        Args:
            total_requests: Total number of requests to make
            delay: Delay between requests in seconds
        """
        print(f"\n🚀 Starting Rate Limit Test")
        print(f"📊 Target: {total_requests} requests")
        print(f"⏱️  Delay: {delay}s between requests")
        print(f"🔑 API Key: {self.api_key[:8]}...")
        print(f"🌐 Gateway: {self.api_gateway_url}")
        print(f"🎯 Endpoint: /api/proxy/product-service/health")
        print("=" * 60)
        
        results = []
        
        for i in range(total_requests):
            result = self.make_request()
            results.append(result)
            
            if i < total_requests - 1:  # Don't sleep after the last request
                time.sleep(delay)
        
        self.print_summary(results)
    
    def print_summary(self, results: list) -> None:
        """Print a summary of the test results."""
        print("\n" + "=" * 60)
        print("📈 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Requests: {self.request_count}")
        print(f"Successful: {self.success_count}")
        print(f"Rate Limited: {self.rate_limited_count}")
        print(f"Errors: {self.error_count}")
        
        if self.success_count > 0:
            success_times = [r['response_time'] for r in results if r.get('response_time')]
            if success_times:
                avg_time = sum(success_times) / len(success_times)
                print(f"Average Response Time: {avg_time:.2f}ms")
                print(f"Fastest Response: {min(success_times):.2f}ms")
                print(f"Slowest Response: {max(success_times):.2f}ms")
        
        if self.rate_limited_count > 0:
            print(f"\n🚫 Rate limiting detected! The API gateway is working correctly.")
            print(f"   {self.rate_limited_count} requests were blocked due to rate limits.")
        
        print("\n" + "=" * 60)
    
    def test_burst_requests(self, burst_size: int = 10) -> None:
        """
        Test burst requests to see immediate rate limiting.
        
        Args:
            burst_size: Number of requests to send in quick succession
        """
        print(f"\n💥 Testing Burst Requests ({burst_size} requests)")
        print("=" * 40)
        
        results = []
        start_time = time.time()
        
        for i in range(burst_size):
            result = self.make_request()
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n⏱️  Burst completed in {total_time:.2f}s")
        print(f"📊 Requests per second: {burst_size / total_time:.2f}")
        
        self.print_summary(results)


def main():
    """Main function to run the rate limit test."""
    print("🔐 API Gateway Rate Limit Tester")
    print("=" * 40)
    
    # Get configuration from user
    api_gateway_url = input("Enter API Gateway URL (default: http://localhost:8000): ").strip()
    if not api_gateway_url:
        api_gateway_url = "http://localhost:8000"
    
    api_key = input("Enter your API key: ").strip()
    if not api_key:
        print("❌ API key is required!")
        sys.exit(1)
    
    # Create tester instance
    tester = RateLimitTester(api_gateway_url, api_key)
    
    # Test options
    print(f"\n📋 Test Options:")
    print("1. Standard rate limit test (with delays)")
    print("2. Burst test (rapid requests)")
    print("3. Both tests")
    
    choice = input("\nSelect test type (1/2/3, default: 1): ").strip()
    
    if choice == "2":
        burst_size = int(input("Enter burst size (default: 10): ") or "10")
        tester.test_burst_requests(burst_size)
    elif choice == "3":
        total_requests = int(input("Enter total requests for standard test (default: 50): ") or "50")
        delay = float(input("Enter delay between requests in seconds (default: 0.1): ") or "0.1")
        burst_size = int(input("Enter burst size (default: 10): ") or "10")
        
        tester.test_rate_limit(total_requests, delay)
        tester.test_burst_requests(burst_size)
    else:  # Default to option 1
        total_requests = int(input("Enter total requests (default: 50): ") or "50")
        delay = float(input("Enter delay between requests in seconds (default: 0.1): ") or "0.1")
        tester.test_rate_limit(total_requests, delay)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
