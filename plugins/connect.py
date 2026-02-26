# plugins/connect.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

import utils
from database import get_db

logger = logging.getLogger(__name__)
DB = get_db()

CBCONNECT_REGEX = re.compile(r"cbconnect\((.+)\)")


# ── /connect command ───────────────────────────────────────────────────────────
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    bot = context.bot
    user = msg.from_user
    chat = msg.chat

    # Check existing connections
    _, already_connected = DB.get_connection(user.id)
    if already_connected:
        await msg.reply_text(
            "Looks Like You Are Already Connected To A Chat, Please /disconnect From It To Connect To Another One :)"
        )
        return

    if chat.type == ChatType.PRIVATE:
        args = (msg.text or "").split(" ")
        if len(args) < 2:
            reply = await utils.ask(
                bot,
                "Please send the id of the chat you would like to connect to : ",
                chat.id,
                user.id,
            )
            if reply is None:
                return
            chat_raw = reply.text or ""
        else:
            chat_raw = args[1]

        try:
            chat_id = int(chat_raw)
        except ValueError:
            await msg.reply_text(
                "That Doesnt Seem Like A Valid ChatId A ChatId Looks Something Like -100xxxxxxxxxx :("
            )
            return

        try:
            admins = await bot.get_chat_administrators(chat_id)
        except Exception:
            await msg.reply_html(
                f"Sorry Looks Like I Couldnt Find That Chat With Id <code>{chat_id}</code>. "
                "Make Sure I'm Admin There With Full Permissions :("
            )
            return

        for admin in admins:
            if user.id == admin.user.id:
                DB.connect_user(user.id, chat_id)
                await msg.reply_text("Awesome I've Successfully Connected You To Your Group !")
                return

        await msg.reply_text("You Cant Connect To A Chat Where You're Not Admin :)")

    elif chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if not user or user.id == 0:
            markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Connect Me", callback_data="cbconnect(con)")]]
            )
            await msg.reply_text(
                "It Looks Like You Are Anonymous Click The Button Below To Connect :(",
                reply_markup=markup,
            )
            return

        try:
            admins = await bot.get_chat_administrators(chat.id)
        except Exception:
            await msg.reply_html(
                "Sorry I Couldn't access the admins list of this chat!\nPlease make sure I'm an admin here."
            )
            return

        for admin in admins:
            if user.id == admin.user.id:
                DB.connect_user(user.id, chat.id)
                await msg.reply_text("Awesome I've Successfully Connected You To This Group !")
                return

        await msg.reply_text("Ok Mr. Non-Admin :)")


# ── /disconnect command ────────────────────────────────────────────────────────
async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    user = msg.from_user

    if not user or user.id == 0:
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Disconnect Me", callback_data="cbconnect(dis)")]]
        )
        await msg.reply_text(
            "Sorry Looks Like You Are Anonymous Use The Button Below To Prove Your Identity :)",
            reply_markup=markup,
        )
        return

    DB.delete_connection(user.id)
    await msg.reply_text("Any Existing Connections Were Cleared Successfully :)")


# ── Callback: cbconnect(con|dis) ───────────────────────────────────────────────
async def cb_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    bot = context.bot

    m = CBCONNECT_REGEX.search(query.data)
    if not m:
        logger.error("cb_connect: bad callback data %s", query.data)
        return

    action = m.group(1)

    if action == "con":
        try:
            admins = await bot.get_chat_administrators(query.message.chat.id)
        except Exception:
            await query.answer("Failed to get admin list.", show_alert=True)
            return

        for admin in admins:
            if query.from_user.id == admin.user.id:
                DB.connect_user(query.from_user.id, query.message.chat.id)
                await query.answer(
                    "Awesome I've Successfully Connected You To This Group !",
                    show_alert=True,
                )
                await query.message.delete()
                return

        await query.answer("Ok Mr. Non-Admin :)", show_alert=True)

    elif action == "dis":
        DB.delete_connection(query.from_user.id)
        await query.answer(
            "All Of Your Connections Were Cleared :)", show_alert=True
        )
