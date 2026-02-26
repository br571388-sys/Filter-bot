# plugins/gfilter.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

import utils
from database import get_db
from plugins.filter import GLOBAL_NUMBER, _verify

logger = logging.getLogger(__name__)
DB = get_db()


# ── /gstop command ─────────────────────────────────────────────────────────────
async def stop_gfilter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    user = update.effective_user

    if not utils.is_admin(user.id):
        await msg.reply_text("Only bot admins can use this command !")
        return

    text = msg.text or ""
    split = text.split(" ", 1)
    key = ""

    if len(split) < 2:
        reply = await utils.ask(
            context.bot,
            "Ok Now Send Me The Name OF The Filter You Would Like To Stop ...",
            msg.chat.id,
            user.id,
        )
        if reply is None:
            return
        key = reply.text or ""
    else:
        key = split[1]

    _, ok = DB.get_mfilter(GLOBAL_NUMBER, key)
    if not ok:
        await msg.reply_html(f"I Couldnt Find Any Global Filter For <code>{key}</code> To Stop !")
        return

    DB.delete_mfilter(GLOBAL_NUMBER, key)
    await msg.reply_html(f"Global Filter For <i>{key}</i> Was Stopped Successfully !")


# ── /startglobal command ───────────────────────────────────────────────────────
async def start_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    chat = update.effective_chat

    target_chat_id, valid = await _verify(update, context)
    if not valid:
        return
    if target_chat_id == 0:
        target_chat_id = chat.id

    text = msg.text or ""
    split = text.split(" ", 1)

    if len(split) < 2 or not split[1].strip():
        await msg.reply_text("Bad Usage No Keyword Provided :(")
        return

    key = split[1].strip()

    _, ok = DB.get_mfilter(GLOBAL_NUMBER, key)
    if not ok:
        await msg.reply_text(f"No Global Filter For {key} Was Found To Restart !")
        return

    for k in DB.get_cached_setting(target_chat_id).stopped:
        if k == key:
            DB.start_gfilter(target_chat_id, key)
            await msg.reply_html(f"Restarted Global Filter For <i>{key}</i> Successfully !")
            return

    await msg.reply_text(f"You Havent Stopped Any Global Filter For {key} :(")


# ── /gfilters command ──────────────────────────────────────────────────────────
async def gfilters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = DB.string_mfilter(GLOBAL_NUMBER)
    await update.message.reply_html(
        "Aʟʟ ғɪʟᴛᴇʀs sᴀᴠᴇᴅ ғᴏʀ ɢʟᴏʙᴀʟ ᴜsᴀɢᴇ :\n" + text
    )
