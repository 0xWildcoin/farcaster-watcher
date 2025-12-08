# Farcaster Watcher 👀
A modular Python bot that monitors new Farcaster casts for a specific user (FID) and sends notifications to Telegram.

## ✨ Features
- Real-time monitoring of Farcaster casts for any FID
- Telegram notifications with nicely formatted messages
- Persistent storage of seen casts (no duplicate notifications)
- Simple, modular codebase (easy to extend)
- Configurable polling interval and history depth via env vars
- .env-based configuration (no secrets in code)
- Ready for running as a systemd service

## 📁 Project Structure
```text
farcaster_watcher/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── storage.py
│   ├── neynar_client.py
│   ├── telegram_client.py
│   └── main.py
├── data/
│   └── seen_casts.json
├── logs/
│   └── .gitkeep
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Neynar API Key
- Telegram Bot Token
- Telegram Chat ID

### 2. Installation
```bash
git clone https://github.com/0xWildcoin/farcaster-watcher.git
cd farcaster-watcher
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
```bash
cp .env.example .env
```

Edit `.env`:
```env
NEYNAR_API_KEY=your_neynar_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
POLL_INTERVAL_SEC=5
LAST_N_CASTS=2
SEEN_FILE=data/seen_casts.json
```

### 4. Running
```bash
python -m main.py
```


## 🔧 Configuration Details

### Environment Variables

| Variable           | Required | Default               | Description                               |
|--------------------|----------|-----------------------|-------------------------------------------|
| `NEYNAR_API_KEY`   | Yes      | —                     | Your Neynar API key                       |
| `TELEGRAM_BOT_TOKEN` | Yes    | —                     | Your Telegram bot token                   |
| `TELEGRAM_CHAT_ID` | Yes      | —                     | Target Telegram chat ID (numeric)         |
| `POLL_INTERVAL_SEC`| No       | `5`                   | Seconds between API checks                |
| `LAST_N_CASTS`     | No       | `2`                   | Number of recent casts to fetch           |
| `SEEN_FILE`        | No       | `data/seen_casts.json`| Path where seen casts are stored          |


## 🐛 Troubleshooting

### ❌ “NEYNAR_API_KEY is not set”

This means the watcher cannot find your environment variable.

**Fix:**

1. Ensure `.env` exists in the project root
2. Confirm it contains:

   ```env
   NEYNAR_API_KEY=your_key_here
   ```

3. Make sure the variable name is **exactly** correct (uppercase, no spaces)
---
### ❌ Telegram messages are not sent

**Checklist:**

- Verify your bot token is valid (`TELEGRAM_BOT_TOKEN`)
- Ensure the bot has been added to the target chat
- If sending to a group, make sure the bot is a **member**
- Double-check `TELEGRAM_CHAT_ID`:
  - It must be a **numeric ID**, not `@username`
  - Group IDs usually start with: `-100...`

👉 To get your chat ID, forward any message from the target chat to **@RawDataBot** on Telegram.


---

### ❌ Bot does not detect new casts

Possible reasons:

- Neynar API rate limits — wait 30–60 seconds and try again
- Incorrect FID entered at startup
- The Farcaster user has no new public casts
- LAST_N_CASTS is too low and the cast was missed (increase it)


## 🤝 Contributing
Fork → Branch → Commit → PR
