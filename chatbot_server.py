from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
import json
import urllib.request
from app.services.gmail_service import send_email

ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"  # paste your full key here

class ChatbotHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        chatbot_path = os.path.join(os.path.dirname(__file__), "frontend", "chatbot.html")
        with open(chatbot_path, "r", encoding="utf-8") as f:
            self.wfile.write(f.read().encode())

    def do_POST(self):
        if self.path == '/chat':
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            messages = body.get('messages', [])
            customer_email = body.get('email')

            try:
                payload = json.dumps({
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "system": "You are AutoPilot AI, a helpful CRM business assistant. Help with leads, sales, revenue, and business automation. Be concise and friendly.",
                    "messages": messages
                }).encode()

                req = urllib.request.Request(
                    'https://api.anthropic.com/v1/messages',
                    data=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'x-api-key': ANTHROPIC_API_KEY,
                        'anthropic-version': '2023-06-01'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())
                    reply = data['content'][0]['text']
                if customer_email:
                       send_email(
                       customer_email,
                       "AutoPilot AI Response",
                         reply
                  )

            except Exception as e:
                reply = f"Error: {str(e)}"

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'reply': reply}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

def start_chatbot_server():
    server = HTTPServer(('localhost', 8502), ChatbotHandler)
    server.serve_forever()

thread = threading.Thread(target=start_chatbot_server, daemon=True)
thread.start()