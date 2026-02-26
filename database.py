# database.py - (c) Converted from Go-Filter-Bot by Jisin0

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database as MongoDatabase

import config

logger = logging.getLogger(__name__)

# ── In-memory caches ───────────────────────────────────────────────────────────
_cached_settings: dict[int, "ChatSettings"] = {}
_connection_cache: dict[int, int] = {}  # user_id → chat_id

GLOBAL_FILTER_CHAT_ID: int = 101  # special chat id for global filters


@dataclass
class ChatSettings:
    stopped: list[str] = field(default_factory=list)


@dataclass
class Filter:
    id: str
    chat_id: int
    text: str
    content: str = ""
    file_id: str = ""
    markup: list[list[dict[str, str]]] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    length: int = 0
    media_type: str = ""


@dataclass
class User:
    id: int
    connected_chat: int = 0


# ── Database class ─────────────────────────────────────────────────────────────
class Database:
    def __init__(self) -> None:
        if not config.MONGODB_URI:
            logger.critical("You must set your 'MONGODB_URI' environmental variable :(")
            sys.exit(1)

        self.client: MongoClient = MongoClient(config.MONGODB_URI)
        db: MongoDatabase = self.client["Adv_Auto_Filter"]

        self.db: MongoDatabase = db
        self.ucol: Collection = db["Users"]
        self.col: Collection = db["Main"]
        self.mcol: Collection = db["Manual_Filters"]

    # ── User operations ────────────────────────────────────────────────────────
    def add_user(self, user_id: int) -> None:
        if not self.ucol.find_one({"_id": user_id}):
            try:
                self.ucol.insert_one({"_id": user_id})
            except Exception as e:
                logger.error("db.add_user: %s", e)

    def stats(self) -> str:
        users = self.ucol.count_documents({})
        mfilters = self.mcol.count_documents({})
        chats = self.col.count_documents({})
        return (
            f"╭ ▸ <b>Users</b> : <code>{users}</code> \n"
            f"├ ▸ <b>Filters</b> : <code>{mfilters}</code>\n"
            f"╰ ▸ <b>Groups</b> : <code>{chats}</code>"
        )

    # ── Connection operations ──────────────────────────────────────────────────
    def get_connection(self, user_id: int) -> tuple[int, bool]:
        if user_id in _connection_cache:
            c = _connection_cache[user_id]
            return c, c != 0

        doc = self.ucol.find_one({"_id": user_id})
        if not doc:
            _connection_cache[user_id] = 0
            return 0, False

        connected = doc.get("connected", 0)
        _connection_cache[user_id] = connected
        return connected, connected != 0

    def connect_user(self, user_id: int, chat_id: int) -> None:
        try:
            self.ucol.update_one(
                {"_id": user_id},
                {"$set": {"connected": chat_id}},
                upsert=True,
            )
        except Exception as e:
            logger.error("db.connect_user: %s", e)
        _connection_cache.pop(user_id, None)

    def delete_connection(self, user_id: int) -> None:
        try:
            self.ucol.update_one({"_id": user_id}, {"$unset": {"connected": ""}})
        except Exception as e:
            logger.error("db.delete_connection: %s", e)
        _connection_cache.pop(user_id, None)

    # ── Manual filter operations ───────────────────────────────────────────────
    def save_mfilter(self, f: Filter) -> None:
        doc = {
            "_id": f.id,
            "group_id": f.chat_id,
            "text": f.text,
            "content": f.content,
            "file": f.file_id,
            "button": f.markup,
            "alert": f.alerts,
            "length": f.length,
            "mediaType": f.media_type,
        }
        try:
            self.mcol.insert_one(doc)
        except Exception as e:
            logger.error("db.save_mfilter: %s", e)

    def get_mfilter(self, chat_id: int, key: str) -> tuple[Optional[dict], bool]:
        doc = self.mcol.find_one({"group_id": chat_id, "text": key})
        if doc:
            return doc, True
        return None, False

    def delete_mfilter(self, chat_id: int, key: str) -> None:
        try:
            self.mcol.delete_one({"group_id": chat_id, "text": key})
        except Exception as e:
            logger.error("db.delete_mfilter: %s", e)

    def get_mfilters(self, chat_id: int) -> list[dict]:
        pipeline = [
            {"$match": {"group_id": chat_id}},
            {"$sort": {"length": -1}},
        ]
        return list(self.mcol.aggregate(pipeline))

    def string_mfilter(self, chat_id: int) -> str:
        docs = self.get_mfilters(chat_id)
        return "".join(f"\n• <code>{d.get('text', '')}</code>" for d in docs)

    def search_mfilter_classic(self, chat_id: int, input_text: str) -> list[Filter]:
        """Fetch all filters for chat and do regex matching locally."""
        results: list[Filter] = []
        docs = self.get_mfilters(chat_id)

        for doc in docs:
            text = doc.get("text", "")
            pattern = re.compile(r"(?i)( |^|[^\w])" + re.escape(text) + r"( |$|[^\w])")
            if pattern.search(input_text):
                results.append(_doc_to_filter(doc))

        return results

    def search_mfilter_new(
        self, chat_id: int, fields: list[str], multi_filter: bool
    ) -> list[Filter]:
        """Push regex query to MongoDB."""
        if not fields:
            return []

        escaped = [re.escape(f) for f in fields]
        pattern = "(?i).*\\b(" + "|".join(escaped) + ")\\b.*"

        mongo_filter = {"group_id": chat_id, "text": {"$regex": pattern}}

        if not multi_filter:
            doc = self.mcol.find_one(mongo_filter)
            if doc:
                return [_doc_to_filter(doc)]
            return []

        docs = list(self.mcol.find(mongo_filter).sort("length", -1))
        return [_doc_to_filter(d) for d in docs]

    # ── Global filter / chat settings ─────────────────────────────────────────
    def get_cached_setting(self, chat_id: int) -> ChatSettings:
        if chat_id not in _cached_settings:
            self.recache_settings(chat_id)
        return _cached_settings.get(chat_id, ChatSettings())

    def recache_settings(self, chat_id: int) -> None:
        doc = self.col.find_one({"_id": chat_id})
        if not doc:
            _cached_settings[chat_id] = ChatSettings()
        else:
            _cached_settings[chat_id] = ChatSettings(
                stopped=doc.get("stopped", [])
            )

    def set_default_settings(self, chat_id: int) -> None:
        if not self.col.find_one({"_id": chat_id}):
            try:
                self.col.insert_one({"_id": chat_id})
            except Exception:
                pass

    def set_chat_setting(self, chat_id: int, key: str, value: Any) -> None:
        self.set_default_settings(chat_id)
        try:
            self.col.update_one({"_id": chat_id}, {"$set": {key: value}})
        except Exception as e:
            logger.error("db.set_chat_setting: %s", e)
        self.recache_settings(chat_id)

    def stop_gfilter(self, chat_id: int, key: str) -> None:
        try:
            self.col.update_one(
                {"_id": chat_id},
                {"$addToSet": {"stopped": key}},
                upsert=True,
            )
        except Exception as e:
            logger.error("db.stop_gfilter: %s", e)
        self.recache_settings(chat_id)

    def start_gfilter(self, chat_id: int, key: str) -> None:
        settings = self.get_cached_setting(chat_id)
        new_stopped = [k for k in settings.stopped if k != key]
        try:
            self.col.update_one(
                {"_id": chat_id}, {"$set": {"stopped": new_stopped}}
            )
        except Exception as e:
            logger.error("db.start_gfilter: %s", e)
        self.recache_settings(chat_id)

    def get_alert(self, unique_id: str, index: int) -> str:
        doc = self.mcol.find_one({"_id": unique_id})
        if not doc:
            return "404: Content Not Found !"
        alerts = doc.get("alert", [])
        if index >= len(alerts):
            return "404: Content Not Found !"
        return alerts[index]


# ── Helper ─────────────────────────────────────────────────────────────────────
def _doc_to_filter(doc: dict) -> Filter:
    return Filter(
        id=str(doc.get("_id", "")),
        chat_id=doc.get("group_id", 0),
        text=doc.get("text", ""),
        content=doc.get("content", ""),
        file_id=doc.get("file", ""),
        markup=doc.get("button", []),
        alerts=doc.get("alert", []),
        length=doc.get("length", 0),
        media_type=doc.get("mediaType", ""),
    )


# ── Singleton ──────────────────────────────────────────────────────────────────
_db_instance: Optional[Database] = None


def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
