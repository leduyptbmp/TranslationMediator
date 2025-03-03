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
                "/settings - View and change translation settings\n"
                "/set_language [code] - Change target language (e.g., /set_language vi)\n"
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
            self.logger.info(f"Received message: {message_text}")  # Log full message for debugging

            # Detect source language first
            self.logger.info("Attempting to detect language for message")
            detected_lang = self.translator.detect_language(message_text)
            self.logger.info(f"Detected language: {detected_lang}")

            if detected_lang and detected_lang != target_language:
                self.logger.info(f"Translating from {detected_lang} to {target_language}")
                translated_text = self.translator.translate_text(
                    message_text,
                    target_lang=target_language,
                    source_lang=detected_lang
                )

                if translated_text and translated_text != message_text:
                    await update.message.reply_text(
                        f"🔄 Dịch / Translation:\n"
                        f"({detected_lang} ➜ {target_language})\n\n"
                        f"{message_text}\n"
                        f"➜ {translated_text}"
                    )
                else:
                    self.logger.warning("Translation failed or returned same text")

        except Exception as e:
            self.logger.error(f"Error in message handler: {str(e)}")
            await send_error_message(update, context, "Xin lỗi, có lỗi xảy ra khi dịch / Sorry, there was an error translating")

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            preferences = self.storage.get_user_preferences(user_id)

            settings_message = (
                "⚙️ Current Settings:\n"
                f"🔤 Target Language: {preferences.get('target_language', 'en')}\n\n"
                "To change target language, use:\n"
                "/set_language [language_code]\n\n"
                "Example: /set_language vi\n\n"
                "Common language codes:\n"
                "🇺🇸 en - English\n"
                "🇻🇳 vi - Vietnamese\n"
                "🇯🇵 ja - Japanese\n"
                "🇰🇷 ko - Korean\n"
                "🇨🇳 zh - Chinese"
            )
            await update.message.reply_text(settings_message)

        except Exception as e:
            self.logger.error(f"Error in settings command: {str(e)}")
            await send_error_message(update, context, "Failed to show settings")

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args or len(context.args) != 1:
                await update.message.reply_text(
                    "Please provide a language code: /set_language [language_code]\n"
                    "Example: /set_language vi"
                )
                return

            user_id = update.effective_user.id
            new_language = context.args[0].lower()

            if not self.translator._is_valid_language(new_language):
                await update.message.reply_text(
                    "❌ Invalid language code. Please use a valid language code.\n"
                    "Example: en, vi, ja, ko, zh"
                )
                return

            preferences = self.storage.get_user_preferences(user_id)
            preferences['target_language'] = new_language
            self.storage.set_user_preferences(user_id, preferences)

            await update.message.reply_text(
                f"✅ Target language successfully changed to: {new_language}"
            )

        except Exception as e:
            self.logger.error(f"Error in set_language command: {str(e)}")
            await send_error_message(update, context, "Failed to change language")