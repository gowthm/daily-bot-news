from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.analysis import generate_briefing
from src.market import (
    fetch_global_gold_price,
    fetch_market_data,
    format_global_gold_price,
    format_market_data,
)
from src.news import (
    dedupe_articles,
    fetch_ai_news,
    fetch_gold_news,
    fetch_india_news,
    fetch_oil_energy_news,
    fetch_usa_economy_news,
    fetch_world_news,
    format_articles,
)
from src.telegram_bot import send_message


def main() -> None:
    load_dotenv()
    print("Begin")

    world_articles, india_articles, usa_articles, oil_articles, gold_articles, ai_articles = dedupe_articles(
        fetch_world_news(),
        fetch_india_news(),
        fetch_usa_economy_news(),
        fetch_oil_energy_news(),
        fetch_gold_news(),
        fetch_ai_news(),
    )
    world_news = format_articles(world_articles)
    india_news = format_articles(india_articles)
    usa_news = format_articles(usa_articles)
    oil_news = format_articles(oil_articles)
    gold_news = format_articles(gold_articles)
    ai_news = format_articles(ai_articles)
    market_data = format_market_data(fetch_market_data())

    try:
        global_gold_price = format_global_gold_price(fetch_global_gold_price())
    except Exception as exc:
        print(f"Global gold price fetch failed: {exc}")
        global_gold_price = "No global gold price available."

    briefing = generate_briefing(
        world_news, india_news, usa_news, oil_news, gold_news, ai_news, market_data, global_gold_price
    )

    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A, %d %B %Y")
    briefing = f"📅 *Daily Market Briefing - {today} (IST)*\n\n{briefing}"

    send_message(briefing)


if __name__ == "__main__":
    main()
