from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
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
                "👋 Xin chào! / Welcome to the Translation Bot!\n\n"
                "Bot có thể giúp bạn dịch tin nhắn từ các kênh khác và chuyển tiếp cho bạn.\n"
                "The bot can help you translate messages from other channels and forward them to you.\n\n"
                "Cách đăng ký kênh đơn giản / Easy way to subscribe:\n"
                "1. Forward một tin nhắn từ kênh bạn muốn đăng ký\n"
                "   Forward any message from the channel you want to subscribe to\n"
                "2. Nhấn nút 'Đăng ký' / Click the 'Subscribe' button\n\n"
                "Các lệnh có sẵn / Available commands:\n"
                "/subscribe hoặc /sub @channel - Đăng ký kênh / Subscribe to a channel\n"
                "/unsubscribe hoặc /unsub @channel - Hủy đăng ký / Unsubscribe from a channel\n"
                "/list - Xem các kênh đã đăng ký / Show your subscribed channels\n"
                "/settings - Cài đặt dịch thuật / View and change translation settings\n"
                "/set_language [code] - Đổi ngôn ngữ đích (vd: /set_language vi) / Change target language\n"
                "/help - Hiện thông tin trợ giúp / Show this help message"
            )
            await update.message.reply_text(welcome_message)
        except Exception as e:
            self.logger.error(f"Error in start command: {str(e)}")
            await send_error_message(update, context, "❌ Không thể khởi động bot / Failed to start bot")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Subscribe command received from user {user_id}")

            if not await self.rate_limiter.check_rate_limit(user_id):
                self.logger.warning(f"Rate limit exceeded for user {user_id}")
                await send_error_message(
                    update, 
                    context, 
                    "⚠️ Vui lòng đợi một chút rồi thử lại / Rate limit exceeded. Please try again later."
                )
                return

            if not context.args:
                self.logger.info("Subscribe command received without channel ID")
                await update.message.reply_text(
                    "ℹ️ Có 2 cách để đăng ký kênh:\n\n"
                    "1️⃣ Forward tin nhắn từ kênh và nhấn nút 'Đăng ký'\n"
                    "2️⃣ Sử dụng lệnh /sub hoặc /subscribe:\n"
                    "   /sub @tenkênh\n"
                    "   /subscribe @tenkênh\n\n"
                    "There are 2 ways to subscribe:\n\n"
                    "1️⃣ Forward a message from the channel and click 'Subscribe'\n"
                    "2️⃣ Use /sub or /subscribe command:\n"
                    "   /sub @channelname\n"
                    "   /subscribe @channelname"
                )
                return

            channel_id = context.args[0]
            self.logger.info(f"Attempting to subscribe to channel: {channel_id}")

            if not validate_channel_id(channel_id):
                self.logger.warning(f"Invalid channel ID format: {channel_id}")
                await send_error_message(
                    update, 
                    context, 
                    "❌ ID kênh không hợp lệ. Vui lòng sử dụng định dạng:\n"
                    "- @tenkênh cho kênh công khai\n"
                    "- -100xxx cho kênh riêng tư\n\n"
                    "Invalid channel ID format. Please use:\n"
                    "- @channelname for public channels\n"
                    "- -100xxx for private channels"
                )
                return

            # Verify channel exists and bot has access
            try:
                self.logger.info(f"Verifying access to channel {channel_id}")
                chat = await context.bot.get_chat(channel_id)
                self.logger.info(f"Successfully verified access to channel: {chat.title}")
            except BadRequest as e:
                self.logger.error(f"Failed to access channel {channel_id}: {str(e)}")
                await send_error_message(
                    update, 
                    context, 
                    "❌ Không thể truy cập kênh. Vui lòng kiểm tra:\n"
                    "1. ID kênh chính xác\n"
                    "2. Bot đã được thêm vào kênh\n"
                    "3. Kênh là công khai\n\n"
                    "Cannot access channel. Please check:\n"
                    "1. Channel ID is correct\n"
                    "2. Bot is added to the channel\n"
                    "3. Channel is public"
                )
                return

            self.logger.info(f"Adding channel subscription for user {user_id}: {channel_id}")
            self.storage.add_channel_subscription(user_id, channel_id)

            success_message = (
                f"✅ Đăng ký thành công kênh {chat.title} ({channel_id})\n"
                f"Successfully subscribed to {chat.title} ({channel_id})\n\n"
                "🔄 Bot sẽ tự động dịch tin nhắn mới\n"
                "Bot will automatically translate new messages"
            )
            await update.message.reply_text(success_message)
            self.logger.info(f"Successfully subscribed user {user_id} to channel {channel_id}")

        except Exception as e:
            self.logger.error(f"Error in subscribe command: {str(e)}")
            await send_error_message(
                update, 
                context, 
                "❌ Không thể đăng ký kênh / Failed to subscribe to channel"
            )

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.effective_message:
                self.logger.error("No message object in update")
                return

            user_id = update.effective_user.id

            if not context.args:
                subscribed_channels = self.storage.get_subscribed_channels(user_id)
                if not subscribed_channels:
                    await update.effective_message.reply_text(
                        "📝 Bạn chưa đăng ký kênh nào\n"
                        "You haven't subscribed to any channels yet"
                    )
                else:
                    # Create keyboard with buttons for each channel
                    keyboard = []
                    for channel in subscribed_channels:
                        keyboard.append([
                            InlineKeyboardButton(
                                f"❌ {channel}",
                                callback_data=f"unsubscribe:{channel}"
                            )
                        ])
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.effective_message.reply_text(
                        "🗑 Chọn kênh muốn hủy đăng ký:\n"
                        "Select channel to unsubscribe:",
                        reply_markup=reply_markup
                    )
                return

            channel_id = context.args[0]
            if not validate_channel_id(channel_id):
                await send_error_message(
                    update, 
                    context, 
                    "❌ ID kênh không hợp lệ / Invalid channel ID format"
                )
                return

            subscribed_channels = self.storage.get_subscribed_channels(user_id)
            if channel_id not in subscribed_channels:
                await update.effective_message.reply_text(
                    f"⚠️ Bạn chưa đăng ký kênh {channel_id}\n"
                    f"You are not subscribed to {channel_id}"
                )
                return

            self.storage.remove_channel_subscription(user_id, channel_id)
            await update.effective_message.reply_text(
                f"✅ Đã hủy đăng ký kênh {channel_id}\n"
                f"Successfully unsubscribed from {channel_id}"
            )

        except Exception as e:
            self.logger.error(f"Error in unsubscribe command: {str(e)}")
            await send_error_message(
                update, 
                context, 
                "❌ Không thể hủy đăng ký kênh / Failed to unsubscribe from channel"
            )

    async def list_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            subscribed_channels = self.storage.get_subscribed_channels(user_id)

            if not subscribed_channels:
                await update.message.reply_text(
                    "📝 Bạn chưa đăng ký kênh nào\n"
                    "You haven't subscribed to any channels yet"
                )
                return

            message = (
                "📋 Các kênh đã đăng ký / Your subscribed channels:\n\n" + 
                "\n".join(f"• {channel}" for channel in subscribed_channels)
            )
            await update.message.reply_text(message)

        except Exception as e:
            self.logger.error(f"Error in list command: {str(e)}")
            await send_error_message(
                update, 
                context, 
                "❌ Không thể hiển thị danh sách kênh / Failed to list subscriptions"
            )

    async def handle_subscribe_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()  # Acknowledge the button click

            # Extract channel info from callback data
            # Format: "subscribe:channel_id"
            channel_id = query.data.split(':')[1]
            user_id = query.from_user.id

            if not validate_channel_id(channel_id):
                await query.edit_message_text(
                    "❌ ID kênh không hợp lệ / Invalid channel ID format"
                )
                return

            try:
                chat = await context.bot.get_chat(channel_id)
                self.storage.add_channel_subscription(user_id, channel_id)

                success_message = (
                    f"✅ Đăng ký thành công kênh {chat.title} ({channel_id})\n"
                    f"Successfully subscribed to {chat.title} ({channel_id})\n\n"
                    "🔄 Bot sẽ tự động dịch tin nhắn mới\n"
                    "Bot will automatically translate new messages"
                )
                await query.edit_message_text(success_message)

            except BadRequest as e:
                self.logger.error(f"Failed to access channel {channel_id}: {str(e)}")
                await query.edit_message_text(
                    "❌ Không thể truy cập kênh. Vui lòng kiểm tra:\n"
                    "1. ID kênh chính xác\n"
                    "2. Bot đã được thêm vào kênh\n"
                    "3. Kênh là công khai\n\n"
                    "Cannot access channel. Please check:\n"
                    "1. Channel ID is correct\n"
                    "2. Bot is added to the channel\n"
                    "3. Channel is public"
                )

        except Exception as e:
            self.logger.error(f"Error in subscribe button handler: {str(e)}")
            await query.edit_message_text("❌ Có lỗi xảy ra / An error occurred")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Handle forwarded channel messages for easy subscription
            if update.message:
                forward_from = None
                if hasattr(update.message, 'forward_from_chat'):
                    forward_from = update.message.forward_from_chat
                elif hasattr(update.message, 'forward_from'):
                    forward_from = update.message.forward_from
                elif hasattr(update.message, 'forward_from_message_id'):
                    # Handle messages forwarded from private groups
                    await update.message.reply_text(
                        "⚠️ Không thể đăng ký tin nhắn từ nhóm riêng tư.\n"
                        "Vui lòng thêm bot vào nhóm để sử dụng.\n\n"
                        "Cannot subscribe to private group messages.\n"
                        "Please add the bot to the group to use it."
                    )
                    return

                if forward_from and forward_from.type in ['channel', 'supergroup', 'bot']:
                    channel_id = str(forward_from.id)
                    user_id = update.effective_user.id

                    # Check if already subscribed
                    if channel_id in self.storage.get_subscribed_channels(user_id):
                        await update.message.reply_text(
                            f"ℹ️ Bạn đã đăng ký kênh/bot này rồi\n"
                            f"You are already subscribed to this channel/bot"
                        )
                        return

                    # Create subscription button
                    keyboard = [[
                        InlineKeyboardButton(
                            "✅ Đăng ký / Subscribe",
                            callback_data=f"subscribe:{channel_id}"
                        )
                    ]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    title = forward_from.title or forward_from.first_name or channel_id
                    await update.message.reply_text(
                        f"🔔 Bạn có muốn đăng ký nhận tin nhắn được dịch từ {title}?\n"
                        f"Would you like to subscribe to translated messages from {title}?",
                        reply_markup=reply_markup
                    )
                    return

            # Handle channel posts
            if update.channel_post:
                channel_id = str(update.channel_post.chat.id)
                message_text = update.channel_post.text

                if not message_text:
                    self.logger.info(f"Skipping non-text message from channel {channel_id}")
                    return

                self.logger.info(f"Received channel message from {channel_id}: {message_text}")

                # Get all users subscribed to this channel
                for user_id, preferences in self.storage.user_data.items():
                    if channel_id in preferences.get('subscribed_channels', []):
                        target_language = preferences.get('target_language', 'en')
                        self.logger.info(f"Processing message for user {user_id} with target language {target_language}")

                        # Detect and translate
                        detected_lang = self.translator.detect_language(message_text)
                        self.logger.info(f"Detected language for channel message: {detected_lang}")

                        if detected_lang and detected_lang != target_language:
                            self.logger.info(f"Translating message from {detected_lang} to {target_language}")
                            translated_text = self.translator.translate_text(
                                message_text,
                                target_lang=target_language,
                                source_lang=detected_lang
                            )

                            if translated_text and translated_text != message_text:
                                forward_message = (
                                    f"📢 Tin nhắn từ kênh {update.channel_post.chat.title} ({channel_id}):\n\n"
                                    f"🔄 Dịch / Translation:\n"
                                    f"({detected_lang} ➜ {target_language})\n\n"
                                    f"{message_text}\n"
                                    f"➜ {translated_text}"
                                )
                                try:
                                    await context.bot.send_message(
                                        chat_id=int(user_id),
                                        text=forward_message,
                                        disable_web_page_preview=True
                                    )
                                    self.logger.info(f"Successfully sent translated message to user {user_id}")
                                except Exception as e:
                                    self.logger.error(f"Failed to send translation to user {user_id}: {str(e)}")

            # Handle direct messages for translation
            if update.message and update.message.text:
                user_id = update.effective_user.id
                if not await self.rate_limiter.check_rate_limit(user_id):
                    self.logger.warning(f"Rate limit exceeded for user {user_id}")
                    return

                preferences = self.storage.get_user_preferences(user_id)
                target_language = preferences.get('target_language', 'en')

                message_text = update.message.text
                self.logger.info(f"Received direct message: {message_text}")

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
            await send_error_message(
                update, 
                context, 
                "❌ Xin lỗi, có lỗi xảy ra khi dịch / Sorry, there was an error translating"
            )

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            preferences = self.storage.get_user_preferences(user_id)

            # Create keyboard with language options
            keyboard = [
                [
                    InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang:vi"),
                    InlineKeyboardButton("🇺🇸 English", callback_data="setlang:en")
                ],
                [
                    InlineKeyboardButton("🇯🇵 日本語", callback_data="setlang:ja"),
                    InlineKeyboardButton("🇰🇷 한국어", callback_data="setlang:ko")
                ],
                [
                    InlineKeyboardButton("🇨🇳 中文", callback_data="setlang:zh")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            settings_message = (
                "⚙️ Cài đặt hiện tại / Current Settings:\n"
                f"🔤 Ngôn ngữ dịch / Target Language: {preferences.get('target_language', 'en')}\n\n"
                "Chọn ngôn ngữ mới / Select new language:"
            )
            await update.message.reply_text(settings_message, reply_markup=reply_markup)

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

    async def handle_unsubscribe_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            # Extract channel info from callback data
            # Format: "unsubscribe:channel_id"
            channel_id = query.data.split(':')[1]
            user_id = query.from_user.id

            if not validate_channel_id(channel_id):
                await query.edit_message_text(
                    "❌ ID kênh không hợp lệ / Invalid channel ID format"
                )
                return

            self.storage.remove_channel_subscription(user_id, channel_id)
            await query.edit_message_text(
                f"✅ Đã hủy đăng ký kênh {channel_id}\n"
                f"Successfully unsubscribed from {channel_id}"
            )

        except Exception as e:
            self.logger.error(f"Error in unsubscribe button handler: {str(e)}")
            await query.edit_message_text("❌ Có lỗi xảy ra / An error occurred")

    async def handle_language_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            # Extract language code from callback data
            # Format: "setlang:lang_code"
            new_language = query.data.split(':')[1]
            user_id = query.from_user.id

            if not self.translator._is_valid_language(new_language):
                await query.edit_message_text(
                    "❌ Mã ngôn ngữ không hợp lệ / Invalid language code"
                )
                return

            preferences = self.storage.get_user_preferences(user_id)
            preferences['target_language'] = new_language
            self.storage.set_user_preferences(user_id, preferences)

            success_message = (
                f"✅ Đã đổi ngôn ngữ dịch thành: {new_language}\n"
                f"Target language successfully changed to: {new_language}"
            )
            await query.edit_message_text(success_message)

        except Exception as e:
            self.logger.error(f"Error in language button handler: {str(e)}")
            await query.edit_message_text("❌ Có lỗi xảy ra / An error occurred")