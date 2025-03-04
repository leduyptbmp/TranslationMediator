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
                "/settings - Cài đặt dịch thuật và ngôn ngữ / View and change translation settings\n"
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
                # Create a text input field
                await update.message.reply_text(
                    "📝 Hãy nhập ID kênh bạn muốn đăng ký:\n"
                    "- @tenkênh cho kênh công khai\n"
                    "- -100xxx cho kênh riêng tư\n\n"
                    "Please enter the channel ID to subscribe:\n"
                    "- @channelname for public channels\n"
                    "- -100xxx for private channels",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❓ Hướng dẫn / Help", callback_data="subscribe_help")]
                    ])
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
            if not update.effective_message:
                return

            message = update.effective_message
            user_id = update.effective_user.id

            # Handle forwarded messages from channels or groups
            if hasattr(message, 'forward_from_chat') and message.forward_from_chat:
                try:
                    source_id = str(message.forward_from_chat.id)
                    source_title = message.forward_from_chat.title
                    message_text = message.text or message.caption or ""
                    chat_type = message.forward_from_chat.type

                    self.logger.info(
                        f"Forward details - Chat ID: {source_id}, "
                        f"Title: {source_title}, "
                        f"Type: {chat_type}, "
                        f"Has text: {bool(message_text)}, "
                        f"User: {user_id}"
                    )

                    # Check if already subscribed
                    is_subscribed = source_id in self.storage.get_subscribed_channels(user_id)
                    self.logger.info(f"User {user_id} subscription status for {source_id}: {is_subscribed}")

                    if not is_subscribed:
                        # Create subscription keyboard
                        keyboard = []

                        # Only show subscribe button for channels and groups
                        if chat_type in ['channel', 'group']:
                            keyboard.append([
                                InlineKeyboardButton(
                                    "✅ Đăng ký / Subscribe",
                                    callback_data=f"subscribe:{source_id}"
                                )
                            ])

                            # Add translate button if there's text
                            if message_text:
                                keyboard.append([
                                    InlineKeyboardButton(
                                        "📝 Dịch tin nhắn này / Translate this message",
                                        callback_data="translate_only"
                                    )
                                ])

                            reply_markup = InlineKeyboardMarkup(keyboard)

                            # Show subscription prompt
                            await message.reply_text(
                                f"🔔 Bạn có muốn đăng ký nhận tin nhắn được dịch từ {source_title}?\n"
                                f"Would you like to subscribe to translated messages from {source_title}?",
                                reply_markup=reply_markup
                            )
                            self.logger.info(f"Showed subscription prompt for {chat_type} {source_id}")
                        return

                    # If already subscribed and has text, translate immediately
                    if message_text:
                        try:
                            detected_lang = self.translator.detect_language(message_text)
                            if detected_lang:
                                preferences = self.storage.get_user_preferences(user_id)
                                target_language = preferences.get('target_language', 'en')
                                if detected_lang != target_language:
                                    translated_text = self.translator.translate_text(
                                        message_text,
                                        target_lang=target_language,
                                        source_lang=detected_lang
                                    )
                                    if translated_text and translated_text != message_text:
                                        await message.reply_text(
                                            f"🔄 {detected_lang} ➜ {target_language}:\n\n"
                                            f"{translated_text}"
                                        )
                                        self.logger.info(f"Translated forwarded message for subscribed user {user_id}")
                        except Exception as e:
                            self.logger.error(f"Translation error for forwarded message: {str(e)}")
                            await send_error_message(
                                update, 
                                context, 
                                "❌ Có lỗi xảy ra khi dịch / Translation error"
                            )
                    return

                except Exception as e:
                    self.logger.error(f"Error processing forwarded message: {str(e)}")
                    await send_error_message(
                        update, 
                        context, 
                        "❌ Có lỗi xảy ra khi xử lý tin nhắn / Error processing message"
                    )
                    return

            # Handle direct messages
            if message.text and not message.forward_from_chat:
                if not await self.rate_limiter.check_rate_limit(user_id):
                    self.logger.warning(f"Rate limit exceeded for user {user_id}")
                    return

                preferences = self.storage.get_user_preferences(user_id)
                target_language = preferences.get('target_language', 'en')
                message_text = message.text

                try:
                    detected_lang = self.translator.detect_language(message_text)
                    self.logger.info(f"Direct message - Source lang: {detected_lang}, Target lang: {target_language}")

                    if detected_lang and detected_lang != target_language:
                        translated_text = self.translator.translate_text(
                            message_text,
                            target_lang=target_language,
                            source_lang=detected_lang
                        )

                        if translated_text and translated_text != message_text:
                            await message.reply_text(
                                f"🔄 {detected_lang} ➜ {target_language}:\n\n"
                                f"{translated_text}"
                            )
                            self.logger.info("Successfully translated direct message")
                except Exception as e:
                    self.logger.error(f"Translation error for direct message: {str(e)}")
                    await send_error_message(
                        update, 
                        context, 
                        "❌ Có lỗi xảy ra khi dịch / Translation error"
                    )
                return

            # Handle channel posts
            if update.channel_post:
                try:
                    channel_id = str(update.channel_post.chat.id)
                    message_text = update.channel_post.text or update.channel_post.caption
                    channel_title = update.channel_post.chat.title or channel_id

                    if not message_text:
                        return

                    self.logger.info(f"Processing channel post from {channel_title} ({channel_id})")

                    # Get all users subscribed to this channel
                    subscribed_users = []
                    for uid, prefs in self.storage.user_data.items():
                        if channel_id in prefs.get('subscribed_channels', []):
                            subscribed_users.append(uid)

                    self.logger.info(f"Found {len(subscribed_users)} subscribers for channel {channel_id}")

                    # Process message for each subscribed user
                    for uid in subscribed_users:
                        try:
                            preferences = self.storage.get_user_preferences(int(uid))
                            target_language = preferences.get('target_language', 'en')

                            # Detect and translate
                            detected_lang = self.translator.detect_language(message_text)
                            self.logger.info(f"Channel post - Source lang: {detected_lang}, Target lang: {target_language}")

                            if detected_lang and detected_lang != target_language:
                                translated_text = self.translator.translate_text(
                                    message_text,
                                    target_lang=target_language,
                                    source_lang=detected_lang
                                )

                                if translated_text and translated_text != message_text:
                                    # Check for media
                                    has_media = bool(
                                        update.channel_post.photo or 
                                        update.channel_post.video or 
                                        update.channel_post.document or 
                                        update.channel_post.animation
                                    )

                                    media_info = "📎 [Có đính kèm phương tiện / Contains media]\n\n" if has_media else ""

                                    forward_message = (
                                        f"📢 Tin nhắn từ kênh {channel_title}:\n"
                                        f"🔄 {detected_lang} ➜ {target_language}:\n\n"
                                        f"{media_info}{translated_text}"
                                    )

                                    await context.bot.send_message(
                                        chat_id=int(uid),
                                        text=forward_message,
                                        disable_web_page_preview=True
                                    )
                                    self.logger.info(f"Successfully sent translation to user {uid}")

                        except Exception as e:
                            self.logger.error(f"Error processing message for user {uid}: {str(e)}")
                            continue

                except Exception as e:
                    self.logger.error(f"Error processing channel post: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in message handler: {str(e)}")
            await send_error_message(
                update, 
                context, 
                "❌ Có lỗi xảy ra / An error occurred"
            )

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            preferences = self.storage.get_user_preferences(user_id)

            # Language code to full name mapping
            language_names = {
                'vi': '🇻🇳 Tiếng Việt',
                'en': '🇺🇸 English',
                'ja': '🇯🇵 日本語',
                'ko': '🇰🇷 한국어',
                'zh': '🇨🇳 中文'
            }

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

            # Get current language code and display full name
            current_lang_code = preferences.get('target_language', 'en')
            current_lang_name = language_names.get(current_lang_code, current_lang_code)

            settings_message = (
                "⚙️ Cài đặt hiện tại / Current Settings:\n"
                f"🔤 Ngôn ngữ dịch / Target Language: {current_lang_name}\n\n"
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

            # Language code to full name mapping
            language_names = {
                'vi': '🇻🇳 Tiếng Việt',
                'en': '🇺🇸 English',
                'ja': '🇯🇵 日本語',
                'ko': '🇰🇷 한국어',
                'zh': '🇨🇳 中文'
            }

            # Get full language name
            language_name = language_names.get(new_language, new_language)

            preferences = self.storage.get_user_preferences(user_id)
            preferences['target_language'] = new_language
            self.storage.set_user_preferences(user_id, preferences)

            success_message = (
                f"✅ Đã đổi ngôn ngữ dịch thành: {language_name}\n"
                f"Target language successfully changed to: {language_name}"
            )
            await query.edit_message_text(success_message)

        except Exception as e:
            self.logger.error(f"Error in language button handler: {str(e)}")
            await query.edit_message_text("❌ Có lỗi xảy ra / An error occurred")

    async def handle_subscribe_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            help_message = (
                "ℹ️ Để đăng ký kênh, bạn có thể:\n\n"
                "1️⃣ Forward tin nhắn từ kênh và nhấn nút 'Đăng ký'\n"
                "2️⃣ Sử dụng lệnh: /sub @tenkênh hoặc /subscribe @tenkênh\n"
                "3️⃣ Dùng ID riêng tư: /sub -100xxx (cho kênh riêng tư)\n\n"
                "How to subscribe to a channel:\n\n"
                "1️⃣ Forward a message from the channel and click 'Subscribe'\n"
                "2️⃣ Use command: /sub @channelname or /subscribe @channelname\n"
                "3️⃣ Use private ID: /sub -100xxx (for private channels)"
            )

            await query.edit_message_text(
                help_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Quay lại / Back", callback_data="back_to_sub")]
                ])
            )

        except Exception as e:
            self.logger.error(f"Error in subscribe help handler: {str(e)}")
            await query.edit_message_text("❌ Có lỗi xảy ra / An error occurred")

    async def handle_back_to_sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            await query.edit_message_text(
                "📝 Hãy nhập ID kênh bạn muốn đăng ký:\n"
                "- @tenkênh cho kênh công khai\n"
                "- -100xxx cho kênh riêng tư\n\n"
                "Please enter the channel ID to subscribe:\n"
                "- @channelname for public channels\n"
                "- -100xxx for private channels",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❓ Hướng dẫn / Help", callback_data="subscribe_help")]
                ])
            )

        except Exception as e:
            self.logger.error(f"Error in back to subscribe handler: {str(e)}")
            await query.edit_message_text("❌ Có lỗi xảy ra / An error occurred")

    # Helper method to translate text and respond
    async def _translate_and_respond(self, update, message_text):
        """Translate the given message text and send the translation as a reply."""
        try:
            if not message_text:
                return False

            user_id = update.effective_user.id
            preferences = self.storage.get_user_preferences(user_id)
            target_language = preferences.get('target_language', 'en')

            # Detect source language
            detected_lang = self.translator.detect_language(message_text)
            if detected_lang and detected_lang != target_language:
                translated_text = self.translator.translate_text(
                    message_text,
                    target_lang=target_language,
                    source_lang=detected_lang
                )

                if translated_text and translated_text != message_text:
                    # Check if message has media
                    has_media = False
                    if update.message:
                        has_media = bool(update.message.photo or update.message.video or 
                                        update.message.document or update.message.animation)

                    media_info = ""
                    if has_media:
                        media_info = "📎 [Có đính kèm phương tiện / Contains media]\n\n"

                    await update.message.reply_text(
                        f"🔄 Dịch / Translation:\n"
                        f"({detected_lang} ➜ {target_language})\n\n"
                        f"{media_info}{translated_text}"
                    )
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error in translate_and_respond: {str(e)}")
            return False

    async def handle_translate_only(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the 'Translate this message' button click."""
        try:
            query = update.callback_query
            await query.answer()

            # Get the original message that was forwarded
            original_message = query.message.reply_to_message
            if not original_message:
                self.logger.warning("Could not find original message to translate")
                await query.edit_message_text(
                    "❌ Không tìm thấy tin nhắn gốc để dịch\n"
                    "Original message not found for translation"
                )
                return

            # Get message text from original message
            message_text = original_message.text or original_message.caption
            if not message_text:
                self.logger.warning("No text content found in original message")
                await query.edit_message_text(
                    "❌ Không tìm thấy nội dung văn bản để dịch\n"
                    "No text content found to translate"
                )
                return

            # Get user preferences
            user_id = query.from_user.id
            preferences = self.storage.get_user_preferences(user_id)
            target_language = preferences.get('target_language', 'en')

            try:
                # Detect source language
                detected_lang = self.translator.detect_language(message_text)
                if not detected_lang:
                    await query.edit_message_text(
                        "❌ Không thể nhận dạng ngôn ngữ\n"
                        "Could not detect language"
                    )
                    return

                self.logger.info(f"Translating text: source={detected_lang}, target={target_language}")

                # Only translate if source and target languages are different
                if detected_lang != target_language:
                    translated_text = self.translator.translate_text(
                        message_text,
                        target_lang=target_language,
                        source_lang=detected_lang
                    )

                    if translated_text and translated_text != message_text:
                        await query.edit_message_text(
                            f"🔄 {detected_lang} ➜ {target_language}:\n\n"
                            f"{translated_text}"
                        )
                        self.logger.info("Successfully translated message on button click")
                        return
                    else:
                        await query.edit_message_text(
                            "❌ Không thể dịch tin nhắn\n"
                            "Could not translate message"
                        )
                        return
                else:
                    await query.edit_message_text(
                        f"ℹ️ Tin nhắn đã ở ngôn ngữ đích ({target_language})\n"
                        f"Message is already in target language ({target_language})"
                    )
                    return

            except Exception as e:
                self.logger.error(f"Translation error: {str(e)}")
                await query.edit_message_text(
                    "❌ Có lỗi xảy ra khi dịch\n"
                    "Translation error occurred"
                )
                return

        except Exception as e:
            self.logger.error(f"Error in translate_only handler: {str(e)}")
            if query:
                await query.edit_message_text(
                    "❌ Có lỗi xảy ra\n"
                    "An error occurred"
                )