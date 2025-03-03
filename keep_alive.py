
import time
import logging
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

# Simple HTTP request handler
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is alive!')
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        return

# Function to start the HTTP server
def start_server():
    server = HTTPServer(('0.0.0.0', 8080), KeepAliveHandler)
    logger.info("Starting keep-alive server on port 8080")
    server.serve_forever()

# Function to ping the server every 10 minutes
def ping_server():
    url = "https://" + open('.env').read().strip().split('=')[1] + ".repl.co"
    while True:
        try:
            urllib.request.urlopen(url)
            logger.info("Pinged server to keep alive")
        except Exception as e:
            logger.error(f"Failed to ping server: {e}")
        time.sleep(600)  # 10 minutes in seconds

# Start the server and pinging in separate threads
def keep_alive():
    server_thread = threading.Thread(target=start_server, daemon=True)
    ping_thread = threading.Thread(target=ping_server, daemon=True)
    
    server_thread.start()
    ping_thread.start()
    
    logger.info("Keep-alive system initialized")
