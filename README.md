# 🐍 PyFilterBot

**Python conversion of [Go-Filter-Bot](https://github.com/Jisin0/Go-Filter-Bot)** — An advanced Telegram filter bot with global filter support.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 Manual Filters | Save keyword→reply pairs per group |
| 🌐 Global Filters | Bot-admin filters that work in ALL groups |
| 🔗 Connections | Manage a group from your PM |
| 📢 Broadcast | Send messages to all users / connected users |
| 🗑️ Auto-Delete | Auto-delete filter replies after N minutes |
| 📎 Media Filters | Filters can contain photos, videos, docs, audio, stickers |
| 🔘 Buttons | URL & Alert buttons in filter replies |
| 📊 Stats | Live user/filter/group counts |

---

## 🚀 Setup

### 1. Clone & install
```bash
git clone <your-repo>
cd PyFilterBot
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.sample .env
# Edit .env with your values
```

### 3. Run
```bash
python main.py
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Your bot token from @BotFather |
| `MONGODB_URI` | ✅ | MongoDB connection string |
| `ADMINS` | ✅ | Space-separated list of admin user IDs |
| `MULTI_FILTER` | ❌ | `true` to send multiple filter results (default: `false`) |
| `AUTO_DELETE` | ❌ | Minutes after which filter replies are deleted (0 = disabled) |
| `PORT` | ❌ | Health-check web server port (default: `10000`) |

---

## 📋 Commands

| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/help` | Help menu |
| `/about` | About the bot |
| `/stats` | Bot statistics |
| `/id` | Get user/chat IDs |
| `/filter <key> <reply>` | Save a manual filter |
| `/gfilter <key> <reply>` | Save a global filter (admins only) |
| `/filters` | List all filters in chat |
| `/gfilters` | List all global filters |
| `/stop <key>` | Stop/delete a filter |
| `/gstop <key>` | Delete a global filter (admins only) |
| `/startglobal <key>` | Re-enable a stopped global filter |
| `/connect [chat_id]` | Connect PM to a group |
| `/disconnect` | Disconnect from current group |
| `/broadcast` | Broadcast to all users (admins only) |
| `/concast` | Broadcast to connected users only (admins only) |

---

## 🐳 Deploy with Docker

```bash
docker build -t pyfilterbot .
docker run --env-file .env pyfilterbot
```

---

## 📦 Tech Stack

- **Python 3.11+**
- **python-telegram-bot v21** (async)
- **MongoDB** via pymongo
- **SQLite** via aiosqlite (for auto-delete)
- **aiohttp** (health-check web server)
