#!/usr/bin/env python
import sys
import os
import json
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer

# GitHub Repository Configuration
GITHUB_TOKEN = 'make a toy token here'  # Replace with your GitHub personal access token
OWNER = 'johnynek'                  # Replace with your GitHub username
REPO = 'bosatsu'            # Replace with your GitHub repository name

# Read webhook URL from standard input

CODESPACE_NAME = os.environ["CODESPACE_NAME"]
webhook_url = f"https://{CODESPACE_NAME}-8080.app.github.dev"

# Function to register a webhook using http.client
def register_webhook():
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-HttpClient"  # GitHub API requires a User-Agent header
    }
    payload = {
        "name": "web",
        "active": True,
        "events": ["*"],  # Listen to all events
        "config": {
            "url": webhook_url,
            "content_type": "json"
        }
    }
    
    conn.request("POST", f"/repos/{OWNER}/{REPO}/hooks", body=json.dumps(payload), headers=headers)
    response = conn.getresponse()
    response_data = response.read().decode()
    
    if response.status == 201:
        print("Webhook successfully created!")
    else:
        print(f"Failed to create webhook: {response.status} - {response_data}")

# List all webhooks to find the one you want to delete
def find_webhook_id() -> int | None:
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-HttpClient"  # Required by GitHub API
    }
    conn.request("GET", f"/repos/{OWNER}/{REPO}/hooks", headers=headers)
    response = conn.getresponse()
    data = response.read().decode()
    
    if response.status == 200:
        webhooks = json.loads(data)
        if not webhooks:
            return None
        for webhook in webhooks:
            if webhook['config']['url'] == webhook_url:
                return int(webhook['id'])
        return None
    else:
        print(f"Failed to list webhooks: {response.status} - {data}")
        return None

# Delete a webhook by ID
def delete_webhook(webhook_id):
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-HttpClient"
    }
    conn.request("DELETE", f"/repos/{OWNER}/{REPO}/hooks/{webhook_id}", headers=headers)
    response = conn.getresponse()
    
    if response.status == 204:
        print(f"Webhook with ID {webhook_id} successfully deleted.")
    else:
        data = response.read().decode()
        print(f"Failed to delete webhook: {response.status} - {data}")

# Register the webhook with the provided URL
register_webhook()

# Define a basic HTTP request handler
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read headers and body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Print headers and JSON body
        print("\nReceived Webhook:")
        print("Headers:")
        for key, value in self.headers.items():
            print(f"{key}: {value}")
        
        print("\nBody:")
        try:
            json_body = json.loads(body)
            print(json.dumps(json_body, indent=4))
        except json.JSONDecodeError:
            print("Received non-JSON body.")
            print(body.decode())
        
        # Send 200 OK response
        self.send_response(200)
        self.end_headers()

# Start HTTP server
def run_server(server_class=HTTPServer, handler_class=WebhookHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

# Run the server
try:
    run_server()
except KeyboardInterrupt:
    print("\nServer stopped by user.")
    ident = find_webhook_id()
    if ident is None:
        print("could not find webhook")
    else:
        delete_webhook(ident)
