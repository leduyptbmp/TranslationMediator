
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
    try:
        with open('.env', 'r') as env_file:
            env_content = env_file.read().strip()
            # Find REPL_NAME line safely
            for line in env_content.split('\n'):
                if line.startswith('REPL_NAME='):
                    repl_name = line.split('=', 1)[1].strip()
                    url = f"https://{repl_name}.repl.co"
                    break
            else:
                # If no REPL_NAME found, try to use REPL_SLUG environment variable
                import os
                repl_slug = os.environ.get('REPL_SLUG')
                if repl_slug:
                    url = f"https://{repl_slug}.repl.co"
                else:
                    logger.error("Could not determine Repl URL, skipping ping")
                    return
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return

    while True:
        try:
            logger.info(f"Pinging {url} to keep alive")
            urllib.request.urlopen(url)
            logger.info("Successfully pinged server to keep alive")
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
