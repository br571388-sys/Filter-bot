# plugins/newchat.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from autodelete import AutodelData, insert_autodel, AUTO_DELETE_SECONDS
from database import get_db

logger = logging.getLogger(__name__)
DB = get_db()

WELCOME_TEXT = (
    "<b><i>👋ᴛʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
    "I ᴄᴀɴ'ᴛ ᴡᴀɪᴛ ᴛᴏ sᴛᴀʀᴛ ʜᴇʟᴘɪɴɢ ʏᴏᴜ ᴏᴜᴛ, "
    "ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ'ᴠᴇ ᴍᴀᴅᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ғɪʀsᴛ !</i></b>"
)


async def my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    my_member = update.my_chat_member

    if not my_member:
        return

    # Only care when it's about the bot itself
    if my_member.new_chat_member.user.id != bot.id:
        return

    chat = my_member.chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    # Save default settings for this chat
    DB.set_default_settings(chat.id)

    try:
        sent = await bot.send_message(chat.id, WELCOME_TEXT, parse_mode="HTML")
        # Auto-delete welcome message after 4 minutes (240 s)
        await insert_autodel(
            AutodelData(chat_id=sent.chat.id, message_id=sent.message_id),
            240,
        )
    except Exception as e:
        logger.error("my_chat_member: %s", e)
