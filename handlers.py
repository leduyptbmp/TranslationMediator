from telegram import Update
from telegram.ext import ContextTypes
from storage import Storage
from translator import TranslationService
from utils import RateLimiter, send_error_message, validate_channel_id
import logging

class CommandHandler:
    def __init__(self):
        self.storage = Storage()
        self.translator = TranslationService()
        self.rate_limiter = RateLimiter(max_requests=30)
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            welcome_message = (
                "👋 Welcome to the Translation Bot!\n\n"
                "I can help you translate messages from other channels and forward them to you.\n\n"
                "Available commands:\n"
                "/subscribe @channel - Subscribe to a channel\n"
                "/unsubscribe @channel - Unsubscribe from a channel\n"
                "/list - Show your subscribed channels\n"
                "/settings - Change translation settings\n"
                "/help - Show this help message"
            )
            await update.message.reply_text(welcome_message)
        except Exception as e:
            self.logger.error(f"Error in start command: {str(e)}")
            await send_error_message(update, context, "Failed to start bot")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id

            if not await self.rate_limiter.check_rate_limit(user_id):
                await send_error_message(update, context, "Rate limit exceeded. Please try again later.")
                return

            if not context.args or len(context.args) != 1:
                await update.message.reply_text("Please provide a channel ID: /subscribe @channel")
                return

            channel_id = context.args[0]
            if not validate_channel_id(channel_id):
                await send_error_message(update, context, "Invalid channel ID format")
                return

            self.storage.add_channel_subscription(user_id, channel_id)
            await update.message.reply_text(f"✅ Successfully subscribed to {channel_id}")

        except Exception as e:
            self.logger.error(f"Error in subscribe command: {str(e)}")
            await send_error_message(update, context, "Failed to subscribe to channel")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id

            if not context.args or len(context.args) != 1:
                await update.message.reply_text("Please provide a channel ID: /unsubscribe @channel")
                return

            channel_id = context.args[0]
            self.storage.remove_channel_subscription(user_id, channel_id)
            await update.message.reply_text(f"✅ Successfully unsubscribed from {channel_id}")

        except Exception as e:
            self.logger.error(f"Error in unsubscribe command: {str(e)}")
            await send_error_message(update, context, "Failed to unsubscribe from channel")

    async def list_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            subscribed_channels = self.storage.get_subscribed_channels(user_id)

            if not subscribed_channels:
                await update.message.reply_text("You haven't subscribed to any channels yet.")
                return

            message = "Your subscribed channels:\n\n" + "\n".join(subscribed_channels)
            await update.message.reply_text(message)

        except Exception as e:
            self.logger.error(f"Error in list command: {str(e)}")
            await send_error_message(update, context, "Failed to list subscriptions")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id

            if not await self.rate_limiter.check_rate_limit(user_id):
                return

            preferences = self.storage.get_user_preferences(user_id)
            target_language = preferences.get('target_language', 'en')

            message_text = update.message.text
            translated_text = self.translator.translate_text(
                message_text,
                target_lang=target_language
            )

            if translated_text and translated_text != message_text:
                await update.message.reply_text(f"🔄 Translation:\n{translated_text}")

        except Exception as e:
            self.logger.error(f"Error in message handler: {str(e)}")