from flask import Flask
import threading
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "7432781768:AAEpyVpDOYcVaxi8v7SKUH7wuAvUiNFDb44"
OMDB_API = "c5906b7b"

# ---------- Flask server (Render port fix) ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

# ---------- Telegram Bot ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send Movie Name")

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    name = update.message.text.strip()

    msg = await update.message.reply_text("🔎 Searching movie...")

    try:
        url = f"http://www.omdbapi.com/?t={name}&apikey={OMDB_API}"
        res = requests.get(url)
        data = res.json()
    except:
        await msg.edit_text("⚠ Server busy")
        return

    if data.get("Response") == "False":
        await msg.edit_text("❌ Movie not found")
        return

    title = data["Title"]
    year = data["Year"]
    rating = data["imdbRating"]
    genre = data["Genre"]
    runtime = data["Runtime"]
    poster = data["Poster"]

    search = title.replace(" ", "+")

    hdhub = f"https://new4.hdhub4u.fo/?s={search}"
    vegamovies = f"https://vegamoviesdl.com/?s={search}"

    trailer = f"https://www.youtube.com/results?search_query={search}+trailer"

    buttons = [
        [InlineKeyboardButton("🎥 Trailer", url=trailer)],
        [InlineKeyboardButton("⬇ Download", url=hdhub)],
        [InlineKeyboardButton("Server 2", url=vegamovies)]
    ]

    text = f"""
🎬 {title} ({year})

⭐ IMDb: {rating}
🎭 Genre: {genre}
⏱ Runtime: {runtime}

━━━━━━━━━━━━
🍿 Watch • Download
━━━━━━━━━━━━
"""

    await update.message.reply_photo(
        photo=poster,
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- Run Bot ----------

bot = ApplicationBuilder().token(TOKEN).build()

bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie))

print("Bot Running...")
bot.run_polling()
