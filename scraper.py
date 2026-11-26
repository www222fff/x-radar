"""Search X's latest posts via twscrape (no browser) and extract codes."""
import os
import random
import datetime as dt

from twscrape import API
from extract import extract_codes

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "accounts.db")
SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "").strip()
WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", "30"))
SEARCH_LIMIT_MIN = int(os.environ.get("SEARCH_LIMIT_MIN", "40"))
SEARCH_LIMIT_MAX = int(os.environ.get("SEARCH_LIMIT_MAX", "80"))


async def scrape():
    """Return a list of hits: {code, tweetTime, url, author, text}."""
    if not SEARCH_QUERY:
        raise RuntimeError("SEARCH_QUERY is not set (define it in the profile)")
    api = API(DB_PATH)
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=WINDOW_MINUTES)
    hits = []
    limit = random.randint(SEARCH_LIMIT_MIN, SEARCH_LIMIT_MAX)
    async for tw in api.search(SEARCH_QUERY, limit=limit):
        date = getattr(tw, "date", None)
        # Latest is time-ordered; skip anything older than the window but keep scanning.
        if date and date < cutoff:
            continue
        text = getattr(tw, "rawContent", "") or ""
        user = getattr(tw, "user", None)
        for code in extract_codes(text):
            hits.append({
                "code": code,
                "tweetTime": date.isoformat() if date else None,
                "url": getattr(tw, "url", "") or "",
                "author": ("@" + user.username) if user and getattr(user, "username", None) else "",
                "text": text,
            })
    return hits
