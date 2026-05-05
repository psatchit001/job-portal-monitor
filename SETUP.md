# Career Portal Monitor — Setup Guide

## One-time setup (do this once)

### 1. Install Python dependencies
```
pip install -r requirements.txt
```

### 2. Install Playwright browsers
```
playwright install chromium
```

### 3. Configure your settings
```
copy .env.example .env
```
Open `.env` and fill in:
- `DISCORD_WEBHOOK_URL` — paste your Discord webhook URL here
- `MATCHER_BACKEND` — `local` (free, offline) or `openai` (better quality, needs API key)
- `OPENAI_API_KEY` — only needed if MATCHER_BACKEND=openai

### 4. First run
```
python run.py
```
Open your browser at: **http://localhost:8000**

Click **▶ Run Now** in the dashboard to trigger the first scrape immediately.

---

## How to get a Discord webhook URL
1. Open Discord → your server → any channel
2. Click the gear icon (Edit Channel) → Integrations → Webhooks
3. Click **New Webhook** → give it a name → **Copy Webhook URL**
4. Paste it into `.env` as `DISCORD_WEBHOOK_URL`

---

## Switching between semantic matchers

In `.env`:
```
# Free, runs offline, ~420MB download on first run
MATCHER_BACKEND=local

# OpenAI API, better quality, costs ~$0.001/day
MATCHER_BACKEND=openai
OPENAI_API_KEY=sk-...
```
Restart the app after changing.

---

## Running automatically in the background (Windows)

The app already checks for new jobs every 3 hours while it's running.
To have it start automatically with Windows:

1. Press `Win + R` → type `shell:startup` → press Enter
2. Create a `.bat` file in that folder:
```bat
@echo off
cd /d "C:\Users\Pavithraa S\OneDrive\Documents\Claude_Code_Apps\career_portal_monitor"
python run.py
```
3. The monitor will start automatically when you log in.

---

## Adding more companies

1. Open `app/database.py` and add an entry to the `COMPANIES` list
2. Create a new scraper in `app/scrapers/companies/your_company.py`
   (copy an existing one as a template)
3. Import and add it to `SCRAPERS` in `app/scrapers/runner.py`

---

## Adjusting match sensitivity

In `.env`:
```
MATCH_THRESHOLD=0.30   # broader net (more results)
MATCH_THRESHOLD=0.45   # tighter match (fewer, higher quality results)
```
