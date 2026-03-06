from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import threading
from flask import Flask
import os
import re

TOKEN = os.getenv("BOT_TOKEN")
OMDB_API = os.getenv("OMDB_API")

# ---------- WEB SERVER (Render Keep Alive) ----------
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running"

def run_web():
    port = int(os.environ.get("PORT",10000))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
# ----------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send Movie Name")


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    # invalid input check
    if not re.search("[a-zA-Z]", text):
        await update.message.reply_text(
            "⚠ Send valid movie name\nExample: RRR, Avatar 2009"
        )
        return

    loading = await update.message.reply_text("🔎 Searching movie...")

    parts = text.split()

    year = None
    title = text

    # optional year
    if parts[-1].isdigit() and len(parts[-1]) == 4:
        year = parts[-1]
        title = " ".join(parts[:-1])

    try:
        if year:
            api = f"http://www.omdbapi.com/?t={title}&y={year}&apikey={OMDB_API}"
        else:
            api = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API}"

        res = requests.get(api, timeout=10)
        data = res.json()

    except Exception as e:
        print(e)
        await loading.edit_text("⚠ Server busy try again")
        return

    if not data or data.get("Response") != "True":
        await loading.edit_text(
            "❌ Movie not found\n\nExample:\nRRR\nAvatar 2009\nBorder 1997"
        )
        return

    title = data.get("Title")
    year = data.get("Year")
    rating = data.get("imdbRating")
    genre = data.get("Genre")
    runtime = data.get("Runtime")
    poster = data.get("Poster")

    if poster == "N/A":
        poster = "https://via.placeholder.com/300x450?text=No+Poster"

    search = title.replace(" ","+")

    # ---------- SERVERS ----------
    server1 = f"https://new4.hdhub4u.fo/?s={search}"
    server2 = f"https://123mkv.bar/?s={search}"
    server3 = f"https://mkvcinemas.sb/?s={search}"
    server4 = f"https://worldfree4u.ist/?s={search}"
    server5 = f"https://bolly4u.gifts/?s={search}"
    server6 = f"https://1filmyfly.org/?s={search}"
    # -----------------------------

    trailer = f"https://www.youtube.com/results?search_query={search}+trailer"

    context.user_data["servers"] = [server1,server2,server3,server4,server5,server6]
    context.user_data["trailer"] = trailer

    keyboard = [
        [
            InlineKeyboardButton("🎬 Trailer", url=trailer),
            InlineKeyboardButton("⬇ Download Server 1", url=server1)
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

━━━━━━━━━━━━━━
🍿 Watch • Download • Enjoy
━━━━━━━━━━━━━━

⚠ Use Brave Browser for no ads

📢 <a href="https://t.me/Latestmovies4Ux">Join Latest Movie Channel</a>
"""

    await loading.delete()

    await update.message.reply_photo(
        photo=poster,
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    s1,s2,s3,s4,s5,s6 = context.user_data["servers"]

    keyboard = [
        [InlineKeyboardButton("Server 2", url=s2)],
        [InlineKeyboardButton("Server 3", url=s3)],
        [InlineKeyboardButton("Server 4", url=s4)],
        [InlineKeyboardButton("Server 5", url=s5)],
        [InlineKeyboardButton("Server 6", url=s6)],
        [InlineKeyboardButton("⬅ Back", callback_data="back")]
    ]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    s1 = context.user_data["servers"][0]
    trailer = context.user_data["trailer"]

    keyboard = [
        [
            InlineKeyboardButton("🎬 Trailer", url=trailer),
            InlineKeyboardButton("⬇ Download Server 1", url=s1)
        ],
        [
            InlineKeyboardButton("🌐 More Servers", callback_data="servers")
        ]
    ]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie))
app.add_handler(CallbackQueryHandler(servers, pattern="servers"))
app.add_handler(CallbackQueryHandler(back, pattern="back"))

print("Bot Running...")

app.run_polling(
    drop_pending_updates=True,
    allowed_updates=Update.ALL_TYPES
)
