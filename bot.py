import logging
import nest_asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TOKEN
from handlers import CommandHandler as BotCommandHandler
from utils import setup_logging

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

async def main():
    # Initialize logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    # Add immediate log messages to verify logging is working
    logger.info("=== Bot Starting ===")
    logger.info("Initializing Telegram bot...")

    try:
        # Initialize the bot
        logger.info("Creating Application instance with token...")
        application = Application.builder().token(TOKEN).build()
        handler = BotCommandHandler()
        logger.info("Bot handler initialized successfully")

        # Register command handlers
        logger.info("Registering command handlers...")
        application.add_handler(CommandHandler("start", handler.start))
        application.add_handler(CommandHandler("help", handler.help))
        application.add_handler(CommandHandler("subscribe", handler.subscribe))
        application.add_handler(CommandHandler("unsubscribe", handler.unsubscribe))
        application.add_handler(CommandHandler("list", handler.list_subscriptions))
        application.add_handler(CommandHandler("settings", handler.settings))
        application.add_handler(CommandHandler("set_language", handler.set_language))
        logger.info("Command handlers registered successfully")

        # Register message handler
        logger.info("Registering message handler...")
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
        logger.info("Message handler registered successfully")

        # Start the bot
        logger.info("Starting bot polling...")
        await application.run_polling()
        logger.info("Bot polling started successfully")

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())