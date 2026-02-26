# config.py - (c) Converted from Go-Filter-Bot by Jisin0

import os
from dotenv import load_dotenv

load_dotenv()

# ── Environment Variables ──────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
MONGODB_URI: str = os.getenv("MONGODB_URI", "")
ADMINS: list[int] = [int(x) for x in os.getenv("ADMINS", "").split() if x.strip()]
MULTI_FILTER: bool = os.getenv("MULTI_FILTER", "false").lower() == "true"
AUTO_DELETE: int = int(os.getenv("AUTO_DELETE", "0"))  # minutes
PORT: str = os.getenv("PORT", "10000")

# ── Bot Texts ──────────────────────────────────────────────────────────────────
TEXT: dict[str, str] = {
    "START": (
        "<b>Hᴇʏ {0} ɪᴍ {1} ᴀɴ Aᴡᴇsᴏᴍᴇ Filter bot with global filter support</b>\n\n"
        "<i>I can save a custom reply for a word in any chat. Check my help menu for more details.</i>"
    ),
    "ABOUT": (
        "<b>○ 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾 :</b> : <a href='https://python.org'>Python</a>\n"
        "<b>○ 𝖫𝗂𝖻𝗋𝖺𝗋𝗒</b> : <a href='https://python-telegram-bot.org'>python-telegram-bot</a>\n"
        "<b>○ 𝖣𝖺𝗍𝖺𝖻𝖺𝗌𝖾</b> : <a href='https://mongodb.org'>mongoDB</a>\n"
        "<b>○ 𝖲𝗎𝗉𝗉𝗈𝗋𝗍</b> : <a href='t.me/Jisin0'>Here</a>"
    ),
    "MF": (
        "Mᴀɴᴜᴀʟ ғɪʟᴛᴇʀs ᴀʟʟᴏᴡ ʏᴏᴜ ᴛᴏ sᴀᴠᴇ ᴄᴜsᴛᴏᴍ ғɪʟᴛᴇʀs ᴏᴛʜᴇʀ ᴛʜᴀɴ ᴛʜᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄ ᴏɴᴇs. "
        "Fɪʟᴛᴇʀs ᴄᴀɴ ʙᴇ ᴏғ ᴛᴇxᴛ/ᴘʜᴏᴛᴏ/ᴅᴏᴄᴜᴍᴇɴᴛ/ᴀᴜᴅɪᴏ/ᴀɴɪᴍᴀᴛɪᴏɴ/ᴠɪᴅᴇᴏ .\n\n"
        "<b><u>Nᴇᴡ ғɪʟᴛᴇʀ :</u></b>\n\n"
        "<b>Fᴏʀᴍᴀᴛ</b>\n"
        "  <code>/filter \"keyword\" text</code> or\n"
        "  Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ -><code>/filter \"keyword\"</code>\n"
        "<b>Usᴀɢᴇ</b>\n"
        "  <code>/filter \"hi\" hello</code>\n"
        "  [<code>hello</code>] -> Reply -> <code>/filter hi</code>\n\n"
        "<b><u>Sᴛᴏᴘ ғɪʟᴛᴇʀ :</u></b>\n\n"
        "<b>Fᴏʀᴍᴀᴛ</b>\n"
        "  <code>/stop \"keyword\"</code>\n"
        "<b>Usᴀɢᴇ</b>\n"
        "  <code>/stop \"hi\"</code>\n\n"
        "<b><u>Vɪᴇᴡ ғɪʟᴛᴇʀs :</u></b>\n"
        "  <code>/filters</code>"
    ),
    "GF": (
        "<b>Gʟᴏʙᴀʟ ғɪʟᴛᴇʀs ᴀʀᴇ ᴍᴀɴᴜᴀʟ ғɪʟᴛᴇʀs sᴀᴠᴇᴅ ʙʏ ʙᴏᴛ ᴀᴅᴍɪɴs ᴛʜᴀᴛ ᴡᴏʀᴋ ɪɴ ᴀʟʟ ᴄʜᴀᴛs. "
        "Tʜᴇʏ ᴘʀᴏᴠɪᴅᴇ ʟᴀᴛᴇsᴛ ᴍᴏᴠɪᴇs ɪɴ ᴀ ᴇᴀsʏ ᴛᴏ ᴜsᴇ ғᴏʀᴍᴀᴛ.</b>\n\n"
        "<b><u>Sᴛᴏᴘ ғɪʟᴛᴇʀ :</u></b>\n\n"
        "<u>Fᴏʀᴍᴀᴛ</u>\n"
        "<code>/stop \"keyword\"</code>\n"
        "<u>Usᴀɢᴇ</u>\n"
        "<code>/stop \"et\"</code>\n\n"
        "<b><u>Vɪᴇᴡ ғɪʟᴛᴇʀs :</u></b>\n"
        "/gfilters"
    ),
    "CONNECT": (
        "<b>Cᴏɴɴᴇᴄᴛɪᴏɴs ᴀʟʟᴏᴡ ʏᴏᴜ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ʜᴇʀᴇ ɪɴ ᴘᴍ ɪɴsᴛᴇᴀᴅ ᴏғ sᴇɴᴅɪɴɢ "
        "ᴛʜᴏsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴘᴜʙʟɪᴄʟʏ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ⠘⁾</b>\n\n"
        "<b><u>Cᴏɴɴᴇᴄᴛ :</u></b>\n"
        "-> Fɪʀsᴛ ɢᴇᴛ ʏᴏᴜʀ ɢʀᴏᴜᴘ's ɪᴅ ʙʏ sᴇɴᴅɪɴɢ /id ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ\n"
        "-> <code>/connect [group_id]</code>\n\n"
        "<b><u>Dɪsᴄᴏɴɴᴇᴄᴛ :</u></b>\n"
        "<code>/disconnect</code>"
    ),
    "BROADCAST": (
        "<b>The broadcast feature allows bot admins to broadcast a message to all of the bot's users.</b>\n\n"
        "<i>Broadcasts are of two types :</i>\n"
        " ~ Full Broadcast - Broadcast to all of the bot users <code>/broadcast</code>\n"
        " ~ Concast - Broadcast to only users who are connected to a chat <code>/concast</code>"
    ),
    "HELP": "<b>To know how to use my modules use the buttons below to get all my commands with usage examples !</b>",
    "BTN": (
        "Here's a format of how you can add buttons to filters.\n"
        "Buttons are split into different rows by using a new line.\n\n"
        "<b>URL Button</b>\n"
        "  <code>[Button Text](url:https://example.com)</code>\n\n"
        "<b>Alert Button</b>\n"
        "  <code>[Button Text](alert:This is an alert)</code>"
    ),
}

# ── Button Configurations ──────────────────────────────────────────────────────
# Format: list of rows, each row is a list of button dicts
BUTTONS: dict[str, list[list[dict]]] = {
    "START": [
        [
            {"text": "About", "callback_data": "edit(ABOUT)"},
            {"text": "Help", "callback_data": "edit(HELP)"},
        ]
    ],
    "ABOUT": [
        [
            {"text": "Home", "callback_data": "edit(START)"},
            {"text": "Stats", "callback_data": "stats"},
        ],
        [{"text": "Source 🔗", "url": "https://github.com/Jisin0/Go-Filter-Bot"}],
    ],
    "STATS": [
        [
            {"text": "⬅ Back", "callback_data": "edit(ABOUT)"},
            {"text": "Refresh 🔄", "callback_data": "stats"},
        ]
    ],
    "HELP": [
        [
            {"text": "Fɪʟᴛᴇʀ", "callback_data": "edit(MF)"},
            {"text": "Gʟᴏʙᴀʟ", "callback_data": "edit(GF)"},
        ],
        [
            {"text": "Cᴏɴɴᴇᴄᴛ", "callback_data": "edit(CONNECT)"},
            {"text": "Broadcast", "callback_data": "edit(BROADCAST)"},
        ],
        [{"text": "Bᴀᴄᴋ ➔", "callback_data": "edit(START)"}],
    ],
    "MF": [
        [
            {"text": "ʙᴜᴛᴛᴏɴs", "callback_data": "edit(BTN)"},
            {"text": "bᴀᴄᴋ ➔", "callback_data": "edit(HELP)"},
        ]
    ],
    "BTN": [[{"text": "bᴀᴄᴋ ➔", "callback_data": "edit(MF)"}]],
    "GF": [[{"text": "bᴀᴄᴋ ➔", "callback_data": "edit(HELP)"}]],
    "CONNECT": [[{"text": "bᴀᴄᴋ ➔", "callback_data": "edit(HELP)"}]],
    "BROADCAST": [[{"text": "bᴀᴄᴋ ➔", "callback_data": "edit(HELP)"}]],
}
