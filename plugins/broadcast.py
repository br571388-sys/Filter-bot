# plugins/broadcast.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

import utils
from database import get_db

logger = logging.getLogger(__name__)
DB = get_db()


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    user = update.effective_user
    bot = context.bot

    if not utils.is_admin(user.id):
        await msg.reply_html(
            "<b>Only bot admins can use this command !</b>",
            reply_to_message_id=msg.message_id,
        )
        return

    text = msg.text or ""
    is_concast = text.startswith("/concast")

    # Build filter for users collection
    mongo_filter: dict = {}
    if is_concast:
        mongo_filter = {"connected": {"$exists": True}}

    if msg.reply_to_message is None:
        await msg.reply_text(
            "Please reply this command to the message you would like to broadcast !"
        )
        return

    rep = msg.reply_to_message
    is_text = bool(rep.text)
    caption = rep.caption_html if not is_text else None
    markup = rep.reply_markup if rep.reply_markup else None

    stat = await msg.reply_html("<code>Starting broadcast ...</code>")

    total = 0
    sent = 0
    failed = 0

    cursor = DB.ucol.find(mongo_filter)
    for doc in cursor:
        raw_id = doc.get("_id")
        if raw_id is None:
            continue
        uid = int(raw_id)

        try:
            if is_text:
                await rep.copy(bot, uid, reply_markup=markup)
            else:
                await rep.copy(
                    bot, uid,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
            sent += 1
        except Exception as e:
            logger.error("broadcast.send: %s", e)
            failed += 1

        total += 1

        # Update stats every 20 messages to avoid flood
        if total % 20 == 0:
            try:
                await stat.edit_text(
                    f"<u>Live Broadcast Stats :</u>\n\nSuccess : {sent}\nFailed  : {failed}\nTotal   : {total}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    try:
        await stat.edit_text(
            f"<b><u>Broadcast Completed :</u></b>\n\nSuccess : {sent}\nFailed  : {failed}\nTotal   : {total}",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("broadcast.complete: %s", e)
