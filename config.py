import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-token-here')

# Rate limiting (messages per minute)
RATE_LIMIT = 30

# Storage file paths
USER_DATA_FILE = 'user_data.json'
CHANNEL_DATA_FILE = 'channel_data.json'

# Colors (in hex)
COLORS = {
    'PRIMARY': '#0088CC',
    'SECONDARY': '#FFFFFF',
    'TEXT': '#222222',
    'SUCCESS': '#3DC23F',
    'BACKGROUND': '#F5F5F5'
}

# Command descriptions
COMMANDS = {
    'start': 'Start the bot',
    'help': 'Show help message',
    'subscribe': 'Subscribe to a channel for translation',
    'unsubscribe': 'Unsubscribe from a channel',
    'list': 'List all subscribed channels',
    'settings': 'Change your translation settings'
}