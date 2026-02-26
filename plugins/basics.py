# plugins/basics.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import config
import utils
from database import get_db

logger = logging.getLogger(__name__)
DB = get_db()


# ── /start ─────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    bot = context.bot

    # Save user (non-blocking)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, DB.add_user, user.id)

    text = config.TEXT["START"].format(user.first_name, bot.first_name)
    markup = utils.build_markup_from_config(config.BUTTONS["START"])

    await update.message.reply_html(text, reply_markup=markup)


# ── /about ─────────────────────────────────────────────────────────────────────
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup = utils.build_markup_from_config(config.BUTTONS["ABOUT"])
    await update.message.reply_html(config.TEXT["ABOUT"], reply_markup=markup)


# ── /help ──────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup = utils.build_markup_from_config(config.BUTTONS["HELP"])
    await update.message.reply_html(config.TEXT["HELP"], reply_markup=markup)


# ── /stats ─────────────────────────────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Refresh 🔄", callback_data="stats")]]
    )
    await update.message.reply_html(DB.stats(), reply_markup=markup)


# ── /id ────────────────────────────────────────────────────────────────────────
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    text = ""

    if msg.reply_to_message:
        text += f"\nReplied to user : <code>{msg.reply_to_message.from_user.id}</code>"

        if msg.reply_to_message.forward_origin:
            origin = msg.reply_to_message.forward_origin
            # Handle different forward origin types
            chat_id = getattr(getattr(origin, "chat", None), "id", None)
            if chat_id:
                text += f"\nForwarded from : <code>{chat_id}</code>"

    text += f"\nUser id : <code>{msg.from_user.id}</code>"

    if msg.chat.type != "private":
        text += f"\nChat id : <code>{msg.chat.id}</code>"

    await msg.reply_html(text)


# ── Callback: stats refresh ────────────────────────────────────────────────────
async def cb_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    markup = utils.build_markup_from_config(config.BUTTONS["STATS"])
    await query.edit_message_text(DB.stats(), parse_mode="HTML", reply_markup=markup)


# ── Callback: edit(KEY) – navigate help menus ──────────────────────────────────
async def cb_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    import re
    m = re.match(r"edit\((.+)\)", query.data)
    if not m:
        return
    key = m.group(1)

    btn_list = config.BUTTONS.get(key, [[{"text": "⤝ Bᴀᴄᴋ", "callback_data": "edit(HELP)"}]])
    markup = utils.build_markup_from_config(btn_list)

    if key == "START":
        text = config.TEXT["START"].format(query.from_user.first_name, context.bot.first_name)
    else:
        text = config.TEXT.get(key, "")

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=markup,
        disable_web_page_preview=True,
    )



