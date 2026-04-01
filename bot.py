from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

import re
import threading
import asyncio
import time
import random
from flask import Flask

from config import TOKEN, ADMIN_ID
from movie_api import search_movie
from servers import get_servers


# ══════════════════════════════════════════════════════════════════
#  FLASK KEEP-ALIVE
# ══════════════════════════════════════════════════════════════════
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "🎬 CineBot Ultra — Running"

threading.Thread(target=lambda: web_app.run(host="0.0.0.0", port=10000), daemon=True).start()


# ══════════════════════════════════════════════════════════════════
#  GLOBAL STATE
# ══════════════════════════════════════════════════════════════════
chat_ids   = set()
maintenance = False

# Per-user search history (last 5)
user_history: dict[int, list[dict]] = {}

# Per-user watchlist
user_watchlist: dict[int, list[dict]] = {}

# Search stats
search_count = 0
popular_searches: dict[str, int] = {}


# ══════════════════════════════════════════════════════════════════
#  ANIMATION FRAMES
# ══════════════════════════════════════════════════════════════════

# Cinema-themed spinners
FILM_REEL    = ["🎞","🎬","🎥","📽","🎞","🎬"]
RADAR_SPIN   = ["◜ ","◝ ","◞ ","◟ "]
MATRIX_CHARS = "ﾊﾋｼｦｲｸｺｻﾀﾔｹﾦｿﾞﾌﾔｪｷ"
BOUNCE       = ["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]
PULSE        = ["█","▓","▒","░","▒","▓"]
SIGNAL       = ["▁","▂","▃","▄","▅","▆","▇","█","▇","▆","▅","▄","▃","▂"]
CLOCK        = ["🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚","🕛"]
ORBIT        = ["◴","◷","◶","◵"]
SCAN_LINES   = ["▔▔▔▔▔▔▔▔","════════","▁▁▁▁▁▁▁▁","════════"]
DNA          = ["∿∿∿∿","≈≈≈≈","〰〰〰〰","≈≈≈≈"]
STARS        = ["✦","✧","★","☆","✦","✧"]
ZAP          = ["⚡","🌩","⚡","💥","⚡","🌩"]
EYE_SCAN     = ["👁 ·····","👁·····","·👁····","··👁···","···👁··","····👁·","·····👁","····👁·","···👁··","··👁···","·👁····","👁·····"]


# ══════════════════════════════════════════════════════════════════
#  ANIMATION ENGINE
# ══════════════════════════════════════════════════════════════════

async def _safe_edit(msg, text: str) -> None:
    try:
        await msg.edit_text(text)
    except Exception:
        pass

async def _safe_edit_caption(msg, text: str, markup=None) -> None:
    try:
        await msg.edit_caption(caption=text, reply_markup=markup)
    except Exception:
        pass


async def cinema_boot_animation(update: Update) -> object:
    """Full cinematic boot sequence — 3 phases."""
    msg = await update.message.reply_text("🎬")

    # Phase 1 — Power on
    boot_frames = [
        "```\n[          ] 0%\n  CINEBOT ONLINE...\n```",
        "```\n[██        ] 20%\n  LOADING MODULES...\n```",
        "```\n[████      ] 40%\n  CONNECTING API...\n```",
        "```\n[██████    ] 60%\n  SCANNING DATABASE...\n```",
        "```\n[████████  ] 80%\n  DECRYPTING VAULT...\n```",
        "```\n[██████████] 100%\n  SYSTEM READY ✓\n```",
    ]
    for frame in boot_frames:
        await _safe_edit(msg, frame)
        await asyncio.sleep(0.3)

    # Phase 2 — Matrix rain effect
    chars = list(MATRIX_CHARS)
    for i in range(6):
        line1 = "".join(random.choices(chars, k=12))
        line2 = "".join(random.choices(chars, k=12))
        line3 = "".join(random.choices(chars, k=12))
        await _safe_edit(msg,
            f"```\n{line1}\n{line2}\n{line3}\n```\n"
            f"  🟢 `MATRIX SYNC...`"
        )
        await asyncio.sleep(0.2)

    # Phase 3 — Lock on target
    eye_frames = EYE_SCAN[:6]
    for frame in eye_frames:
        await _safe_edit(msg,
            f"🎯 **TARGETING MOVIE DATABASE**\n"
            f"  `{frame}`\n"
            f"  _Lock acquired..._"
        )
        await asyncio.sleep(0.2)

    return msg


async def hacker_search_animation(msg) -> None:
    """Advanced multi-phase search animation."""

    # Phase 1 — Signal scan
    for i, frame in enumerate(SIGNAL):
        bar = "".join(SIGNAL[max(0,j-2):j+1] + SIGNAL[j+1:i+1] for j in range(i+1))
        await _safe_edit(msg,
            f"📡 **SIGNAL ACQUIRED**\n"
            f"  `{frame * 3}` scanning…\n"
            f"  `{BOUNCE[i % len(BOUNCE)]}` indexing nodes"
        )
        await asyncio.sleep(0.15)

    # Phase 2 — Database query animation
    db_frames = [
        ("🗄", "CONNECTING TO DB",    "▱▱▱▱▱▱▱▱"),
        ("🗄", "AUTH HANDSHAKE",      "▰▱▱▱▱▱▱▱"),
        ("🗄", "QUERY DISPATCH",      "▰▰▱▱▱▱▱▱"),
        ("🔍", "SCANNING TITLES",     "▰▰▰▱▱▱▱▱"),
        ("🔍", "MATCHING PATTERNS",   "▰▰▰▰▱▱▱▱"),
        ("🎞", "FETCHING METADATA",   "▰▰▰▰▰▱▱▱"),
        ("🎞", "LOADING RATINGS",     "▰▰▰▰▰▰▱▱"),
        ("🎬", "PULLING POSTERS",     "▰▰▰▰▰▰▰▱"),
        ("🏆", "COMPILING RESULTS",   "▰▰▰▰▰▰▰▰"),
    ]
    for icon, label, bar in db_frames:
        spin = BOUNCE[hash(label) % len(BOUNCE)]
        await _safe_edit(msg,
            f"{spin} **{icon} {label}**\n"
            f"  `{bar}`\n"
            f"  _{random.choice(['Decrypting...','Parsing...','Indexing...','Verifying...'])}_"
        )
        await asyncio.sleep(0.22)

    # Phase 3 — Radar lock
    for i, frame in enumerate(EYE_SCAN[:8]):
        await _safe_edit(msg,
            f"🎯 **LOCK ON TARGET**\n"
            f"  `{frame}`\n"
            f"  `{ORBIT[i % len(ORBIT)]}` triangulating…"
        )
        await asyncio.sleep(0.18)

    # Phase 4 — Final decode
    for i in range(5):
        chars = list(MATRIX_CHARS)
        noise = "".join(random.choices(chars, k=10))
        await _safe_edit(msg,
            f"💾 **DECODING PAYLOAD**\n"
            f"  `{noise}`\n"
            f"  `{PULSE[i % len(PULSE)] * 8}` decrypting"
        )
        await asyncio.sleep(0.15)


async def not_found_animation(msg) -> None:
    """Dramatic 'not found' sequence."""
    frames = [
        "🔴 **ERROR 404**\n  `scanning...`",
        "🔴 **ERROR 404**\n  `no signal...`",
        "📡 **SIGNAL LOST**\n  `◌◌◌◌◌◌◌◌`",
        "📡 **SIGNAL LOST**\n  `●◌◌◌◌◌◌◌`",
        "📡 **SIGNAL LOST**\n  `●●◌◌◌◌◌◌`",
        "❌ **DATABASE MISS**\n  `retrying...`",
        "❌ **DATABASE MISS**\n  `all nodes checked`",
        "💀 **NOT FOUND**\n  `target eliminated`",
    ]
    for frame in frames:
        await _safe_edit(msg, frame)
        await asyncio.sleep(0.25)


async def maintenance_animation(msg) -> None:
    """Server maintenance dramatic display."""
    frames = [
        f"🔧 **MAINTENANCE MODE**\n  `{SIGNAL[i % len(SIGNAL)] * 6}`\n  _System offline_"
        for i in range(8)
    ]
    for frame in frames:
        await _safe_edit(msg, frame)
        await asyncio.sleep(0.2)


# ══════════════════════════════════════════════════════════════════
#  RATING VISUAL
# ══════════════════════════════════════════════════════════════════

def _rating_stars(rating_str: str) -> str:
    try:
        r = float(rating_str)
        filled = int(r / 2)
        half   = 1 if (r / 2 - filled) >= 0.5 else 0
        empty  = 5 - filled - half
        return "★" * filled + ("½" if half else "") + "☆" * empty + f"  `{r}/10`"
    except Exception:
        return f"`{rating_str}/10`"

def _rating_bar(rating_str: str) -> str:
    try:
        r   = float(rating_str)
        pct = r / 10
        n   = int(pct * 16)
        bar = "▰" * n + "▱" * (16 - n)
        color = "🟢" if r >= 7 else ("🟡" if r >= 5 else "🔴")
        return f"{color} `{bar}`"
    except Exception:
        return ""

def _runtime_bar(runtime_str: str) -> str:
    try:
        mins = int(runtime_str.replace(" min","").strip())
        pct  = min(mins / 180, 1.0)
        n    = int(pct * 12)
        bar  = "▰" * n + "▱" * (12 - n)
        return f"`{bar}` `{runtime_str}`"
    except Exception:
        return f"`{runtime_str}`"

def _genre_badges(genre_str: str) -> str:
    genre_icons = {
        "Action":    "💥", "Adventure": "🗺", "Animation": "🎨",
        "Comedy":    "😂", "Crime":     "🔫", "Documentary":"📹",
        "Drama":     "🎭", "Fantasy":   "🧙", "Horror":    "👻",
        "Mystery":   "🔍", "Romance":   "💕", "Sci-Fi":    "🚀",
        "Thriller":  "😱", "War":       "⚔️", "Western":   "🤠",
        "Biography": "📖", "History":   "🏛", "Music":     "🎵",
        "Sport":     "🏆", "Family":    "👨‍👩‍👧",
    }
    genres = [g.strip() for g in genre_str.split(",")]
    return " · ".join(
        f"{genre_icons.get(g, '🎬')} {g}" for g in genres[:4]
    )


# ══════════════════════════════════════════════════════════════════
#  HISTORY TRACKING
# ══════════════════════════════════════════════════════════════════

def _add_history(uid: int, movie_data: dict) -> None:
    if uid not in user_history:
        user_history[uid] = []
    entry = {
        "title": movie_data.get("Title","?"),
        "year":  movie_data.get("Year","?"),
        "rating": movie_data.get("imdbRating","?"),
    }
    # Remove duplicate
    user_history[uid] = [h for h in user_history[uid] if h["title"] != entry["title"]]
    user_history[uid].insert(0, entry)
    user_history[uid] = user_history[uid][:5]

def _add_to_popular(title: str) -> None:
    global popular_searches
    key = title.lower()
    popular_searches[key] = popular_searches.get(key, 0) + 1


# ══════════════════════════════════════════════════════════════════
#  /start — Cinematic welcome
# ══════════════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)
    uid  = update.effective_user.id
    name = update.effective_user.first_name or "User"

    msg = await update.message.reply_text("🎬")

    # Boot sequence
    for i, frame in enumerate(["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]):
        await _safe_edit(msg,
            f"{frame} **CINEBOT ULTRA** — booting…\n"
            f"  `{'█' * i}{'░' * (8-i)}` {i*12}%"
        )
        await asyncio.sleep(0.18)

    # Matrix flash
    for _ in range(4):
        chars = list(MATRIX_CHARS)
        line = "".join(random.choices(chars, k=16))
        await _safe_edit(msg, f"```\n{line}\nINITIALIZING...\n```")
        await asyncio.sleep(0.15)

    history_txt = ""
    if uid in user_history and user_history[uid]:
        recent = user_history[uid][0]
        history_txt = f"\n🔁 Last search: **{recent['title']}** ({recent['year']})\n"

    await _safe_edit(msg,
        f"╔══════════════════════════╗\n"
        f"║  🎬  CINEBOT  ULTRA  🎬  ║\n"
        f"╚══════════════════════════╝\n\n"
        f"👋 Welcome, **{name}**!\n"
        f"{history_txt}\n"
        f"📽 **Just type any movie name:**\n"
        f"  • `RRR`\n"
        f"  • `Avatar 2009`\n"
        f"  • `The Dark Knight`\n\n"
        f"🛠 **Commands:**\n"
        f"  • `/history` — your recent searches\n"
        f"  • `/watchlist` — saved movies\n"
        f"  • `/popular` — trending searches\n"
        f"  • `/stats` — bot statistics\n\n"
        f"──────────────────────────\n"
        f"  🔴 Live · 🟢 Fast · 💾 Smart\n"
        f"  _CineBot Ultra v3 — Ready_"
    )


# ══════════════════════════════════════════════════════════════════
#  MAIN MOVIE SEARCH
# ══════════════════════════════════════════════════════════════════
async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global maintenance, search_count

    chat_ids.add(update.effective_chat.id)
    uid = update.effective_user.id

    if maintenance:
        msg = await update.message.reply_text("🔧")
        await maintenance_animation(msg)
        await _safe_edit(msg,
            f"🔧 **SERVER MAINTENANCE**\n"
            f"══════════════════════════\n"
            f"  ⚠️ System temporarily offline\n"
            f"  🔄 Please try again later\n"
            f"══════════════════════════\n"
            f"  _Auto-restore in progress…_"
        )
        return

    text = update.message.text.strip()

    if not re.search("[a-zA-Z]", text):
        await update.message.reply_text(
            "⚠️ **Invalid input**\n"
            "  Please send a valid movie name.\n"
            "  Example: `Avatar` or `RRR 2022`"
        )
        return

    # Start cinematic animation
    loading = await update.message.reply_text(f"{FILM_REEL[0]} **Initializing…**")
    await hacker_search_animation(loading)

    # Parse title + year
    parts = text.split()
    year  = None
    title = text
    if parts[-1].isdigit() and len(parts[-1]) == 4:
        year  = parts[-1]
        title = " ".join(parts[:-1])

    # Fetch data
    await _safe_edit(loading,
        f"🌐 **FETCHING FROM OMDB**\n"
        f"  `{'▰' * 12}` querying…"
    )
    data = search_movie(title, year)

    if not data or data.get("Response") != "True":
        await not_found_animation(loading)
        await _safe_edit(loading,
            f"❌ **MOVIE NOT FOUND**\n"
            f"══════════════════════════\n"
            f"  🔍 Query: `{text}`\n"
            f"  📡 Database: no match\n"
            f"══════════════════════════\n"
            f"  💡 Try:\n"
            f"  • Full title: `The Dark Knight`\n"
            f"  • Add year: `Avatar 2009`\n"
            f"  • Check spelling"
        )
        return

    # Track stats
    search_count += 1
    _add_history(uid, data)
    _add_to_popular(data["Title"])

    # Extract fields
    m_title   = data.get("Title","?")
    m_year    = data.get("Year","?")
    m_rating  = data.get("imdbRating","N/A")
    m_genre   = data.get("Genre","?")
    m_runtime = data.get("Runtime","?")
    m_plot    = data.get("Plot","?")
    m_director= data.get("Director","?")
    m_actors  = data.get("Actors","?")
    m_lang    = data.get("Language","?")
    m_country = data.get("Country","?")
    m_awards  = data.get("Awards","N/A")
    m_box     = data.get("BoxOffice","N/A")
    m_poster  = data.get("Poster","")
    m_votes   = data.get("imdbVotes","?")
    m_rated   = data.get("Rated","?")

    servers = get_servers(m_title)
    trailer = f"https://www.youtube.com/results?search_query={m_title.replace(' ','+')}"

    # Save to user_data
    context.user_data["servers"]  = servers
    context.user_data["trailer"]  = trailer
    context.user_data["movie"]    = data
    context.user_data["watching"] = False

    # Build rich caption
    stars      = _rating_stars(m_rating)
    rating_bar = _rating_bar(m_rating)
    runtime_bar= _runtime_bar(m_runtime)
    genre_badges = _genre_badges(m_genre)

    # Truncate plot
    plot_short = m_plot[:120] + "…" if len(m_plot) > 120 else m_plot

    caption = (
        f"🎬 **{m_title}** `({m_year})`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ **IMDb** {stars}\n"
        f"   {rating_bar}\n"
        f"🗳 **Votes** `{m_votes}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎭 {genre_badges}\n"
        f"⏱ **Runtime** {runtime_bar}\n"
        f"🔞 **Rated** `{m_rated}`\n"
        f"🌍 **Language** `{m_lang}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎥 **Director** `{m_director}`\n"
        f"👥 **Cast** `{m_actors[:60]}…`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 _{plot_short}_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 `{m_awards[:50]}`\n"
        f"💰 **Box Office** `{m_box}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ Use **Brave Browser** for no ads\n"
        f"📢 @Latestmovies4Ux"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎬 Trailer", url=trailer),
            InlineKeyboardButton("⬇️ Server 1", url=servers[0]),
        ],
        [
            InlineKeyboardButton("🌐 More Servers", callback_data="servers"),
            InlineKeyboardButton("💾 Watchlist", callback_data="watchlist_add"),
        ],
        [
            InlineKeyboardButton("📊 Full Details", callback_data="full_details"),
            InlineKeyboardButton("🔄 Similar", callback_data="similar"),
        ],
    ]

    await loading.delete()

    if m_poster and m_poster != "N/A":
        await update.message.reply_photo(
            photo=m_poster,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ══════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    uid   = update.effective_user.id

    # ── More Servers
    if data == "servers":
        s = context.user_data.get("servers", [])
        if not s or len(s) < 6:
            await query.answer("⚠️ No more servers", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton(f"🖥 Server {i+2}", url=s[i+1])]
            for i in range(min(5, len(s)-1))
        ]
        keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="back_main")])
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ── Back to main keyboard
    elif data == "back_main":
        s       = context.user_data.get("servers", [])
        trailer = context.user_data.get("trailer", "")
        keyboard = [
            [
                InlineKeyboardButton("🎬 Trailer", url=trailer),
                InlineKeyboardButton("⬇️ Server 1", url=s[0] if s else "#"),
            ],
            [
                InlineKeyboardButton("🌐 More Servers", callback_data="servers"),
                InlineKeyboardButton("💾 Watchlist", callback_data="watchlist_add"),
            ],
            [
                InlineKeyboardButton("📊 Full Details", callback_data="full_details"),
                InlineKeyboardButton("🔄 Similar", callback_data="similar"),
            ],
        ]
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ── Add to Watchlist
    elif data == "watchlist_add":
        movie_data = context.user_data.get("movie", {})
        if not movie_data:
            await query.answer("⚠️ No movie data", show_alert=True)
            return
        if uid not in user_watchlist:
            user_watchlist[uid] = []
        entry = {
            "title":  movie_data.get("Title","?"),
            "year":   movie_data.get("Year","?"),
            "rating": movie_data.get("imdbRating","?"),
        }
        titles = [w["title"] for w in user_watchlist[uid]]
        if entry["title"] in titles:
            await query.answer("✅ Already in watchlist!", show_alert=True)
        else:
            user_watchlist[uid].append(entry)
            await query.answer(f"💾 Added: {entry['title']}", show_alert=True)

    # ── Full Details
    elif data == "full_details":
        movie_data = context.user_data.get("movie", {})
        if not movie_data:
            await query.answer("No data", show_alert=True)
            return

        rts   = movie_data.get("Ratings", [])
        rt_txt = ""
        for r in rts:
            source = r.get("Source","?")
            val    = r.get("Value","?")
            icon   = "🍅" if "Rotten" in source else ("🎬" if "Metacritic" in source else "⭐")
            rt_txt += f"  {icon} **{source}**: `{val}`\n"

        full = (
            f"📋 **FULL DETAILS**\n"
            f"══════════════════════════\n"
            f"🎬 **{movie_data.get('Title')}** ({movie_data.get('Year')})\n"
            f"──────────────────────────\n"
            f"📝 **Plot:**\n  _{movie_data.get('Plot','N/A')}_\n"
            f"──────────────────────────\n"
            f"🎥 **Director:** `{movie_data.get('Director','N/A')}`\n"
            f"✍️ **Writer:** `{movie_data.get('Writer','N/A')[:60]}`\n"
            f"👥 **Cast:** `{movie_data.get('Actors','N/A')}`\n"
            f"──────────────────────────\n"
            f"🌍 **Country:** `{movie_data.get('Country','N/A')}`\n"
            f"🗣 **Language:** `{movie_data.get('Language','N/A')}`\n"
            f"🔞 **Rated:** `{movie_data.get('Rated','N/A')}`\n"
            f"📅 **Released:** `{movie_data.get('Released','N/A')}`\n"
            f"──────────────────────────\n"
            f"📊 **All Ratings:**\n{rt_txt}"
            f"🗳 **IMDb Votes:** `{movie_data.get('imdbVotes','N/A')}`\n"
            f"🏆 **Awards:** `{movie_data.get('Awards','N/A')}`\n"
            f"💰 **Box Office:** `{movie_data.get('BoxOffice','N/A')}`\n"
            f"══════════════════════════"
        )
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="back_main")]]
        try:
            await query.edit_message_caption(
                caption=full,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            await query.message.reply_text(full, reply_markup=InlineKeyboardMarkup(keyboard))

    # ── Similar movies suggestion
    elif data == "similar":
        movie_data = context.user_data.get("movie", {})
        genre = movie_data.get("Genre","").split(",")[0].strip() if movie_data else ""
        title = movie_data.get("Title","") if movie_data else ""
        trailer = f"https://www.youtube.com/results?search_query=movies+like+{title.replace(' ','+')}"
        keyboard = [
            [InlineKeyboardButton(f"🎬 Movies like {title[:20]}…", url=trailer)],
            [InlineKeyboardButton("◀️ Back", callback_data="back_main")],
        ]
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ══════════════════════════════════════════════════════════════════
#  /history
# ══════════════════════════════════════════════════════════════════
async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    h   = user_history.get(uid, [])
    if not h:
        await update.message.reply_text(
            "📭 **No search history yet.**\n"
            "  Search for a movie to start!"
        )
        return

    lines = ""
    for i, entry in enumerate(h, 1):
        stars = "⭐" * min(int(float(entry['rating'])) // 2, 5) if entry['rating'] != 'N/A' else ""
        lines += f"  {i}. **{entry['title']}** `({entry['year']})` {stars}\n"

    await update.message.reply_text(
        f"🕘 **YOUR SEARCH HISTORY**\n"
        f"══════════════════════════\n"
        f"{lines}"
        f"══════════════════════════\n"
        f"  _Last {len(h)} searches_"
    )


# ══════════════════════════════════════════════════════════════════
#  /watchlist
# ══════════════════════════════════════════════════════════════════
async def watchlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    wl  = user_watchlist.get(uid, [])
    if not wl:
        await update.message.reply_text(
            "📋 **Watchlist is empty.**\n"
            "  Search a movie and tap 💾 to save!"
        )
        return

    lines = ""
    for i, entry in enumerate(wl, 1):
        lines += f"  {i}. **{entry['title']}** `({entry['year']})` ⭐`{entry['rating']}`\n"

    await update.message.reply_text(
        f"💾 **YOUR WATCHLIST**\n"
        f"══════════════════════════\n"
        f"{lines}"
        f"══════════════════════════\n"
        f"  {len(wl)} movie(s) saved"
    )


# ══════════════════════════════════════════════════════════════════
#  /popular
# ══════════════════════════════════════════════════════════════════
async def popular_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not popular_searches:
        await update.message.reply_text("📊 No data yet — search some movies!")
        return

    top = sorted(popular_searches.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ""
    medals = ["🥇","🥈","🥉"] + ["🏅"] * 7
    for i, (title, count) in enumerate(top):
        lines += f"  {medals[i]} **{title.title()}** — `{count}x`\n"

    await update.message.reply_text(
        f"🔥 **TRENDING SEARCHES**\n"
        f"══════════════════════════\n"
        f"{lines}"
        f"══════════════════════════\n"
        f"  _Top {len(top)} searches_"
    )


# ══════════════════════════════════════════════════════════════════
#  /stats
# ══════════════════════════════════════════════════════════════════
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid       = update.effective_user.id
    my_count  = len(user_history.get(uid, []))
    wl_count  = len(user_watchlist.get(uid, []))
    top_movie = max(popular_searches, key=popular_searches.get) if popular_searches else "N/A"

    await update.message.reply_text(
        f"📊 **BOT STATISTICS**\n"
        f"══════════════════════════\n"
        f"  🌐 **Total Users** : `{len(chat_ids)}`\n"
        f"  🔍 **Total Searches** : `{search_count}`\n"
        f"  🔥 **Most Searched** : `{top_movie.title()}`\n"
        f"──────────────────────────\n"
        f"  👤 **Your Searches** : `{my_count}`\n"
        f"  💾 **Your Watchlist** : `{wl_count}`\n"
        f"══════════════════════════\n"
        f"  _CineBot Ultra v3_"
    )


# ══════════════════════════════════════════════════════════════════
#  ADMIN — Maintenance
# ══════════════════════════════════════════════════════════════════
async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global maintenance
    if update.message.from_user.id != ADMIN_ID: return
    maintenance = True
    await update.message.reply_text("🔧 **Maintenance ON** — notifying users…")
    for chat in chat_ids:
        try:
            await context.bot.send_message(
                chat,
                "🔧 **SERVER MAINTENANCE**\n"
                "══════════════════════════\n"
                "  ⚠️ Temporarily offline\n"
                "  🔄 Back soon!\n"
                "══════════════════════════"
            )
        except Exception:
            pass

async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global maintenance
    if update.message.from_user.id != ADMIN_ID: return
    maintenance = False
    await update.message.reply_text("✅ **Maintenance OFF** — notifying users…")
    for chat in chat_ids:
        try:
            await context.bot.send_message(
                chat,
                "✅ **SERVER ONLINE**\n"
                "══════════════════════════\n"
                "  🟢 All systems operational\n"
                "  🎬 Search your movie now!\n"
                "══════════════════════════"
            )
        except Exception:
            pass

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin broadcast: /broadcast Your message here"""
    if update.message.from_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    sent = failed = 0
    for chat in chat_ids:
        try:
            await context.bot.send_message(chat,
                f"📢 **ANNOUNCEMENT**\n"
                f"══════════════════════════\n"
                f"{msg}\n"
                f"══════════════════════════\n"
                f"  _— CineBot Admin_"
            )
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"📢 **Broadcast complete**\n"
        f"  ✅ Sent: `{sent}`\n"
        f"  ❌ Failed: `{failed}`"
    )


# ══════════════════════════════════════════════════════════════════
#  BUILD & RUN
# ══════════════════════════════════════════════════════════════════
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",           start))
app.add_handler(CommandHandler("history",         history_cmd))
app.add_handler(CommandHandler("watchlist",       watchlist_cmd))
app.add_handler(CommandHandler("popular",         popular_cmd))
app.add_handler(CommandHandler("stats",           stats_cmd))
app.add_handler(CommandHandler("broadcast",       broadcast))
app.add_handler(CommandHandler("maintenance_on",  maintenance_on))
app.add_handler(CommandHandler("maintenance_off", maintenance_off))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie))
app.add_handler(CallbackQueryHandler(callback_handler))

print("🎬 CineBot Ultra v3 — Running...")
app.run_polling()
