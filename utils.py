# utils.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import asyncio
import random
import string
from typing import Optional

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import ContextTypes

import config

# ── Constants ──────────────────────────────────────────────────────────────────
_CHARSET = string.ascii_letters + string.digits
ASK_TIMEOUT = 300  # seconds (5 minutes)

# pending asks: user_id → asyncio.Future[Message]
_pending_asks: dict[int, asyncio.Future] = {}


# ── Utility functions ──────────────────────────────────────────────────────────
def rand_string(length: int) -> str:
    """Generate a random alphanumeric string of the given length."""
    return "".join(random.choices(_CHARSET, k=length))


def is_admin(user_id: int) -> bool:
    """Check whether the user is a global bot admin (from env)."""
    return user_id in config.ADMINS


def contains(lst: list[str], value: str) -> bool:
    """Check if a string list contains the given value."""
    return value in lst


def build_markup(button_data: list[list[dict[str, str]]]) -> Optional[InlineKeyboardMarkup]:
    """Convert a list-of-rows button structure to an InlineKeyboardMarkup."""
    if not button_data:
        return None

    keyboard: list[list[InlineKeyboardButton]] = []
    for row in button_data:
        btn_row: list[InlineKeyboardButton] = []
        for b in row:
            text = b.get("Text", b.get("text", ""))
            url = b.get("Url", b.get("url", ""))
            cb = b.get("CallbackData", b.get("callback_data", ""))
            if url:
                btn_row.append(InlineKeyboardButton(text=text, url=url))
            elif cb:
                btn_row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if btn_row:
            keyboard.append(btn_row)

    return InlineKeyboardMarkup(keyboard) if keyboard else None


def build_markup_from_config(
    button_list: list[list[dict]],
) -> InlineKeyboardMarkup:
    """Build InlineKeyboardMarkup from config BUTTONS format."""
    keyboard: list[list[InlineKeyboardButton]] = []
    for row in button_list:
        btn_row: list[InlineKeyboardButton] = []
        for b in row:
            text = b.get("text", "")
            url = b.get("url", "")
            cb = b.get("callback_data", "")
            if url:
                btn_row.append(InlineKeyboardButton(text=text, url=url))
            elif cb:
                btn_row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if btn_row:
            keyboard.append(btn_row)
    return InlineKeyboardMarkup(keyboard)


# ── Ask / Conversation helper ──────────────────────────────────────────────────
async def ask(
    bot: Bot,
    text: str,
    chat_id: int,
    user_id: int,
    message_id: Optional[int] = None,
) -> Optional[Message]:
    """
    Send a message and wait up to ASK_TIMEOUT seconds for the user to reply.
    Returns the reply Message or None on timeout.
    """
    sent = await bot.send_message(chat_id, text, parse_mode="HTML")
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _pending_asks[user_id] = future

    try:
        msg = await asyncio.wait_for(asyncio.shield(future), timeout=ASK_TIMEOUT)
        return msg
    except asyncio.TimeoutError:
        _pending_asks.pop(user_id, None)
        await bot.send_message(
            chat_id,
            "<i>Request timed out ❗</i>",
            parse_mode="HTML",
        )
        return None


async def resolve_ask(user_id: int, message: Message) -> bool:
    """
    Called from the message handler to resolve a pending ask.
    Returns True if this message resolved a pending ask.
    """
    future = _pending_asks.pop(user_id, None)
    if future and not future.done():
        future.set_result(message)
        return True
    return False


def has_pending_ask(user_id: int) -> bool:
    return user_id in _pending_asks
