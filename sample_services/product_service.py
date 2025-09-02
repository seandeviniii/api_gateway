#!/usr/bin/env python3
"""
Simple Product Service HTTP Server
Run this locally without Docker: python product_service.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import os

class ProductServiceHandler(BaseHTTPRequestHandler):
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self._set_headers(200)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/health':
            # Health check endpoint
            response = {
                "status": "healthy",
                "service": "product-service",
                "version": "1.0.0"
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_url.path.startswith('/products'):
            # Products endpoint
            response = [
                {"id": 1, "name": "Product 1", "price": 29.99, "category": "Electronics"},
                {"id": 2, "name": "Product 2", "price": 19.99, "category": "Books"}
            ]
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
            
        else:
            # Default response
            self._set_headers(404)
            response = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith('/products'):
            # Create new product
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                product_data = json.loads(post_data.decode('utf-8'))
                response = {
                    "id": 3,
                    "name": product_data.get('name', 'New Product'),
                    "price": product_data.get('price', 39.99),
                    "category": product_data.get('category', 'Electronics'),
                    "message": "Product created successfully"
                }
                self._set_headers(201)
                self.wfile.write(json.dumps(response).encode())
            except json.JSONDecodeError:
                self._set_headers(400)
                response = {"error": "Invalid JSON"}
                self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            response = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_PUT(self):
        """Handle PUT requests"""
        if self.path.startswith('/products'):
            # Update product
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)
            
            try:
                product_data = json.loads(put_data.decode('utf-8'))
                response = {
                    "id": 1,
                    "name": product_data.get('name', 'Updated Product'),
                    "price": product_data.get('price', 34.99),
                    "category": product_data.get('category', 'Electronics'),
                    "message": "Product updated successfully"
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(response).encode())
            except json.JSONDecodeError:
                self._set_headers(400)
                response = {"error": "Invalid JSON"}
                self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            response = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path.startswith('/products'):
            # Delete product
            self._set_headers(204)
        else:
            self._set_headers(404)
            response = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Custom logging to show requests"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=8080):
    """Run the product service server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ProductServiceHandler)
    
    print(f"🚀 Product Service running on http://localhost:{port}")
    print(f"📡 Available endpoints:")
    print(f"   GET  http://localhost:{port}/health")
    print(f"   GET  http://localhost:{port}/products/")
    print(f"   POST http://localhost:{port}/products/")
    print(f"   PUT  http://localhost:{port}/products/1")
    print(f"   DELETE http://localhost:{port}/products/1")
    print(f"\n💡 Test with: curl http://localhost:{port}/health")
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping Product Service...")
        httpd.server_close()
        print(f"✅ Product Service stopped")

if __name__ == '__main__':
    # You can change the port here if needed
    PORT = 8080
    run_server(PORT)
