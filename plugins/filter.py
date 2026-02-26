# plugins/filter.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.constants import ChatType
from telegram.ext import ContextTypes

import autodelete
import config
import utils
from autodelete import AutodelData, insert_autodel
from database import Filter, get_db

logger = logging.getLogger(__name__)
DB = get_db()

# ── Regex patterns ─────────────────────────────────────────────────────────────
BUTTON_REGEX = re.compile(
    r"\[([^\[]+?)\]\((buttonurl|url|alert):(?:/{0,2})(.+?)\)"
)
PARSE_REGEX = re.compile(r'^"([^"]+)"')
CBSTOP_REGEX = re.compile(r"stopf\((.+)\)")
CBALERT_REGEX = re.compile(r"alert\((.+)\)")

# ── Constants ──────────────────────────────────────────────────────────────────
LEN_UNIQUE_ID = 15
GLOBAL_NUMBER: int = 101
MAX_KEY_LENGTH = 20
MAX_BUTTONS = 5
FILTER_SPLIT_COUNT = 3
MIN_BUTTON_PARSE_PARAMS = 4
ALERT_CACHE_DURATION = 3000
CB_STOP_PARAM_COUNT = 3


# ── /filter and /gfilter commands ─────────────────────────────────────────────
async def new_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    user = update.effective_user
    chat = update.effective_chat
    text = msg.text or ""

    # Determine target chat
    if text.startswith("/gfilter"):
        if not utils.is_admin(user.id):
            await msg.reply_text("Thats an Admin-only Command :(")
            return
        target_chat_id = GLOBAL_NUMBER
    else:
        target_chat_id, valid = await _verify(update, context)
        if not valid:
            return
        if target_chat_id == 0:
            target_chat_id = chat.id

    args = text.split(" ", FILTER_SPLIT_COUNT - 1)
    if len(args) < 2 and (msg.reply_to_message is None and len(args) < FILTER_SPLIT_COUNT):
        await msg.reply_html(
            "Not Enough Parameters :(\n\nExample:- <code>/filter hi hello</code>"
        )
        return

    parse = _parse_quotes(text.split(" ", 1)[1] if len(text.split(" ", 1)) > 1 else "")
    key = parse[0].lower()

    if len(key) > MAX_KEY_LENGTH:
        await msg.reply_html(
            f"Sorry The Length of the Key Can't be More than {MAX_KEY_LENGTH} Characters !\n"
            f"Input Key: <code>{key}</code>"
        )
        return

    # Check if filter already exists
    existing, exists = DB.get_mfilter(target_chat_id, key)
    if exists:
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Stop Filter", callback_data=f"stopf({key}|local|y)")]]
        )
        await msg.reply_html(
            f"It Looks Like Another Filter For <code>{key}</code> Has Already Been Saved In This Chat, "
            "If You Want To Stop It First Use The Button Below",
            reply_markup=markup,
        )
        return

    content = parse[1] if len(parse) > 1 else ""
    button: list[list[dict]] = []

    # Extract content from replied-to message
    if msg.reply_to_message:
        rep = msg.reply_to_message
        content += (rep.text or "") + (rep.caption or "")

        if rep.reply_markup:
            button = _button_to_map(rep.reply_markup.inline_keyboard)

    unique_id = utils.rand_string(LEN_UNIQUE_ID)
    content, button, alerts = _parse_buttons(content, unique_id, button)

    # Detect media
    file_id = ""
    media_type = ""
    if msg.reply_to_message:
        rep = msg.reply_to_message
        if rep.document:
            file_id = rep.document.file_id
            media_type = "document"
        elif rep.video:
            file_id = rep.video.file_id
            media_type = "video"
        elif rep.audio:
            file_id = rep.audio.file_id
            media_type = "audio"
        elif rep.sticker:
            file_id = rep.sticker.file_id
            media_type = "sticker"
        elif rep.animation:
            file_id = rep.animation.file_id
            media_type = "animation"
        elif rep.photo:
            file_id = rep.photo[-1].file_id
            media_type = "photo"

    f = Filter(
        id=unique_id,
        chat_id=target_chat_id,
        text=key,
        content=content,
        file_id=file_id,
        markup=button,
        alerts=alerts,
        length=len(key),
        media_type=media_type,
    )
    DB.save_mfilter(f)

    await msg.reply_html(f"<i>Successfully Saved A Manual Filter For <code>{key}</code> !</i>")


# ── /stop command ──────────────────────────────────────────────────────────────
async def stop_mfilter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    chat = update.effective_chat

    target_chat_id, valid = await _verify(update, context)
    if not valid:
        return
    if target_chat_id == 0:
        target_chat_id = chat.id

    text = msg.text or ""
    split = text.split(" ", 1)
    key = ""

    if len(split) < 2:
        if chat.type == ChatType.PRIVATE:
            reply = await utils.ask(
                context.bot,
                "Ok Now Send Me The Name OF The Filter You Would Like To Stop ...",
                chat.id,
                msg.from_user.id,
            )
            if reply is None:
                return
            key = reply.text or ""
        else:
            await msg.reply_text("Whoops looks like you forgot to mention a filter to stop !")
            return
    else:
        key = split[1]

    _, local_exists = DB.get_mfilter(target_chat_id, key)
    _, global_exists = DB.get_mfilter(GLOBAL_NUMBER, key)

    if not local_exists and not global_exists:
        await msg.reply_html(f"I Couldnt Find Any Filter For <code>{key}</code> To Stop !")
        return

    if local_exists and global_exists:
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("Local", callback_data=f"stopf({key}|local|y)"),
            InlineKeyboardButton("Global", callback_data=f"stopf({key}|global|y)"),
        ]])
        await msg.reply_html(
            "Please Select If You Would Like To Stop The Manual Filter (which you saved) "
            f"Or Global Filter (saved by owners) For <code>{key}</code>",
            reply_markup=markup,
        )
    elif local_exists:
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("CONFIRM", callback_data=f"stopf({key}|local|y)")]]
        )
        await msg.reply_html(
            f"Please Press The Button Below To Confirm Deletion Of Manual Filter For <code>{key}</code>",
            reply_markup=markup,
        )
    else:
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("CONFIRM", callback_data=f"stopf({key}|global|y)")]]
        )
        await msg.reply_html(
            f"Please Press The Button Below To Stop Global Filter For <code>{key}</code>",
            reply_markup=markup,
        )


# ── /filters command ───────────────────────────────────────────────────────────
async def all_mfilters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    chat_id = msg.chat.id

    if msg.chat.type == ChatType.PRIVATE:
        connected, ok = DB.get_connection(msg.from_user.id)
        if ok:
            chat_id = connected

    text = DB.string_mfilter(chat_id)
    await msg.reply_html("Lɪsᴛ ᴏғ ғɪʟᴛᴇʀs ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ :\n" + text)


# ── Callback: stopf(key|type|action) ──────────────────────────────────────────
async def cb_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    target_chat_id, valid = await _verify(update, context)
    if not valid:
        return
    if target_chat_id == 0:
        target_chat_id = query.message.chat.id

    m = CBSTOP_REGEX.search(query.data)
    if not m:
        await query.answer("Bad Button :(", show_alert=True)
        return

    args = m.group(1).split("|")
    if len(args) < CB_STOP_PARAM_COUNT:
        await query.answer("Bad Button :(", show_alert=True)
        return

    key, ftype, erase = args[0], args[1], args[2]

    if ftype == "local":
        if erase == "y":
            DB.delete_mfilter(target_chat_id, key)
            await query.edit_message_text(
                f"Manual Filter For <code>{key}</code> Was Deleted Successfully !",
                parse_mode="HTML",
            )
    elif ftype == "global":
        DB.stop_gfilter(target_chat_id, key)
        await query.edit_message_text(
            f"Global Filter For <code>{key}</code> Has Been Stopped Successfully !",
            parse_mode="HTML",
        )


# ── Callback: alert(uniqueID|index) ───────────────────────────────────────────
async def cb_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    m = CBALERT_REGEX.search(query.data)
    if not m:
        await query.answer("Bad Request !", show_alert=True)
        return

    parts = m.group(1).split("|")
    if len(parts) < 2:
        await query.answer("Bad Request !", show_alert=True)
        return

    unique_id = parts[0]
    try:
        index = int(parts[1])
    except ValueError:
        await query.answer("Bad Request !", show_alert=True)
        return

    text = DB.get_alert(unique_id, index)
    await query.answer(text, show_alert=True, cache_time=ALERT_CACHE_DURATION)


# ── Message handler: check all messages for filter matches ────────────────────
async def mfilter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message or update.channel_post
    if not msg:
        return

    # Check if this is a pending ask reply
    if msg.from_user and utils.has_pending_ask(msg.from_user.id):
        await utils.resolve_ask(msg.from_user.id, msg)
        return

    # Run manual + global filters concurrently
    await asyncio.gather(
        _run_mfilter(msg, context.bot),
        _run_gfilter(msg, context.bot),
    )


# ── Internal filter runners ────────────────────────────────────────────────────
async def _run_mfilter(msg: Message, bot: Bot) -> None:
    chat_type = msg.chat.type
    chat_id: int

    if chat_type == ChatType.PRIVATE:
        connected, ok = DB.get_connection(msg.from_user.id)
        if not ok:
            return
        chat_id = connected
    elif chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
        chat_id = msg.chat.id
    else:
        return

    text = msg.text or msg.caption or ""
    if not text:
        return

    fields = text.split()
    if len(fields) <= 15:
        results = DB.search_mfilter_new(chat_id, fields, config.MULTI_FILTER)
    else:
        results = DB.search_mfilter_classic(chat_id, text)

    for f in results:
        await _send_filter(f, bot, msg, chat_id, msg.message_id)


async def _run_gfilter(msg: Message, bot: Bot) -> None:
    chat_type = msg.chat.type
    chat_id: int

    if chat_type == ChatType.PRIVATE:
        connected, ok = DB.get_connection(msg.from_user.id)
        if not ok:
            return
        chat_id = connected
    elif chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
        chat_id = msg.chat.id
    else:
        return

    text = msg.text or msg.caption or ""
    if not text:
        return

    stopped = DB.get_cached_setting(chat_id).stopped
    fields = text.split()

    if len(fields) <= 15:
        results = DB.search_mfilter_new(GLOBAL_NUMBER, fields, config.MULTI_FILTER)
    else:
        results = DB.search_mfilter_classic(GLOBAL_NUMBER, text)

    for f in results:
        if f.text in stopped:
            continue
        await _send_filter(f, bot, msg, chat_id, msg.message_id)


# ── Send a filter response ─────────────────────────────────────────────────────
async def _send_filter(
    f: Filter, bot: Bot, update_msg: Message, chat_id: int, message_id: int
) -> None:
    markup = utils.build_markup(f.markup)
    content = f.content
    sent: Optional[Message] = None

    try:
        if f.media_type:
            if f.media_type == "document":
                sent = await bot.send_document(
                    chat_id, f.file_id, caption=content, reply_markup=markup,
                    parse_mode="HTML",
                    reply_to_message_id=message_id,
                )
            elif f.media_type == "video":
                sent = await bot.send_video(
                    chat_id, f.file_id, caption=content, reply_markup=markup,
                    parse_mode="HTML",
                    reply_to_message_id=message_id,
                )
            elif f.media_type == "audio":
                sent = await bot.send_audio(
                    chat_id, f.file_id, caption=content, reply_markup=markup,
                    parse_mode="HTML",
                    reply_to_message_id=message_id,
                )
            elif f.media_type == "photo":
                sent = await bot.send_photo(
                    chat_id, f.file_id, caption=content, reply_markup=markup,
                    parse_mode="HTML",
                    reply_to_message_id=message_id,
                )
            elif f.media_type == "sticker":
                sent = await bot.send_sticker(
                    chat_id, f.file_id, reply_markup=markup,
                    reply_to_message_id=message_id,
                )
            elif f.media_type == "animation":
                sent = await bot.send_animation(
                    chat_id, f.file_id, caption=content, reply_markup=markup,
                    parse_mode="HTML",
                    reply_to_message_id=message_id,
                )
            else:
                logger.warning("Unknown media type: %s", f.media_type)
        else:
            sent = await update_msg.reply_html(
                content,
                reply_markup=markup,
                reply_to_message_id=message_id,
            )
    except Exception as e:
        logger.error("send_filter: %s | filter: %s", e, f)
        return

    if sent and autodelete.AUTO_DELETE_SECONDS > 0:
        await insert_autodel(
            AutodelData(chat_id=chat_id, message_id=sent.message_id),
            autodelete.AUTO_DELETE_SECONDS,
        )


# ── Parse helpers ──────────────────────────────────────────────────────────────
def _parse_quotes(text: str) -> list[str]:
    m = PARSE_REGEX.match(text)
    if m:
        key = m.group(1)
        remainder = text.replace(f'"{key}"', "", 1)
        return [key, remainder]
    parts = text.split(" ", 1)
    key = parts[0]
    remainder = text.replace(key, "", 1)
    return [key, remainder]


def _parse_buttons(
    text: str, unique_id: str, total_buttons: list[list[dict]]
) -> tuple[str, list[list[dict]], list[str]]:
    return_text = text
    alert: list[str] = []

    for line in text.split("\n"):
        row_buttons: list[dict] = []
        for m in BUTTON_REGEX.findall(line):
            if len(m) < 3:
                continue
            btn_text, btn_type, btn_value = m[0], m[1], m[2]

            if btn_type in ("url", "buttonurl"):
                row_buttons.append({"Text": btn_text, "Url": btn_value})
            elif btn_type in ("alert", "buttonalert"):
                alert.append(btn_value)
                row_buttons.append({
                    "Text": btn_text,
                    "CallbackData": f"alert({unique_id}|{len(alert) - 1})",
                })

            # Remove matched syntax from text
            return_text = return_text.replace(
                f"[{btn_text}]({btn_type}:{btn_value})", "", 1
            )

        if row_buttons:
            total_buttons.append(row_buttons)

    return return_text.strip(), total_buttons, alert


def _button_to_map(
    keyboard: list[list]
) -> list[list[dict]]:
    result: list[list[dict]] = []
    for row in keyboard:
        row_data: list[dict] = []
        for btn in row:
            b: dict = {"Text": btn.text}
            if getattr(btn, "callback_data", None):
                b["CallbackData"] = btn.callback_data
            elif getattr(btn, "url", None):
                b["Url"] = btn.url
            else:
                continue
            row_data.append(b)
        if row_data:
            result.append(row_data)
    return result


# ── Verify helper (check admin for non-private chats) ─────────────────────────
_cached_admins: dict[int, list[int]] = {}


async def _verify(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> tuple[int, bool]:
    """Returns (chat_id_override, is_valid). chat_id_override=0 means use current chat."""
    bot = context.bot
    query = update.callback_query
    msg = update.message

    if query:
        chat = query.message.chat
        user_id = query.from_user.id
        msg_id = query.message.message_id
    else:
        chat = msg.chat
        user_id = msg.from_user.id if msg.from_user else 0
        msg_id = msg.message_id

    chat_type = chat.type

    if chat_type == ChatType.PRIVATE:
        connected, ok = DB.get_connection(user_id)
        if not ok:
            await bot.send_message(
                chat.id, "Please connect to a chat first to use this operation !",
                reply_to_message_id=msg_id,
            )
            return 0, False
        return connected, True

    elif chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if user_id == 0:
            await bot.send_message(
                chat.id,
                "Sorry It Looks Like You Are Anonymous Please Connect From Pm And Use Me Or Turn Off Anonymous :(",
                reply_to_message_id=msg_id,
            )
            return 0, False

        # Check admin cache
        if chat.id in _cached_admins:
            if user_id in _cached_admins[chat.id]:
                return 0, True
            if query:
                await query.answer("Who dis non-admin telling me what to do !", show_alert=True)
            else:
                await bot.send_message(
                    chat.id,
                    "Hey You're Not An Admin, If You Are A New Admin Use /updateadmins !",
                    reply_to_message_id=msg_id,
                )
            return 0, False
        else:
            try:
                admins = await bot.get_chat_administrators(chat.id)
                admin_ids = [a.user.id for a in admins]
                _cached_admins[chat.id] = admin_ids
                if user_id in admin_ids:
                    return 0, True
            except Exception:
                return 0, False

            if query:
                await query.answer("Who dis non-admin telling me what to do !", show_alert=True)
            else:
                await bot.send_message(
                    chat.id, "Who dis non-admin telling me what to do !",
                    reply_to_message_id=msg_id,
                )
            return 0, False

    return 0, False
