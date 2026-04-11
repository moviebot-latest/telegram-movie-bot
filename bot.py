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

# Typing + reply function
async def send_reply(update):
    # typing animation
    await update.message.chat.send_action(action="typing")
    await asyncio.sleep(1.5)

    await update.message.reply_text(
        MSG,
        reply_markup=get_button()
    )

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update)

# All messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update)

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("✅ Bot Running with Typing Animation...")

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
