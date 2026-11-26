"""Extract codes/tokens from post text.

Rules come from the environment so each profile can match something different.
Defaults match 5-char codes mixing uppercase letters and digits (e.g. 9XAJP),
which filters out plain words and bare numbers.
"""
import os
import re

CODE_PATTERN = os.environ.get("CODE_PATTERN", r"\b[A-Z0-9]{5}\b")
CODE_UPPERCASE = os.environ.get("CODE_UPPERCASE", "1") == "1"
CODE_REQUIRE_LETTER_AND_DIGIT = os.environ.get("CODE_REQUIRE_LETTER_AND_DIGIT", "1") == "1"
CODE_BLOCKLIST = {
    t.strip().upper()
    for t in os.environ.get("CODE_BLOCKLIST", "HTTPS,HTTP2").split(",")
    if t.strip()
}

CODE_TOKEN = re.compile(CODE_PATTERN)


def is_likely_code(token: str) -> bool:
    if token.upper() in CODE_BLOCKLIST:
        return False
    if CODE_REQUIRE_LETTER_AND_DIGIT:
        return bool(re.search(r"[A-Za-z]", token)) and bool(re.search(r"[0-9]", token))
    return True


def extract_codes(text: str):
    if not text:
        return []
    source = str(text).upper() if CODE_UPPERCASE else str(text)
    found, seen = [], set()
    for match in CODE_TOKEN.finditer(source):
        token = match.group(0)
        if is_likely_code(token) and token not in seen:
            seen.add(token)
            found.append(token)
    return found
