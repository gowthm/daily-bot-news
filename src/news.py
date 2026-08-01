import os

import requests

NEWSAPI_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
NEWSAPI_EVERYTHING_URL = "https://newsapi.org/v2/everything"

USA_ECONOMY_QUERY = (
    '"US dollar" OR "dollar index" OR "Federal Reserve" OR "Fed rate" OR '
    '"US jobs report" OR "nonfarm payrolls" OR "unemployment rate" OR '
    '"US inflation" OR "US economy" OR "US GDP"'
)

OIL_ENERGY_QUERY = (
    '"crude oil" OR OPEC OR "oil prices" OR "oil supply" OR "oil production" OR '
    '"energy market" OR "Brent crude" OR "WTI crude"'
)

GOLD_QUERY = (
    '"gold price" OR "gold demand" OR "central bank gold" OR "gold reserves" OR '
    '"gold ETF" OR "gold rally" OR "gold outlook"'
)

AI_NEWS_QUERY = (
    '"artificial intelligence" OR "AI regulation" OR "AI chips" OR "AI stocks" OR '
    'OpenAI OR Nvidia OR "AI data center" OR "AI investment" OR "AI bubble"'
)


def _fetch_headlines(params: dict) -> list[dict]:
    api_key = os.environ["NEWSAPI_KEY"]
    response = requests.get(
        NEWSAPI_TOP_HEADLINES_URL,
        params={**params, "apiKey": api_key},
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("articles", [])


def _fetch_everything(query: str, page_size: int) -> list[dict]:
    api_key = os.environ["NEWSAPI_KEY"]
    response = requests.get(
        NEWSAPI_EVERYTHING_URL,
        params={
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": api_key,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("articles", [])


def fetch_world_news(page_size: int = 7) -> list[dict]:
    return _fetch_headlines({"language": "en", "pageSize": page_size})


def fetch_india_news(page_size: int = 6) -> list[dict]:
    return _fetch_headlines({"country": "in", "language": "en", "pageSize": page_size})


def fetch_usa_economy_news(page_size: int = 6) -> list[dict]:
    """US dollar, Federal Reserve, jobs report, and broader economy news."""
    return _fetch_everything(USA_ECONOMY_QUERY, page_size)


def fetch_oil_energy_news(page_size: int = 3) -> list[dict]:
    """Crude oil, OPEC, and energy market news."""
    return _fetch_everything(OIL_ENERGY_QUERY, page_size)


def fetch_gold_news(page_size: int = 3) -> list[dict]:
    """Gold-specific news: demand, central bank buying, ETF flows, outlook."""
    return _fetch_everything(GOLD_QUERY, page_size)


def fetch_ai_news(page_size: int = 3) -> list[dict]:
    """USA & world AI industry news: regulation, chips, major AI companies, AI-driven stock moves."""
    return _fetch_everything(AI_NEWS_QUERY, page_size)


def _article_key(article: dict) -> str:
    url = (article.get("url") or "").strip().lower()
    if url:
        return url
    return (article.get("title") or "").strip().lower()


def dedupe_articles(*article_lists: list[dict]) -> list[list[dict]]:
    """Remove articles already seen in an earlier list (by url, falling back to title).

    Category feeds are fetched independently, so the same story can be
    returned by more than one query (e.g. a global top headline that also
    matches the India feed). Keeping it in only its first category stops the
    same story from being repeated across sections of the briefing.
    """
    seen: set[str] = set()
    result = []
    for articles in article_lists:
        deduped = []
        for article in articles:
            key = _article_key(article)
            if key:
                if key in seen:
                    continue
                seen.add(key)
            deduped.append(article)
        result.append(deduped)
    return result


def format_articles(articles: list[dict]) -> str:
    lines = []
    for article in articles:
        title = article.get("title") or ""
        source = (article.get("source") or {}).get("name") or ""
        description = article.get("description") or ""
        lines.append(f"- {title} ({source}): {description}")
    return "\n".join(lines) if lines else "No articles available."
