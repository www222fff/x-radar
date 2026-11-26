# x-radar

Watch X for posts matching a search, pull out codes or tokens from them, and show the results on a small web page, newest first.

It searches X's latest posts with [twscrape](https://github.com/vladkens/twscrape) (no browser). What to search for and what to extract are set per **profile**, so one install can watch different topics. The included `cue` profile collects Manus Cue invite codes (5 characters mixing uppercase letters and digits, such as `9XAJP`).

## Requirements

- Python 3.10+
- One X account to search with. Use a dedicated account: automated searching can get an account rate-limited or locked.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Add the X account. Copy `account.example.txt` to `account.txt` and fill it in, either with the account's `auth_token` and `ct0` cookies or with username, password, and mailbox IMAP credentials. Then:

```bash
chmod 600 account.txt
python add_account.py
```

`account.txt` and `accounts.db` hold credentials and are gitignored. Never commit them.

## Run

```bash
./run.sh          # uses profiles/cue.env
./run.sh mytopic  # uses profiles/mytopic.env
```

Each profile keeps its own results file (`codes-<profile>.json`). The page is served on `127.0.0.1` at the profile's `PORT`; put it behind a reverse proxy or tunnel if you want it public. To run several profiles at once, give each a different `PORT`.

## Adding a profile

Copy `profiles/cue.env` to `profiles/<name>.env` and edit it:

| Variable | Meaning |
|---|---|
| `PAGE_TITLE` / `PAGE_SUBTITLE` | Text shown on the page |
| `SEARCH_QUERY` | X search query (X search operators work) |
| `CODE_PATTERN` | Regex for what to extract from each post |
| `CODE_UPPERCASE` | `1` to uppercase post text before matching |
| `CODE_REQUIRE_LETTER_AND_DIGIT` | `1` to keep only matches with both a letter and a digit |
| `CODE_BLOCKLIST` | Comma-separated matches to ignore |
| `WINDOW_MINUTES` | How long a result stays listed |
| `PORT` | Web server port |

## Search pacing

Search gaps are randomized so the account doesn't hit X on a fixed rhythm. Optional environment variables (they can go in a profile too):

| Variable | Default | Meaning |
|---|---|---|
| `MEDIAN_GAP_SECONDS` | `170` | Typical gap between searches |
| `MIN_GAP_SECONDS` / `MAX_GAP_SECONDS` | `70` / `480` | Bounds for a normal gap |
| `BREAK_CHANCE` | `0.1` | Chance of an 8–20 minute pause after a search |
| `QUIET_START_HOUR` / `QUIET_END_HOUR` | `1` / `8` | Hours (UTC+8) when gaps are 2–3x longer |
| `SEARCH_LIMIT_MIN` / `SEARCH_LIMIT_MAX` | `40` / `80` | Posts fetched per search, picked at random |
| `NO_SCRAPE` | unset | Set to `1` to serve the page without searching |

## Test

```bash
python test_extract.py
```
