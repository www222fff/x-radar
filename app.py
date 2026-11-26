"""Web UI + background search loop for X Radar."""
import os
import json
import time
import random
import threading
import asyncio
import datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8787"))
HOST = os.environ.get("HOST", "127.0.0.1")
WINDOW_MIN = int(os.environ.get("WINDOW_MINUTES", "30"))
MEDIAN_GAP_SEC = float(os.environ.get("MEDIAN_GAP_SECONDS", "170"))
MIN_GAP_SEC = float(os.environ.get("MIN_GAP_SECONDS", "70"))
MAX_GAP_SEC = float(os.environ.get("MAX_GAP_SECONDS", "480"))
BREAK_CHANCE = float(os.environ.get("BREAK_CHANCE", "0.1"))
QUIET_START_HOUR = int(os.environ.get("QUIET_START_HOUR", "1"))
QUIET_END_HOUR = int(os.environ.get("QUIET_END_HOUR", "8"))
LOCAL_TZ = dt.timezone(dt.timedelta(hours=8))
PAGE_REFRESH_SEC = 30
PAGE_TITLE = os.environ.get("PAGE_TITLE", "X Radar")
PAGE_SUBTITLE = os.environ.get("PAGE_SUBTITLE", "Matches posted on X")
STORE_FILE = os.path.join(BASE, os.environ.get("STORE_FILE", "codes.json"))
INDEX_FILE = os.path.join(BASE, "public", "index.html")

state = {"codes": {}, "lastRun": None, "lastError": None, "nextRun": None}
lock = threading.Lock()


def parse_iso(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def load_store():
    try:
        with open(STORE_FILE, encoding="utf-8") as f:
            for c in json.load(f):
                state["codes"][c["code"]] = c
    except Exception:
        pass


def persist():
    tmp = STORE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(list(state["codes"].values()), f, ensure_ascii=False, indent=2)
    os.replace(tmp, STORE_FILE)


def prune():
    cutoff = time.time() - WINDOW_MIN * 60
    for k in list(state["codes"]):
        ts = parse_iso(state["codes"][k].get("tweetTime") or state["codes"][k].get("firstSeen"))
        if ts and ts < cutoff:
            del state["codes"][k]


def upsert(hits):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    added = 0
    with lock:
        for h in hits:
            c = state["codes"].get(h["code"])
            if c:
                c["lastSeen"] = now
            else:
                state["codes"][h["code"]] = {
                    "code": h["code"], "firstSeen": now, "lastSeen": now,
                    "tweetTime": h.get("tweetTime") or now,
                    "url": h.get("url", ""), "author": h.get("author", ""), "text": h.get("text", ""),
                }
                added += 1
        prune()
        persist()
    return added


def recent():
    with lock:
        prune()
        return sorted(
            state["codes"].values(),
            key=lambda v: parse_iso(v.get("tweetTime") or v.get("firstSeen")) or 0,
            reverse=True,
        )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/codes":
            payload = {
                "title": PAGE_TITLE,
                "subtitle": PAGE_SUBTITLE,
                "windowMinutes": WINDOW_MIN,
                "pageRefreshSeconds": PAGE_REFRESH_SEC,
                "lastRun": state["lastRun"],
                "nextRun": state["nextRun"],
                "lastError": state["lastError"],
                "codes": recent(),
            }
            self._send(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path in ("/", "/index.html"):
            try:
                with open(INDEX_FILE, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except Exception:
                self._send(500, b"index.html missing", "text/plain")
            return
        self._send(404, b"not found", "text/plain")


def next_gap_seconds():
    gap = random.lognormvariate(0, 0.45) * MEDIAN_GAP_SEC
    gap = min(MAX_GAP_SEC, max(MIN_GAP_SEC, gap))
    if random.random() < BREAK_CHANCE:
        gap = random.uniform(480, 1200)
    hour = dt.datetime.now(LOCAL_TZ).hour
    if QUIET_START_HOUR <= hour < QUIET_END_HOUR:
        gap *= random.uniform(2.0, 3.0)
    return gap


def loop():
    from scraper import scrape
    while True:
        try:
            hits = asyncio.run(scrape())
            added = upsert(hits)
            state["lastRun"] = dt.datetime.now(dt.timezone.utc).isoformat()
            state["lastError"] = None
            print(f"[{state['lastRun']}] scraped {len(hits)} hits, {added} new; showing {len(recent())}", flush=True)
        except Exception as e:
            state["lastError"] = str(e)
            print(f"[{dt.datetime.now(dt.timezone.utc).isoformat()}] scrape failed: {e}", flush=True)
        gap = next_gap_seconds()
        state["nextRun"] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=gap)).isoformat()
        print(f"  next scrape in {gap:.0f}s", flush=True)
        time.sleep(gap)


def main():
    load_store()
    if os.environ.get("NO_SCRAPE") != "1":
        threading.Thread(target=loop, daemon=True).start()
    else:
        print("NO_SCRAPE=1: UI only, scraper disabled", flush=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"x-radar [{PAGE_TITLE}] on http://{HOST}:{PORT} (window {WINDOW_MIN}m, median gap ~{MEDIAN_GAP_SEC:.0f}s)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
