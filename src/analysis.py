import os

import anthropic
import requests

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT_TEMPLATE = """You are writing a short daily briefing for a retail (non-expert) investor whose portfolio spans: USA stocks, India stocks, Gold, and Bonds. Write it as a Telegram message.

HARD LIMIT: the entire message, all sections combined, must be under 3500 characters (not words - characters, including spaces and emojis). This is a strict budget because Telegram cuts off longer messages. If you have too much to say, cut less-important items rather than writing longer sentences. Do not pad with filler.

HARD LENGTH CONSTRAINT: The entire message (all sections combined, including emojis and formatting) must be under 4000 characters total. Never satisfy this by omitting a section, dropping a required item, or leaving out something materially important - instead make every bullet as compact as possible (aim for well under 15 words per bullet, no filler words, no repeated context between bullets) so that everything required still fits. If you are running long, tighten wording first, then trim to the low end of each section's bullet-count range - only as a last resort should the least important bullet in the least important section be cut.

Formatting rules (Telegram legacy Markdown, not standard Markdown - there is no font-size or heading-level control, only bold/italic, so use bold and emoji as the visual hierarchy. The reader is a retail investor skimming on a phone, not a professional reading a report - every bullet must be scannable in under 2 seconds):
- Use *single asterisks* around each section title to make it bold - this is the top-level heading.
- Under each section title, use "- " to start every bullet point, one fact/point per line.
- Inside a bullet, when the bullet has a clear sub-topic label (e.g. an asset name, a country, a category), wrap ONLY that label in *single asterisks* followed by a colon - e.g. "- *Gold:* up, driven by a weaker dollar."
- In every bullet that states a market move, level, or outlook (Key Highlights, USA Dollar Tracker, Market Snapshot, Investment Outlook), also bold the single most important word or number in the rest of the sentence (the direction, the % change, or the key figure) - e.g. "- *Gold:* up *1.2%*, driven by a weaker dollar." Bold at most this one extra span per bullet - do not bold entire sentences.
- In those same directional bullets, put a trend emoji right after the bold label, before the rest of the text: 📈 for up/bullish, 📉 for down/bearish, ➡️ for flat/neutral - e.g. "- *Gold:* 📈 up *1.2%*, driven by a weaker dollar." This lets the reader tell direction at a glance without reading the words.
- Keep each bullet to one short, plain-language sentence - avoid jargon a retail investor wouldn't know; if a technical term is necessary, add a 2-4 word plain-language gloss.

Formatting rules (Telegram legacy Markdown - only bold/italic exist, no headings, so bold is the visual hierarchy):
- Use *single asterisks* around EVERY section title, no exceptions, to make it bold - this is the top-level heading and must always stand out.
- Under each section title, use "- " to start every bullet, one point per line.
- Inside a bullet, wrap the sub-topic label in *single asterisks* followed by a colon, e.g. "- *Gold:* ...".
- Then, in the rest of that same bullet, also bold the single most important word or phrase - the actual number, direction (*up*/*down*/*flat*), or key fact - so a reader skimming only the bold words still gets the point, e.g. "- *Gold:* *up 1.2%*, dollar is weaker." Bold at most this one extra phrase per bullet (plus the label) - never bold the whole sentence.

Sections, in this exact order (each title has one leading emoji before the bold text). Keep to the low end of each bullet range to stay inside the character limit:

⭐ *Key Highlights*
- The 3 most important things this investor needs to know today, across all news below. Bold label first ("*IMPORTANT:*" if urgent, otherwise a 1-2 word topic), then also bold the key number/direction in the rest of the line per the rule above - these 3 lines are the most-skimmed part of the whole message, so they must be easy to scan.

🌍 *World & India*
- 3 bullets max, combined, covering the most market-moving world events (USA, China, Russia, South Korea, Japan, Europe) and India events (RBI, budget, sectors). Pick only what actually matters today - skip minor items.

💵 *Dollar, Oil, Gold & AI*
- 1 bullet each (max 4 bullets total) on: US dollar direction, oil/energy, gold demand/outlook, and AI/tech news - only if there's something genuinely notable; skip any with nothing important to say.

📊 *Market Snapshot*
- Compact list, one short line per item, of: Nifty, S&P500, Nasdaq 100, KOSPI, gold, crude oil, USD/INR, US 10-year bond yield. Format as "- *Name:* value/move" with no extra explanation.
- One line with the exact GLOBAL GOLD PRICE value given below, verbatim (price, USD change, percent change).

📈 *What To Do Today*
- One bullet each for USA Stocks, India Stocks, Gold, Bonds: bold label, then up/down/flat and a 3-6 word reason. Then 1 combined "watch for" bullet across India/USA/Global if space allows.

🎯 *Today's Strategy*
- Do NOT combine "what to watch" and "sectors to buy/avoid" into one long sentence - give each its own short bullet point instead of a packed paragraph.
- *India:* what to watch today (one short bullet)
- *India sectors:* buy/avoid sectors (one short bullet)
- *USA:* S&P500/Nasdaq outlook (one short bullet)
- *USA sectors:* key sectors to watch (one short bullet)
- *Global:* China, Russia, South Korea, Europe signals (one short bullet, split into two if needed)

Be concise, factual, and actionable. No financial advice disclaimer needed. Every section title starts with one leading emoji. Inside bullets, the only emoji allowed is the single trend emoji (📈/📉/➡️) on directional bullets as described above - do not add other decorative emojis inside bullets.

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
