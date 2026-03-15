from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

import re
import threading
from flask import Flask

from config import TOKEN, ADMIN_ID
from movie_api import search_movie
from servers import get_servers
from animation import hacker_animation


chat_ids = set()
maintenance = False


# ---------- Render Keep Alive ----------
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web, daemon=True).start()
# --------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_ids.add(update.effective_chat.id)

    await update.message.reply_text(
        "🎬 Send Movie Name\nExample:\nRRR\nAvatar 2009"
    )


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global maintenance

    chat_ids.add(update.effective_chat.id)

    if maintenance:

        await update.message.reply_text(
            "⚠ Server Maintenance\nTry again later"
        )
        return

    text = update.message.text.strip()

    if not re.search("[a-zA-Z]", text):

        await update.message.reply_text(
            "⚠ Send valid movie name"
        )
        return

    await hacker_animation(update)

    loading = await update.message.reply_text("🔎 Searching movie...")

    parts = text.split()

    year = None
    title = text

    if parts[-1].isdigit() and len(parts[-1]) == 4:

        year = parts[-1]
        title = " ".join(parts[:-1])

    data = search_movie(title, year)

    if not data or data.get("Response") != "True":

        await loading.edit_text("❌ Movie not found")
        return

    title = data["Title"]
    year = data["Year"]
    rating = data["imdbRating"]
    genre = data["Genre"]
    runtime = data["Runtime"]
    poster = data["Poster"]

    servers = get_servers(title)

    trailer = f"https://www.youtube.com/results?search_query={title}+trailer"

    context.user_data["servers"] = servers
    context.user_data["trailer"] = trailer

    keyboard = [
        [
            InlineKeyboardButton("🎬 Trailer", url=trailer),
            InlineKeyboardButton("⬇ Download", url=servers[0])
        ],
        [
            InlineKeyboardButton("🌐 More Servers", callback_data="servers")
        ]
    ]

    caption = f"""
🎬 {title} ({year})

⭐ IMDb Rating: {rating}
🎭 Genre: {genre}
🎥 Runtime: {runtime}

⚠ Use Brave Browser for no ads

📢 https://t.me/Latestmovies4Ux
"""

    await loading.delete()

    await update.message.reply_photo(
        photo=poster,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    s = context.user_data["servers"]

    keyboard = [
        [InlineKeyboardButton("Server 2", url=s[1])],
        [InlineKeyboardButton("Server 3", url=s[2])],
        [InlineKeyboardButton("Server 4", url=s[3])],
        [InlineKeyboardButton("Server 5", url=s[4])],
        [InlineKeyboardButton("Server 6", url=s[5])]
    ]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------- Maintenance Commands ----------

async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global maintenance

    if update.message.from_user.id != ADMIN_ID:
        return

    maintenance = True

    for chat in chat_ids:
        try:
            await context.bot.send_message(chat, "⚠ Server Maintenance")
        except:
            pass


async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global maintenance

    if update.message.from_user.id != ADMIN_ID:
        return

    maintenance = False

    for chat in chat_ids:
        try:
            await context.bot.send_message(chat, "✅ Server Online")
        except:
            pass


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("maintenance_on", maintenance_on))
app.add_handler(CommandHandler("maintenance_off", maintenance_off))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie))
app.add_handler(CallbackQueryHandler(servers, pattern="servers"))

print("Bot Running...")

app.run_polling()
