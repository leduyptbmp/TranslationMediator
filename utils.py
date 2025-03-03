import logging
from typing import Optional
from telegram import Update
from telegram.ext import CallbackContext
import time

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}

    def check_rate_limit(self, user_id: int) -> bool:
        current_time = time.time()
        user_requests = self.requests.get(user_id, [])

        # Remove old requests
        user_requests = [req for req in user_requests 
                        if current_time - req < self.time_window]

        if len(user_requests) >= self.max_requests:
            return False

        user_requests.append(current_time)
        self.requests[user_id] = user_requests
        return True

def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

def send_error_message(update: Update, context: CallbackContext, message: str):
    try:
        update.message.reply_text(f"⚠️ Error: {message}")
    except Exception as e:
        logging.error(f"Failed to send error message: {str(e)}")

def validate_channel_id(channel_id: str) -> bool:
    return (channel_id.startswith('@') and len(channel_id) > 1) or \
           (channel_id.startswith('-100') and channel_id[4:].isdigit())