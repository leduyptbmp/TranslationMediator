import logging
import nest_asyncio
import os
import signal
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TOKEN
from handlers import CommandHandler as BotCommandHandler
from utils import setup_logging
from keep_alive import keep_alive

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

async def main():
    # Initialize logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize keep-alive mechanism
    keep_alive()

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
        application.add_handler(CommandHandler("sub", handler.subscribe))  # Short version
        application.add_handler(CommandHandler("unsubscribe", handler.unsubscribe))
        application.add_handler(CommandHandler("unsub", handler.unsubscribe))  # Short version
        application.add_handler(CommandHandler("list", handler.list_subscriptions))
        application.add_handler(CommandHandler("settings", handler.settings))
        logger.info("Command handlers registered successfully")

        # Register message handler for both private messages and channel posts
        logger.info("Registering message handlers...")
        application.add_handler(MessageHandler(
            (filters.TEXT & ~filters.COMMAND) | filters.ChatType.CHANNEL,
            handler.handle_message
        ))
        logger.info("Message handlers registered successfully")

        # Register callback query handlers
        logger.info("Registering callback query handlers...")
        application.add_handler(CallbackQueryHandler(
            handler.handle_subscribe_button,
            pattern="^subscribe:"
        ))
        application.add_handler(CallbackQueryHandler(
            handler.handle_unsubscribe_button,
            pattern="^unsubscribe:"
        ))
        application.add_handler(CallbackQueryHandler(
            handler.handle_language_button,
            pattern="^setlang:"
        ))
        application.add_handler(CallbackQueryHandler(
            handler.handle_subscribe_help,
            pattern="^subscribe_help$"
        ))
        application.add_handler(CallbackQueryHandler(
            handler.handle_back_to_sub,
            pattern="^back_to_sub$"
        ))
        application.add_handler(CallbackQueryHandler(
            handler.handle_translate_only,
            pattern="^translate_only$"
        ))
        logger.info("Callback query handlers registered successfully")

        # Start the bot
        logger.info("Starting bot polling...")

        # Set up signal handlers for graceful shutdown
        PID_FILE = "/tmp/my_bot.pid" # Assuming a PID file location

        def signal_handler(sig, frame):
            logger.info("Received shutdown signal, cleaning up...")
            # Remove PID file
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            logger.info("Cleanup complete, exiting")
            sys.exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error in polling: {e}")
        finally:
            # Always clean up PID file
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot stopped due to error: {e}")