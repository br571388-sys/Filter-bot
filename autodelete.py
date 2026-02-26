# autodelete.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiosqlite
from telegram import Bot

import config

logger = logging.getLogger(__name__)

_DB_PATH = "./cache.sqlite"
_db_conn: aiosqlite.Connection | None = None

AUTO_DELETE_SECONDS = config.AUTO_DELETE * 60  # convert minutes → seconds


@dataclass
class AutodelData:
    chat_id: int
    message_id: int
    exp_time: datetime | None = None


# ── DB Setup ───────────────────────────────────────────────────────────────────
async def init_db() -> None:
    global _db_conn
    if config.AUTO_DELETE == 0:
        return

    _db_conn = await aiosqlite.connect(_DB_PATH)
    await _db_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id    INTEGER,
            message_id INTEGER,
            exp_time   DATETIME,
            UNIQUE(chat_id, message_id)
        )
        """
    )
    await _db_conn.commit()
    logger.info("Autodelete SQLite DB initialized.")


async def insert_autodel(data: AutodelData, seconds: int) -> None:
    if _db_conn is None:
        return
    exp_time = datetime.utcnow() + timedelta(seconds=seconds)
    try:
        await _db_conn.execute(
            """
            INSERT INTO cache (chat_id, message_id, exp_time)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id, message_id)
            DO UPDATE SET exp_time = excluded.exp_time
            """,
            (data.chat_id, data.message_id, exp_time.isoformat()),
        )
        await _db_conn.commit()
    except Exception as e:
        logger.error("insert_autodel: %s", e)


# ── Background ticker ──────────────────────────────────────────────────────────
async def run_autodel(bot: Bot) -> None:
    """Runs every 60 s and deletes messages whose exp_time has passed."""
    if _db_conn is None:
        logger.warning("Autodelete DB not initialized; skipping runner.")
        return

    while True:
        await asyncio.sleep(60)
        now = datetime.utcnow().isoformat()
        try:
            async with _db_conn.execute(
                "SELECT chat_id, message_id FROM cache WHERE exp_time <= ?", (now,)
            ) as cursor:
                rows = await cursor.fetchall()

            for chat_id, message_id in rows:
                try:
                    await bot.delete_message(chat_id, message_id)
                except Exception:
                    pass  # message may already be gone

                try:
                    await _db_conn.execute(
                        "DELETE FROM cache WHERE chat_id = ? AND message_id = ?",
                        (chat_id, message_id),
                    )
                except Exception as e:
                    logger.error("autodel delete row: %s", e)

            await _db_conn.commit()
        except Exception as e:
            logger.error("run_autodel loop: %s", e)
