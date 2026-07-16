# daily-news-update

A daily Telegram bot built for a portfolio spanning USA stocks, India stocks, Gold, Silver, Bitcoin, and Bonds. It fetches world, India, USA economy/dollar, oil, gold, and AI news, plus market data (Nifty, Sensex, S&P 500, Nasdaq 100, gold, silver, crude, USD/INR, Bitcoin, US 10Y Treasury yield, global spot gold & silver), asks an LLM to turn it all into a structured morning briefing with a "don't miss this" highlights section and a per-asset investment outlook, and sends it to Telegram. Runs as a GitHub Actions job, triggered by an external cron job — no server to keep running.

## Architecture

- `src/news.py` — fetches world & India headlines, plus dedicated USA dollar/economy, oil & energy, gold, and AI industry feeds, from [NewsAPI](https://newsapi.org)
- `src/market.py` — fetches index/commodity data via `yfinance`, plus the live global spot gold & silver price (XAU/USD, XAG/USD) from [goldprice.org](https://goldprice.org/live-gold-price.html)
- `src/analysis.py` — sends news + market data to an LLM and gets back a formatted briefing. Supports either Anthropic (`claude-sonnet-5` by default, override with `ANTHROPIC_MODEL`) or Groq, switchable via `LLM_PROVIDER`
- `src/telegram_bot.py` — sends the briefing to Telegram (Markdown-formatted, with a plain-text fallback if parsing fails), splitting on the 4096-char message limit
- `main.py` — orchestrates the pipeline; this is what the scheduled job runs
- `.github/workflows/daily-brief.yml` — GitHub Actions workflow, triggered by an external cron job around 7:00 AM IST (via `repository_dispatch`), or manually (`workflow_dispatch`)

## Briefing sections

Kept short on purpose — simple wording for a retail investor, and a strict ~3500-character budget so the whole briefing fits in a single Telegram message instead of being split.

1. **Key Highlights** — the 3 most important items across everything below, flagged if urgent
2. World & India — combined, most market-moving items only
3. Dollar, Oil, Gold & AI — one line each, only if genuinely notable
4. Market Snapshot (Nifty, S&P 500, Nasdaq 100, KOSPI, gold, crude, USD/INR, US 10Y Treasury yield, plus the goldprice.org spot gold line)
5. **What To Do Today** — a directional call (up/down/flat) for USA stocks, India stocks, Gold, Bonds, plus what to watch for

Formatting is Telegram legacy Markdown: section titles are bold, and within bullets a bold sub-label (e.g. `*Gold:*`) precedes the detail — Telegram has no font-size/heading levels, so bold is the only available visual hierarchy.

## Setup

### 1. Create the Telegram bot

Message [@BotFather](https://t.me/BotFather) on Telegram, run `/newbot`, and save the API token. Send the bot a message yourself (or add it as admin to a channel) so it has a chat to post into. To get your chat ID: message your bot once, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and read `message.chat.id` from the JSON — or message [@userinfobot](https://t.me/userinfobot). For a channel, use its `@handle` instead of a numeric ID.

### 2. Get API keys

- **NewsAPI**: free tier at https://newsapi.org (100 requests/day)
- **LLM provider** (pick one, set via `LLM_PROVIDER`):
  - **Anthropic** (default): create a key at https://console.anthropic.com. Measured cost for the full daily briefing (3,100 input / ~1,100 output tokens): **`claude-sonnet-5`** ~$0.017–0.026/day (~$0.50–0.78/month); **`claude-haiku-4-5`** (set `ANTHROPIC_MODEL=claude-haiku-4-5` to switch) ~$0.005/day (~$0.16/month) — cheaper but less nuanced on the gold/stock prediction reasoning.
  - **Groq** (free/cheap testing): create a key at https://console.groq.com/keys

### 3. Configure secrets

**For GitHub Actions (recommended):** in the repo settings, add these under *Settings → Secrets and variables → Actions*:

- `NEWSAPI_KEY`
- `ANTHROPIC_API_KEY` (or `GROQ_API_KEY` + `LLM_PROVIDER=groq`, if testing with Groq)
- `ANTHROPIC_MODEL` (optional, e.g. `claude-haiku-4-5` for lower cost)
- `BOT_TOKEN`
- `CHAT_ID`

This workflow has no built-in schedule — it's triggered by your external cron job hitting the GitHub API (`repository_dispatch`, event type `daily-brief`), targeted for ~7:00 AM IST. It can also be triggered manually from the Actions tab (`workflow_dispatch`).

**For local testing:** copy `.env.example` to `.env` and fill in the same values. `.env` is gitignored — never put real secrets in `.env.example`, since that file is committed.

### 4. Run locally

```bash
pip install -r requirements.txt
python main.py
```

This fetches news + market data, generates the briefing, and sends it to Telegram immediately — useful for testing before relying on the schedule.
