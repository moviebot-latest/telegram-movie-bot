from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests

TOKEN = "7432781768:AAEpyVpDOYcVaxi8v7SKUH7wuAvUiNFDb44"
OMDB_API = "c5906b7b"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send Movie Name")

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    name = update.message.text.strip()

    loading = await update.message.reply_text("🔎 Searching movie...")

    try:
        api = f"http://www.omdbapi.com/?t={name}&apikey={OMDB_API}"
        res = requests.get(api, timeout=10)
        data = res.json()
    except:
        await loading.delete()
        await update.message.reply_text("⚠ Server busy try again")
        return

    await loading.delete()

    # MOVIE NOT FOUND
    if data.get("Response") == "False":
        await update.message.reply_text("❌ Movie not found")
        return

    title = data.get("Title")
    year = data.get("Year")
    rating = data.get("imdbRating")
    genre = data.get("Genre")
    runtime = data.get("Runtime")
    poster = data.get("Poster")

    search = title.replace(" ","+")

    # SERVER LINKS
    hdhub4u = f"https://new4.hdhub4u.fo/?s={search}"
    vegamovies = f"https://vegamoviesdl.com/?s={search}"
    moviews = f"https://moviews.xyz/?s={search}"
    worldfree = f"https://worldfree4u.ist/?s={search}"
    filmyzilla = f"https://www.filmyzilla32.com/?s={search}"

    trailer = f"https://www.youtube.com/results?search_query={search}+trailer"

    context.user_data["servers"] = [vegamovies, moviews, worldfree, filmyzilla]

    keyboard = [
        [InlineKeyboardButton("🎥 Watch Trailer", url=trailer)],
        [InlineKeyboardButton("⬇ Download Movie", url=hdhub4u)],
        [InlineKeyboardButton("🌐 More Servers", callback_data="servers")]
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
"""

    await update.message.reply_photo(
        photo = poster,
        caption = caption,
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    vegamovies, moviews, worldfree, filmyzilla = context.user_data["servers"]

    keyboard = [
        [InlineKeyboardButton("Server 2 Vegamovies", url=vegamovies)],
        [InlineKeyboardButton("Server 3 Moviews", url=moviews)],
        [InlineKeyboardButton("Server 4 WorldFree4u", url=worldfree)],
        [InlineKeyboardButton("Server 5 Filmyzilla", url=filmyzilla)]
    ]

    await query.message.reply_text(
        "🌐 Select Server:",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie))
app.add_handler(CallbackQueryHandler(servers, pattern="servers"))

print("Bot Running...")

app.run_polling()