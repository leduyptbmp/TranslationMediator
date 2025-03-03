import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from config import TOKEN
from handlers import CommandHandler as BotCommandHandler
from utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Initializing Telegram bot...")

    try:
        # Initialize the bot
        logger.info("Creating Updater instance with token...")
        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher
        handler = BotCommandHandler()
        logger.info("Bot handler initialized successfully")

        # Register command handlers
        logger.info("Registering command handlers...")
        dispatcher.add_handler(CommandHandler("start", handler.start))
        dispatcher.add_handler(CommandHandler("help", handler.help))
        dispatcher.add_handler(CommandHandler("subscribe", handler.subscribe))
        dispatcher.add_handler(CommandHandler("unsubscribe", handler.unsubscribe))
        dispatcher.add_handler(CommandHandler("list", handler.list_subscriptions))
        logger.info("Command handlers registered successfully")

        # Register message handler
        logger.info("Registering message handler...")
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handler.handle_message))
        logger.info("Message handler registered successfully")

        # Start the bot
        logger.info("Starting bot polling...")
        updater.start_polling()
        logger.info("Bot polling started successfully")
        updater.idle()

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == '__main__':
    main()