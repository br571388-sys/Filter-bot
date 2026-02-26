#!/usr/bin/env python3
# main.py - (c) Converted from Go-Filter-Bot by Jisin0
# Python conversion of the Go-Filter-Bot

from __future__ import annotations

import asyncio
import logging
import sys
from threading import Thread

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import autodelete
import config

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Import plugins ─────────────────────────────────────────────────────────────
from plugins.basics import (
    about, cb_edit, cb_stats, get_id, help_cmd, start, stats,
)
from plugins.broadcast import broadcast
from plugins.connect import cb_connect, connect, disconnect
from plugins.filter import (
    all_mfilters, cb_alert, cb_stop, mfilter_handler, new_filter, stop_mfilter,
)
from plugins.gfilter import gfilters, start_global, stop_gfilter
from plugins.newchat import my_chat_member


# ── Healthcheck web server (for Koyeb / Render / Heroku) ──────────────────────
async def _health(request: web.Request) -> web.Response:
    return web.Response(text="Waku Waku")


async def start_webserver() -> None:
    app = web.Application()
    app.router.add_get("/", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(config.PORT))
    await site.start()
    logger.info("Health-check webserver started on port %s", config.PORT)


# ── Bot setup ──────────────────────────────────────────────────────────────────
def build_application() -> Application:
    if not config.BOT_TOKEN:
        logger.critical("Exiting Because No BOT_TOKEN Provided :(")
        sys.exit(1)

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .build()
    )

    # ── Message handler groups ─────────────────────────────────────────────────
    # Group 1: Filter handler (runs for every private/group message)
    GROUP_FILTER_HANDLER = 1
    BASIC_COMMANDS_GROUP = 2
    COMMAND_HANDLER_GROUP = 3
    CALLBACK_HANDLER_GROUP = 4

    # All messages in private/group chats → filter checker
    application.add_handler(
        MessageHandler(
            filters.TEXT | filters.CAPTION | filters.PHOTO |
            filters.DOCUMENT | filters.VIDEO | filters.AUDIO |
            filters.ANIMATION | filters.Sticker.ALL,
            mfilter_handler,
        ),
        group=GROUP_FILTER_HANDLER,
    )

    # ── Basic commands ─────────────────────────────────────────────────────────
    application.add_handler(CommandHandler("start", start), group=BASIC_COMMANDS_GROUP)
    application.add_handler(CommandHandler("about", about), group=BASIC_COMMANDS_GROUP)
    application.add_handler(CommandHandler("help", help_cmd), group=BASIC_COMMANDS_GROUP)
    application.add_handler(CommandHandler("stats", stats), group=BASIC_COMMANDS_GROUP)
    application.add_handler(CommandHandler("id", get_id), group=BASIC_COMMANDS_GROUP)

    # ── Feature commands ───────────────────────────────────────────────────────
    application.add_handler(CommandHandler("filter", new_filter), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("gfilter", new_filter), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("filters", all_mfilters), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("stop", stop_mfilter), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("gstop", stop_gfilter), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("connect", connect), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("disconnect", disconnect), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("startglobal", start_global), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("gfilters", gfilters), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("broadcast", broadcast), group=COMMAND_HANDLER_GROUP)
    application.add_handler(CommandHandler("concast", broadcast), group=COMMAND_HANDLER_GROUP)

    # ── Callback handlers ──────────────────────────────────────────────────────
    application.add_handler(
        CallbackQueryHandler(cb_connect, pattern=r"^cbconnect\("),
        group=CALLBACK_HANDLER_GROUP,
    )
    application.add_handler(
        CallbackQueryHandler(cb_stop, pattern=r"^stopf\("),
        group=CALLBACK_HANDLER_GROUP,
    )
    application.add_handler(
        CallbackQueryHandler(cb_edit, pattern=r"^edit\("),
        group=CALLBACK_HANDLER_GROUP,
    )
    application.add_handler(
        CallbackQueryHandler(cb_alert, pattern=r"^alert\("),
        group=CALLBACK_HANDLER_GROUP,
    )
    application.add_handler(
        CallbackQueryHandler(cb_stats, pattern=r"^stats$"),
        group=CALLBACK_HANDLER_GROUP,
    )

    # ── Chat member handler ────────────────────────────────────────────────────
    application.add_handler(
        ChatMemberHandler(my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    return application


# ── Main ───────────────────────────────────────────────────────────────────────
async def main() -> None:
    # Start health-check web server
    await start_webserver()

    # Initialize autodelete SQLite DB
    await autodelete.init_db()

    app = build_application()

    # Start the bot
    await app.initialize()
    await app.start()

    bot = app.bot
    me = await bot.get_me()
    logger.info("@%s Started!", me.username)

    # Start autodelete background task if enabled
    if autodelete.AUTO_DELETE_SECONDS > 0:
        asyncio.create_task(autodelete.run_autodel(bot))

    # Poll for updates (drop pending updates on start)
    await app.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

    # Run until interrupted
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
