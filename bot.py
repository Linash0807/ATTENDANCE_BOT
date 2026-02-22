from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from attendance import get_attendance
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

import logging
import asyncio
from telegram.error import Conflict

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send /attendance to get your attendance.")

async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching attendance...")
    try:
        data = get_attendance()
        await update.message.reply_text(data)
    except Exception as e:
        logger.error(f"Error in attendance command: {e}", exc_info=True)
        await update.message.reply_text("❌ An error occurred while fetching attendance.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and stop the application if it's a conflict to trigger a retry."""
    logger.error(f"Exception while handling an update: {context.error}")
    if isinstance(context.error, Conflict):
        logger.warning("Conflict detected in internal polling loop. Stopping for retry...")
        if context.application.updater:
            await context.application.updater.stop()

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables.")
        return

    # Wait a few seconds to let any old instance finish its polling session
    # especially important for Railway blue-green deployments
    logger.info("Waiting 10 seconds for any previous instances to settle...")
    await asyncio.sleep(10)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attendance", attendance))
    app.add_error_handler(error_handler)

    logger.info("Starting bot...")
    
    while True:
        try:
            # Initialize and start the application
            await app.initialize()
            await app.start()
            
            # Explicitly delete webhook to avoid conflicts
            logger.info("Deleting webhook and starting polling...")
            await app.bot.delete_webhook(drop_pending_updates=True)
            
            # Start polling
            await app.updater.start_polling(drop_pending_updates=True)
            
            # Keep the bot running until it's stopped (either manually or by error handler)
            while app.updater.running:
                await asyncio.sleep(1)
                
        except Conflict:
            logger.warning("Conflict detected during startup. Retrying in 20 seconds...")
            await asyncio.sleep(20)
        except Exception as e:
            logger.error(f"Unexpected entry point error: {e}", exc_info=True)
            break
        finally:
            # Cleanup
            if app.updater and app.updater.running:
                await app.updater.stop()
            if app.running:
                await app.stop()
            await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
