import asyncio
import json
import os
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.error import TelegramError

import config
from monitor import extract_links, fetch_page, link_hash

SEEN_FILE = "seen_links.json"


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)


async def check_bandi(bot: Bot, chat_id: int):
    seen = load_seen()
    new_found = False

    for source in config.SOURCES:
        html = fetch_page(source["url"])
        if html is None:
            print(f"[{datetime.now()}] Errore: {source['name']} non raggiungibile")
            continue

        links = extract_links(html, source["url"])
        for link in links:
            h = link_hash(link)
            if h in seen:
                continue

            seen.add(h)
            new_found = True

            message = (
                f"📢 <b>Nuovo bando trovato!</b>\n\n"
                f"🏥 <b>{source['name']}</b>\n"
                f"📄 {link['title']}\n"
                f"🔗 {link['url']}\n\n"
                f"<i>Rilevato {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>"
            )

            try:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            except TelegramError as e:
                print(f"Errore invio messaggio: {e}")

    save_seen(seen)
    if not new_found:
        print(f"[{datetime.now()}] Nessun nuovo bando")


async def start(bot: Bot, chat_id: int):
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "👋 <b>Bot Bandi Psicologi Varese</b>\n\n"
            "Monitoro automaticamente le pagine dei bandi di:\n"
            "• ASST Sette Laghi\n"
            "• ASST Valle Olona\n"
            "• ATS Insubria\n"
            "• Regione Lombardia\n"
            "• Ordine Psicologi Lombardia\n\n"
            "Ti avviserò appena trovo un nuovo bando per psicologi. "
            "Sto già al lavoro! 🔍"
        ),
        parse_mode="HTML",
    )


async def main():
    bot = Bot(token=config.BOT_TOKEN)

    try:
        await start(bot, config.ADMIN_CHAT_ID)
    except TelegramError as e:
        print(f"Impossibile inviare il messaggio di benvenuto: {e}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_bandi,
        "interval",
        minutes=config.CHECK_INTERVAL_MINUTES,
        args=[bot, config.ADMIN_CHAT_ID],
    )
    scheduler.start()

    print(f"Bot avviato. Controllo ogni {config.CHECK_INTERVAL_MINUTES} minuti.")
    print("Premi Ctrl+C per fermare.")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())