#!/usr/bin/env python3
"""
Simple test server to validate webhook functionality.
Prints received webhook data with "python server echo" prefix.
"""

import json
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class WebhookTestHandler(BaseHTTPRequestHandler):
    """Handler for webhook test requests."""
    
    def do_POST(self):
        """Handle POST requests (webhooks)."""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read the request body
            post_data = self.rfile.read(content_length)
            
            # Parse JSON if possible
            try:
                data = json.loads(post_data.decode('utf-8'))
                text = data.get('text', 'No text field')
                confidence = data.get('confidence', 'Unknown')
                chunk_index = data.get('chunk_index', 'Unknown')
                timestamp = data.get('timestamp', 'Unknown')
                
                # Print with the requested prefix
                print(f"python server echo: [{confidence}] {text}")
                print(f"  └── chunk: {chunk_index}, timestamp: {timestamp}")
                
            except json.JSONDecodeError:
                # If not JSON, just print the raw data
                text = post_data.decode('utf-8', errors='ignore')
                print(f"python server echo: {text}")
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'success',
                'message': 'Webhook received',
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"python server echo: ERROR - {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests (health check)."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'message': 'Webhook test server is running',
            'endpoint': f'http://localhost:{self.server.server_port}',
            'timestamp': datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
        print(f"python server echo: Health check requested")
    
    def log_message(self, format, *args):
        """Override to customize logging."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")


def run_server(port=8080):
    """Run the webhook test server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookTestHandler)
    
    print(f"🚀 Webhook test server starting on port {port}")
    print(f"📡 Webhook URL: http://localhost:{port}")
    print(f"🔍 Health check: http://localhost:{port}")
    print(f"💡 Use Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n⏹️  Server stopped by user")
        httpd.shutdown()


if __name__ == '__main__':
    port = 8080
    
    # Check if port is specified as argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            run_server(port)
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    run_server(port)
