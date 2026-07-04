import os

import requests

TELEGRAM_MESSAGE_LIMIT = 4000


def send_message(text: str) -> None:
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    for start in range(0, len(text), TELEGRAM_MESSAGE_LIMIT):
        chunk = text[start : start + TELEGRAM_MESSAGE_LIMIT]
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
            timeout=15,
        )
        if response.status_code == 400:
            # Markdown entities didn't parse (e.g. a stray "*") - resend as plain text
            # rather than losing the chunk.
            response = requests.post(url, data={"chat_id": chat_id, "text": chunk}, timeout=15)
        response.raise_for_status()
