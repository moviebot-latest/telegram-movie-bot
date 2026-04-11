# ============================================================
#   🤖 ADVANCED EXPIRED BOT — @ALLH4CKERGODS_BOT
#   pip install pyTelegramBotAPI rich
# ============================================================

import os
import telebot
import time
import threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

# ─── CONFIG (Render Environment Variable se) ───────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
NEW_BOT   = "@ALLH4CKERGODS_BOT"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable nahi mila! Render me set karo.")
# ───────────────────────────────────────────────────────────

console = Console()
client  = telebot.TeleBot(BOT_TOKEN)
stats   = {"total": 0, "start": 0, "other": 0, "users": set()}

EXPIRED_MSG = f"""⚠️ *This bot is expired\\!*

🚫 Yeh bot band ho gaya hai\\.

✅ *Naya active bot:*
👉 {NEW_BOT}

_Yeh bot active hai — ise use karo\\!_ 🙏"""

# ─── ANIMATED TERMINAL BANNER ──────────────────────────────
def show_banner():
    console.clear()
    banner = Text()
    banner.append("\n  ██████╗  ██████╗ ████████╗\n", style="bold red")
    banner.append("  ██╔══██╗██╔═══██╗╚══██╔══╝\n", style="bold yellow")
    banner.append("  ██████╔╝██║   ██║   ██║   \n", style="bold green")
    banner.append("  ██╔══██╗██║   ██║   ██║   \n", style="bold cyan")
    banner.append("  ██████╔╝╚██████╔╝   ██║   \n", style="bold magenta")
    banner.append("  ╚═════╝  ╚═════╝    ╚═╝   \n", style="bold blue")
    console.print(banner, justify="center")
    console.print(
        Panel.fit(
            f"[bold red]⛔ EXPIRED BOT[/] [white]→[/] [bold green]{NEW_BOT}[/]",
            border_style="red",
            padding=(0, 4),
        ),
        justify="center"
    )

# ─── LIVE STATS DISPLAY ────────────────────────────────────
def live_stats():
    with Live(refresh_per_second=2, console=console) as live:
        while True:
            table = Table(
                box=box.ROUNDED,
                border_style="bright_black",
                show_header=True,
                header_style="bold cyan",
                title="[bold red]📊 BOT STATS[/]",
                expand=False,
            )
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value",  style="bold yellow")

            uptime = int(time.time() - start_time)
            h, m, s = uptime//3600, (uptime%3600)//60, uptime%60

            table.add_row("🕐 Uptime",        f"{h:02d}:{m:02d}:{s:02d}")
            table.add_row("📨 Total Messages", str(stats["total"]))
            table.add_row("🚀 /start Calls",   str(stats["start"]))
            table.add_row("💬 Other Messages", str(stats["other"]))
            table.add_row("👤 Unique Users",   str(len(stats["users"])))
            table.add_row("🕓 Last Update",    datetime.now().strftime("%H:%M:%S"))

            live.update(Panel(table, border_style="red", padding=(0, 2)))
            time.sleep(0.5)

# ─── ANIMATED SPINNER ON STARTUP ───────────────────────────
def startup_animation():
    steps = [
        "🔌 Connecting to Telegram...",
        "🔐 Authenticating token...",
        "📡 Starting polling engine...",
        "🤖 AI handler loading...",
        "✅ Bot is LIVE!",
    ]
    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold red"),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=len(steps))
        for step in steps:
            progress.update(task, description=step, advance=1)
            time.sleep(0.6)

# ─── LOG HELPER ────────────────────────────────────────────
def log(user, cmd, uid):
    now = datetime.now().strftime("%H:%M:%S")
    console.print(
        f"[dim]{now}[/]  "
        f"[bold red]{cmd:<12}[/]  "
        f"[cyan]{user:<20}[/]  "
        f"[dim white]id={uid}[/]"
    )

# ─── HANDLERS ──────────────────────────────────────────────
@client.message_handler(commands=['start'])
def handle_start(msg):
    stats["total"] += 1
    stats["start"] += 1
    stats["users"].add(msg.from_user.id)
    log(msg.from_user.first_name or "User", "/start", msg.from_user.id)
    client.send_message(msg.chat.id, EXPIRED_MSG, parse_mode='MarkdownV2')


@client.message_handler(func=lambda m: True)
def handle_any(msg):
    stats["total"] += 1
    stats["other"] += 1
    stats["users"].add(msg.from_user.id)
    log(msg.from_user.first_name or "User", "message", msg.from_user.id)
    client.send_message(msg.chat.id, EXPIRED_MSG, parse_mode='MarkdownV2')

# ─── MAIN ──────────────────────────────────────────────────
if __name__ == "__main__":
    start_time = time.time()
    show_banner()
    time.sleep(0.5)
    startup_animation()

    console.print("\n[bold green]  ✅ Bot is running![/]  Press [red]Ctrl+C[/] to stop.\n")
    console.print(f"  [dim]All users redirect →[/] [bold cyan]{NEW_BOT}[/]\n")
    console.print("  [bold dim]──────────────────────────────────────────[/]")
    console.print("  [bold dim]  TIME       COMMAND       USER             ID[/]")
    console.print("  [bold dim]──────────────────────────────────────────[/]\n")

    threading.Thread(target=live_stats, daemon=True).start()

    try:
        client.infinity_polling(timeout=10, long_polling_timeout=5)
    except KeyboardInterrupt:
        console.print("\n[bold red]  ⛔ Bot stopped.[/]\n")
