
import os
import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from db import MessageRecord, SessionLocal
import datetime

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/telegram"
WEBHOOK_PORT = 8443
WEBHOOK_URL = f"https://checker.gift{WEBHOOK_PATH}"
ADMIN_IDS = [6538167049]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    msg = update.message
    if msg:
        reply_to_user_id = None
        if msg.reply_to_message:
            original_msg = session.query(MessageRecord).filter_by(
                chat_id=str(msg.chat_id),
                message_id=msg.reply_to_message.message_id
            ).first()
            if original_msg:
                reply_to_user_id = original_msg.user_id

        record = MessageRecord(
            message_id=msg.message_id,
            chat_id=str(msg.chat_id),
            chat_title=msg.chat.title if msg.chat.type != "private" else None,
            user_id=str(msg.from_user.id),
            sender=msg.from_user.username or msg.from_user.first_name,
            text=msg.text or "(non-text message)",
            date=msg.date,
            chat_type=msg.chat.type,
            source="user",
            reply_to_user_id=reply_to_user_id,
        )
        session.add(record)
        session.commit()
        logger.info(f"User message saved: {record.text}")
    session.close()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error: {context.error}")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    await app.bot.set_webhook(url=WEBHOOK_URL)

    runner = web.AppRunner(app.web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    logger.info(f"Bot started with webhook at {WEBHOOK_URL}")
    await site.start()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
