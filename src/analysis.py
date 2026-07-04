import os

import anthropic
import requests

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT_TEMPLATE = """You are a financial analyst preparing a personal morning briefing for an investor whose portfolio spans: USA stocks, India stocks, Gold, and Bonds. This briefing directly informs their investment decisions, so do not omit anything materially important from the source data below - if a news item or data point could plausibly move any of those asset classes, it must be reflected somewhere in the briefing.

Generate the briefing as a Telegram message.

Formatting rules (Telegram legacy Markdown, not standard Markdown - there is no font-size or heading-level control, only bold/italic, so use bold as the visual hierarchy):
- Use *single asterisks* around each section title to make it bold - this is the top-level heading.
- Under each section title, use "- " to start every bullet point, one fact/point per line.
- Inside a bullet, when the bullet has a clear sub-topic label (e.g. an asset name, a country, a category), wrap ONLY that label in *single asterisks* followed by a colon, then plain text for the rest of the bullet - e.g. "- *Gold:* up, driven by a weaker dollar." This gives a second visual tier (bold label + plain detail) under the bold section title. Do not bold anything else in the sentence.
- Keep each bullet to one short sentence.

Sections, in this exact order (each section title includes one leading emoji before the bold text):

⭐ *Key Highlights*
- The 3-5 single most important, portfolio-moving items across ALL the news and data below - the things this investor absolutely must not miss today. Pull from world, India, USA, oil, gold, and AI-relevant items, whichever matter most today. Start each with a bold label "*IMPORTANT:*" if it is urgent or unusual, otherwise a bold one-or-two-word topic label (e.g. "*Fed:*", "*Oil:*").

🌍 *World News Brief*
- 3-4 bullets on key world events affecting markets, each with a bold topic label. You MUST explicitly check for and include anything material about these major economies, not just generic international headlines: USA, China, Russia, South Korea, Japan, and Europe. If one of them had a notable market-moving event (e.g. "South Korea's KOSPI surged", a China trade move, a Russia sanction/energy story), it must appear here - do not silently drop a major-economy item in favor of a smaller one.

🇮🇳 *India News Brief*
- 3-4 bullets on India-specific events (RBI, budget, geopolitics, sectors), each with a bold topic label

🇺🇸 *USA Economy & Dollar Tracker*
- Bullets summarizing what the US jobs report / unemployment / Fed policy / inflation / GDP news implies for the dollar's direction. State the dollar trend explicitly - strengthening, weakening, or flat, and why. Use a bold label like "*Dollar trend:*" on the summary bullet.

🛢️ *Oil & Energy*
- 2-3 bullets from the OIL & ENERGY NEWS below on crude supply, OPEC decisions, and what it means for oil prices

🥇 *Gold News*
- 2-3 bullets from the GOLD NEWS below on demand, central bank buying, ETF flows, or outlook - distinct from the raw price data in Market Snapshot

🤖 *AI News*
- 2-3 bullets from the AI NEWS below (USA & world) on AI regulation, major AI companies, AI chip makers, and how AI-driven moves affect Nasdaq/tech stocks

📊 *Market Snapshot*
- One bullet per index/commodity from MARKET DATA below (includes Nifty, S&P500, Nasdaq 100, KOSPI, gold futures, crude oil, USD/INR, and the US 10-year Treasury yield), each bullet starting with a bold asset name label, with the move and what it signals
- One additional bullet stating the exact GLOBAL GOLD PRICE value given below verbatim (price, USD change, percent change) - always include this, never omit or paraphrase it away

📈 *Investment Outlook*
- One bullet each, in this exact order, each starting with a bold asset label, giving a directional call (up/down/flat) and the one-line reason tied to the dollar/rate/news/AI backdrop above:
  1. *USA Stocks:* (S&P500 and Nasdaq 100)
  2. *India Stocks:* (Nifty)
  3. *Gold:*
  4. *Bonds:* (US 10-year Treasury yield direction, and what it means for bond prices - yields up means bond prices down, and vice versa)

🎯 *Today's Strategy*
- *India:* what to watch, sectors to buy/avoid
- *USA:* S&P500/Nasdaq outlook, key sectors
- *Global:* China, Russia, South Korea, Europe signals

Be concise, factual, and actionable. No financial advice disclaimer needed. Emojis go ONLY at the very start of each section title, right before the bold text - never inside a bullet.

WORLD NEWS:
{world_news}

INDIA NEWS:
{india_news}

USA ECONOMY & DOLLAR NEWS:
{usa_news}

OIL & ENERGY NEWS:
{oil_news}

GOLD NEWS:
{gold_news}

AI NEWS:
{ai_news}

MARKET DATA:
{market_data}

GLOBAL GOLD PRICE:
{global_gold_price}
"""


def _build_prompt(
    world_news: str,
    india_news: str,
    usa_news: str,
    oil_news: str,
    gold_news: str,
    ai_news: str,
    market_data: str,
    global_gold_price: str,
) -> str:
    return PROMPT_TEMPLATE.format(
        world_news=world_news,
        india_news=india_news,
        usa_news=usa_news,
        oil_news=oil_news,
        gold_news=gold_news,
        ai_news=ai_news,
        market_data=market_data,
        global_gold_price=global_gold_price,
    )


def _generate_with_anthropic(prompt: str) -> str:
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return next(block.text for block in response.content if block.type == "text")


def _generate_with_groq(prompt: str) -> str:
    api_key = os.environ["GROQ_API_KEY"]
    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def generate_briefing(
    world_news: str,
    india_news: str,
    usa_news: str,
    oil_news: str,
    gold_news: str,
    ai_news: str,
    market_data: str,
    global_gold_price: str,
) -> str:
    prompt = _build_prompt(
        world_news, india_news, usa_news, oil_news, gold_news, ai_news, market_data, global_gold_price
    )
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "groq":
        return _generate_with_groq(prompt)
    return _generate_with_anthropic(prompt)
