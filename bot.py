from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")

MSG = "⚠️ This bot is expired.\n\n👉 Please use the new bot below 👇"

# Button
def get_button():
    keyboard = [
        [InlineKeyboardButton("🚀 OPEN NEW BOT", url="https://t.me/ALLH4CKERGODS_BOT")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Typing + reply
async def send_reply(update):
    await update.message.chat.send_action(action="typing")
    await asyncio.sleep(1.5)

    await update.message.reply_text(
        MSG,
        reply_markup=get_button()
    )

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update)

# ✅ FIXED MAIN (NO asyncio.run)
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("✅ Bot Running without event loop error...")

    app.run_polling()   # ✅ direct run

if __name__ == "__main__":
    main()
