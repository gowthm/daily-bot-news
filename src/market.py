import cloudscraper
import yfinance as yf

TICKERS = {
    "Nifty50": "^NSEI",
    "S&P500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "KOSPI": "^KS11",
    "Gold Futures": "GC=F",
    "Crude Oil": "CL=F",
    "USD/INR": "INR=X",
    "US 10Y Treasury Yield": "^TNX",
}

# How to display each ticker's price, so USD-denominated USA assets are never ambiguous.
TICKER_DISPLAY = {
    "Nifty50": "{price} pts",
    "S&P500": "${price}",
    "Nasdaq 100": "${price}",
    "KOSPI": "{price} pts",
    "Gold Futures": "${price}/oz",
    "Crude Oil": "${price}/bbl",
    "USD/INR": "₹{price} per $1",
    "US 10Y Treasury Yield": "{price}%",
}

# goldprice.org's live-price feed (same JSON the live-gold-price.html page renders from).
GOLD_PRICE_URL = "https://data-asg.goldprice.org/dbXRates/USD"


def fetch_market_data() -> dict[str, dict[str, float]]:
    data = {}
    for name, symbol in TICKERS.items():
        history = yf.Ticker(symbol).history(period="2d")
        if len(history) < 2:
            continue
        prev_close = history["Close"].iloc[-2]
        curr_close = history["Close"].iloc[-1]
        pct_change = ((curr_close - prev_close) / prev_close) * 100
        data[name] = {"price": round(float(curr_close), 2), "change_pct": round(float(pct_change), 2)}
    return data


def format_market_data(data: dict[str, dict[str, float]]) -> str:
    lines = []
    for name, values in data.items():
        display = TICKER_DISPLAY.get(name, "{price}").format(price=values["price"])
        lines.append(f"- {name}: {display} ({values['change_pct']:+.2f}%)")
    return "\n".join(lines) if lines else "No market data available."


def fetch_global_gold_price() -> dict[str, float]:
    """Live spot gold price (XAU/USD per troy oz) from goldprice.org."""
    scraper = cloudscraper.create_scraper()
    response = scraper.get(GOLD_PRICE_URL, timeout=20, headers={"Referer": "https://goldprice.org/"})
    response.raise_for_status()
    item = response.json()["items"][0]
    return {
        "price_usd_per_oz": round(item["xauPrice"], 2),
        "change_usd": round(item["chgXau"], 2),
        "change_pct": round(item["pcXau"], 2),
    }


def format_global_gold_price(data: dict[str, float]) -> str:
    if not data:
        return "No global gold price available."
    return (
        f"- Global Spot Gold (XAU/USD, goldprice.org): ${data['price_usd_per_oz']}/oz "
        f"({data['change_usd']:+.2f} USD, {data['change_pct']:+.2f}%)"
    )
