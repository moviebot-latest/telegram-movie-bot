from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
import requests
import threading
import json
import os
import asyncio
from flask import Flask

TOKEN    = os.getenv("BOT_TOKEN")
OMDB_API = os.getenv("OMDB_API")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ═══════════════════════════════════════
#         WEB SERVER (RENDER KEEP ALIVE)
# ═══════════════════════════════════════
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "🎬 CineBot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()


# ═══════════════════════════════════════
#         PERSISTENT STORAGE (JSON)
# ═══════════════════════════════════════
SERVERS_FILE = "servers.json"

DEFAULT_SERVERS = {
    "s1": {"name": "HdHub4u",     "url": "https://new4.hdhub4u.fo/?s="},
    "s2": {"name": "123Mkv",      "url": "https://123mkv.bar/?s="},
    "s3": {"name": "MkvCinemas",  "url": "https://mkvcinemas.sb/?s="},
    "s4": {"name": "WorldFree4u", "url": "https://worldfree4u.ist/?s="},
    "s5": {"name": "Bolly4u",     "url": "https://bolly4u.gifts/?s="},
}

def load_servers() -> dict:
    """File se servers load karo, file nahi hai to default use karo"""
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE, "r") as f:
                data = json.load(f)
                # Naye keys missing ho to default se fill karo
                for k, v in DEFAULT_SERVERS.items():
                    if k not in data:
                        data[k] = v.copy()
                return data
        except:
            pass
    # File nahi hai — default copy karke save karo
    save_servers(DEFAULT_SERVERS)
    return {k: v.copy() for k, v in DEFAULT_SERVERS.items()}

def save_servers(data: dict):
    """Servers ko file me save karo (permanent)"""
    with open(SERVERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def reset_servers():
    """Sab servers default pe reset karo"""
    data = {k: v.copy() for k, v in DEFAULT_SERVERS.items()}
    save_servers(data)
    return data

# ── Bot start hote hi load karo ──
bot_servers = load_servers()


# ═══════════════════════════════════════
#              ANIMATIONS
# ═══════════════════════════════════════
SEARCH_FRAMES = ["🔍 S•e•a•r•c•h•i•n•g .", "🔍 S•e•a•r•c•h•i•n•g ..", "🎬 F•o•u•n•d !"]
SERVER_FRAMES = ["🌐 Connecting .  ", "🌐 Connecting .. ", "🌐 Connecting ...", "⚡ Servers Ready!"]
BACK_FRAMES   = ["🔄 Going Back .  ", "🔄 Going Back .. ", "🎬 Back to Movie!"]
SAVE_FRAMES   = ["💾 Saving .  ", "💾 Saving .. ", "✅ Saved!"]

# ConversationHandler states
WAITING_URL, WAITING_NAME = range(2)


# ═══════════════════════════════════════
#           ADMIN CHECK
# ═══════════════════════════════════════
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ═══════════════════════════════════════
#                START
# ═══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_note = "\n\n🔧 *Admin:* Use /admin to manage servers." if is_admin(update.effective_user.id) else ""
    await update.message.reply_text(
        "🎬 *Welcome to CineBot!*\n\n"
        "Send any *Movie Name* to get:\n"
        "• 📽 Poster + Details\n"
        "• ⭐ IMDb Rating\n"
        "• 🎥 Trailer Link\n"
        "• ⬇️ Fast Download Servers\n\n"
        "🔎 *Just type a movie name...*" + admin_note,
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════
#          ADMIN PANEL — /admin
# ═══════════════════════════════════════
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 *Access Denied!*", parse_mode="Markdown")
        return

    # Fresh load from file
    global bot_servers
    bot_servers = load_servers()

    text  = "🔧 *Admin Panel — Server Manager*\n\n"
    text += "📋 *Current Active Servers:*\n"
    text += "─────────────────────────\n"
    for i in range(1, 6):
        key = f"s{i}"
        text += f"*{i}.* _{bot_servers[key]['name']}_\n`{bot_servers[key]['url']}`\n\n"
    text += "─────────────────────────\n"
    text += "🖊 Tap a server to edit it 👇"

    keyboard = [
        [InlineKeyboardButton(
            f"✏️ Server {i} — {bot_servers[f's{i}']['name']}",
            callback_data=f"admin_edit_s{i}"
        )]
        for i in range(1, 6)
    ]
    keyboard.append([InlineKeyboardButton("🔄 Reset All to Default", callback_data="admin_reset")])

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ═══════════════════════════════════════
#       ADMIN — EDIT BUTTON PRESSED
# ═══════════════════════════════════════
async def admin_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("🚫 Access Denied!", show_alert=True)
        return ConversationHandler.END

    server_key = query.data.replace("admin_edit_", "")  # "s1" .. "s5"
    context.user_data["editing_server"] = server_key

    val = bot_servers[server_key]
    num = server_key[1]

    await query.message.reply_text(
        f"✏️ *Editing Server {num} — {val['name']}*\n\n"
        f"🔗 *Current URL:*\n`{val['url']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Send new website URL*\n"
        f"Format: `https://newsite.com/?s=`\n\n"
        f"_(Search term auto-attach hogi end mein)_\n\n"
        f"/cancel — Cancel karne ke liye",
        parse_mode="Markdown"
    )

    return WAITING_URL


# ═══════════════════════════════════════
#       ADMIN — NEW URL RECEIVE
# ═══════════════════════════════════════
async def admin_receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    new_url = update.message.text.strip()

    if not new_url.startswith("http"):
        await update.message.reply_text(
            "❌ *Invalid URL!*\n\n"
            "Must start with `http://` or `https://`\n\n"
            "Try again or /cancel",
            parse_mode="Markdown"
        )
        return WAITING_URL

    context.user_data["new_url"] = new_url
    server_key   = context.user_data.get("editing_server")
    current_name = bot_servers[server_key]["name"]

    await update.message.reply_text(
        f"✅ *URL noted!*\n`{new_url}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Now send the display name*\n"
        f"Current: `{current_name}`\n\n"
        f"_(Same name rakhna ho to wahi bhejo)_\n\n"
        f"/cancel — Cancel karne ke liye",
        parse_mode="Markdown"
    )

    return WAITING_NAME


# ═══════════════════════════════════════
#       ADMIN — NEW NAME RECEIVE + SAVE
# ═══════════════════════════════════════
async def admin_receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    global bot_servers

    new_name   = update.message.text.strip()
    new_url    = context.user_data.get("new_url")
    server_key = context.user_data.get("editing_server")
    num        = server_key[1]

    # ── Saving animation ──
    loader = await update.message.reply_text(SAVE_FRAMES[0])
    for frame in SAVE_FRAMES[1:]:
        await asyncio.sleep(0.6)
        await loader.edit_text(frame)

    # ── Update memory ──
    bot_servers[server_key]["url"]  = new_url
    bot_servers[server_key]["name"] = new_name

    # ── Save to file (PERMANENT) ──
    save_servers(bot_servers)

    await asyncio.sleep(0.4)
    await loader.delete()

    await update.message.reply_text(
        f"🎉 *Server {num} Updated & Saved!*\n\n"
        f"🏷 *Name:* `{new_name}`\n"
        f"🔗 *URL:* `{new_url}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ Permanently saved — bot restart ke baad bhi active rahega\n"
        f"🎬 Naye movie searches abhi se yahi link use karenge\n\n"
        f"/admin — Panel wapas kholne ke liye",
        parse_mode="Markdown"
    )

    return ConversationHandler.END


# ═══════════════════════════════════════
#       ADMIN — RESET ALL
# ═══════════════════════════════════════
async def admin_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("🚫 Access Denied!", show_alert=True)
        return

    global bot_servers
    bot_servers = reset_servers()  # Default pe reset + file me save

    text = "🔄 *All Servers Reset to Default!*\n\n"
    for i in range(1, 6):
        text += f"*{i}.* _{DEFAULT_SERVERS[f's{i}']['name']}_\n`{DEFAULT_SERVERS[f's{i}']['url']}`\n\n"
    text += "✅ *Saved permanently.*\n/admin — Panel kholne ke liye"

    await query.message.reply_text(text, parse_mode="Markdown")


# ═══════════════════════════════════════
#              CANCEL
# ═══════════════════════════════════════
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ *Cancelled.* Koi changes save nahi hue.\n\n/admin — Panel kholne ke liye",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ═══════════════════════════════════════
#            MOVIE SEARCH
# ═══════════════════════════════════════
async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name   = update.message.text.strip()
    loader = await update.message.reply_text(SEARCH_FRAMES[0])

    await asyncio.sleep(0.7)
    await loader.edit_text(SEARCH_FRAMES[1])
    await asyncio.sleep(0.7)

    try:
        res  = requests.get(f"http://www.omdbapi.com/?t={name}&apikey={OMDB_API}", timeout=5)
        data = res.json()
    except:
        await loader.edit_text("⚠️ Server busy, try again later.")
        return

    if data.get("Response") == "False":
        await loader.edit_text("❌ *Movie not found!*\n\nCheck spelling and try again.", parse_mode="Markdown")
        return

    await loader.edit_text(SEARCH_FRAMES[2])
    await asyncio.sleep(0.5)
    await loader.delete()

    title    = data.get("Title",      "N/A")
    year     = data.get("Year",       "N/A")
    rating   = data.get("imdbRating", "N/A")
    genre    = data.get("Genre",      "N/A")
    runtime  = data.get("Runtime",    "N/A")
    director = data.get("Director",   "N/A")
    actors   = data.get("Actors",     "N/A")
    plot     = data.get("Plot",       "N/A")
    language = data.get("Language",   "N/A")
    poster   = data.get("Poster",     "N/A")
    votes    = data.get("imdbVotes",  "N/A")

    if poster == "N/A" or not poster:
        poster = "https://i.imgur.com/8qH7Z8L.jpeg"

    try:
        star_bar = "⭐" * int(float(rating)) + "☆" * (10 - int(float(rating)))
    except:
        star_bar = "N/A"

    search = title.replace(" ", "+")

    # ── Current active servers use karo ──
    urls  = [bot_servers[f"s{i}"]["url"] + search for i in range(1, 6)]
    names = [bot_servers[f"s{i}"]["name"]          for i in range(1, 6)]
    trailer = f"https://www.youtube.com/results?search_query={search}+trailer"

    caption = (
        f"🎬 *{title}* `({year})`\n\n"
        f"{star_bar}\n"
        f"⭐ *IMDb:* `{rating}/10`  •  🗳 *Votes:* `{votes}`\n\n"
        f"🎭 *Genre:* `{genre}`\n"
        f"⏱ *Runtime:* `{runtime}`\n"
        f"🌍 *Language:* `{language}`\n"
        f"🎥 *Director:* `{director}`\n"
        f"🎭 *Cast:* `{actors}`\n\n"
        f"📖 *Plot:*\n_{plot}_\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *Fast servers available below*\n"
        f"🦁 *Use Brave Browser for No Ads*"
    )

    sent = await update.message.reply_photo(
        photo=poster,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Watch Trailer", url=trailer)],
            [InlineKeyboardButton(f"⬇️ Fast Download — {names[0]}", url=urls[0])],
            [InlineKeyboardButton("🌐 More Servers", callback_data="servers_tmp")]
        ])
    )

    msg_id = str(sent.message_id)
    context.user_data[msg_id] = {
        "servers": urls,
        "names":   names,
        "trailer": trailer,
        "title":   title
    }

    await sent.edit_reply_markup(reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Watch Trailer", url=trailer)],
        [InlineKeyboardButton(f"⬇️ Fast Download — {names[0]}", url=urls[0])],
        [InlineKeyboardButton("🌐 More Servers", callback_data=f"servers_{msg_id}")]
    ]))


# ═══════════════════════════════════════
#           MORE SERVERS
# ═══════════════════════════════════════
async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🌐 Loading servers...")

    msg_id     = query.data.split("_", 1)[1]
    movie_data = context.user_data.get(msg_id)

    if not movie_data:
        await query.message.reply_text("⚠️ Session expired. Search the movie again.")
        return

    loader = await query.message.reply_text(SERVER_FRAMES[0])
    for frame in SERVER_FRAMES[1:]:
        await asyncio.sleep(0.7)
        await loader.edit_text(frame)
    await asyncio.sleep(0.4)
    await loader.delete()

    urls   = movie_data["servers"]
    names  = movie_data["names"]
    title  = movie_data["title"]
    medals = ["🥇", "🥈", "🥉", "🏅", "🎖"]

    keyboard = [[InlineKeyboardButton(f"{medals[i]} {names[i]}", url=urls[i])] for i in range(5)]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_{msg_id}")])

    await query.message.reply_text(
        f"🌐 *Download Servers for:*\n🎬 _{title}_\n\n"
        "Pick any server 👇\n"
        "🦁 *Brave Browser = No Ads*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ═══════════════════════════════════════
#               BACK
# ═══════════════════════════════════════
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Going back...")

    msg_id     = query.data.split("_", 1)[1]
    movie_data = context.user_data.get(msg_id)

    if not movie_data:
        await query.message.reply_text("⚠️ Session expired. Search the movie again.")
        return

    loader = await query.message.reply_text(BACK_FRAMES[0])
    for frame in BACK_FRAMES[1:]:
        await asyncio.sleep(0.7)
        await loader.edit_text(frame)
    await asyncio.sleep(0.4)
    await loader.delete()

    await query.message.reply_text(
        f"🎬 *Back to:* _{movie_data['title']}_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Watch Trailer", url=movie_data["trailer"])],
            [InlineKeyboardButton(f"⬇️ Fast Download — {movie_data['names'][0]}", url=movie_data["servers"][0])],
            [InlineKeyboardButton("🌐 More Servers", callback_data=f"servers_{msg_id}")]
        ])
    )


# ═══════════════════════════════════════
#             BOT START
# ═══════════════════════════════════════
app = ApplicationBuilder().token(TOKEN).build()

admin_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_edit, pattern="^admin_edit_")],
    states={
        WAITING_URL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_url)],
        WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_name)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(admin_conv)
app.add_handler(CallbackQueryHandler(admin_reset, pattern="^admin_reset$"))
app.add_handler(CallbackQueryHandler(servers,     pattern="^servers_"))
app.add_handler(CallbackQueryHandler(back,        pattern="^back_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie))

print("✅ CineBot Running...")
app.run_polling()
