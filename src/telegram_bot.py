import os

import requests

TELEGRAM_MESSAGE_LIMIT = 4000


def _split_into_chunks(text: str, limit: int) -> list[str]:
    """Split text into chunks without breaking a line in the middle.

    Splitting on a raw character offset can land inside a *bold* span,
    leaving one chunk with an unbalanced asterisk - Telegram then rejects
    that chunk's Markdown (400) and it falls back to plain text, so the
    formatting silently breaks for that chunk only. Keeping whole lines
    together avoids ever cutting through a markdown entity.
    """
    lines = text.split("\n")
    chunks = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(line) <= limit:
            current = line
        else:
            for start in range(0, len(line), limit):
                chunks.append(line[start : start + limit])
            current = ""
    if current:
        chunks.append(current)
    return chunks


def send_message(text: str) -> None:
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    for chunk in _split_into_chunks(text, TELEGRAM_MESSAGE_LIMIT):
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
