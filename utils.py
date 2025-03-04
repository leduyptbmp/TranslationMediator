import logging
import os
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
import time

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}

    async def check_rate_limit(self, user_id: int) -> bool:
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
    try:
        # Create logs directory if it doesn't exist
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)

        # Configure logging format
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)

        # Set up file handler
        file_handler = logging.FileHandler(os.path.join(logs_dir, 'telegram_bot.log'))
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Set up specific loggers
        for logger_name in ['translator', 'bot', 'handlers']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)

        logging.info("Logging setup completed successfully")

    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

def validate_channel_id(channel_id: str) -> bool:
    return (channel_id.startswith('@') and len(channel_id) > 1) or \
           (channel_id.startswith('-100') and channel_id[4:].isdigit())

async def send_error_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        if update.effective_message:
            await update.effective_message.reply_text(f"⚠️ Error: {message}")
        else:
            logging.error(f"Could not send error message: no effective message")
    except Exception as e:
        logging.error(f"Failed to send error message: {str(e)}")