"""
Fetches live Codeforces stats and rewrites the block between
<!--CF_STATS:START--> and <!--CF_STATS:END--> markers in README.md.

Run locally for testing:
    CF_HANDLE=your_handle python scripts/update_stats.py

In CI, CF_HANDLE is read from a repo secret (see update-stats.yml).
"""

import datetime
import json
import os
import re
import sys
import urllib.request

START_MARKER = "<!--CF_STATS:START-->"
END_MARKER = "<!--CF_STATS:END-->"
README_PATH = "README.md"


def fetch_codeforces(handle: str) -> dict:
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        payload = json.load(resp)
    if payload.get("status") != "OK":
        raise RuntimeError(f"Codeforces API error: {payload}")
    return payload["result"][0]


def build_block(info: dict) -> str:
    rating = info.get("rating", "unrated")
    max_rating = info.get("maxRating", rating)
    rank = str(info.get("rank", "unrated")).title()
    today = datetime.date.today().isoformat()

    rating_badge = (
        f"https://img.shields.io/badge/Codeforces-{rating}_({rank})-000000?style=flat-square"
    )
    peak_badge = f"https://img.shields.io/badge/Peak-{max_rating}-000000?style=flat-square"

    return (
        f"{START_MARKER}\n"
        f"![Codeforces Rating]({rating_badge})\n"
        f"![Peak Rating]({peak_badge})\n"
        f"<sub>Last synced {today} UTC via GitHub Actions</sub>\n"
        f"{END_MARKER}"
    )


def main() -> None:
    handle = os.environ.get("CF_HANDLE", "").strip()
    if not handle:
        print("CF_HANDLE is not set — skipping update.")
        sys.exit(0)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    info = fetch_codeforces(handle)
    block = build_block(info)

    pattern = re.compile(re.escape(START_MARKER) + ".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(content):
        print("Markers not found in README.md — nothing updated.")
        sys.exit(0)

    new_content = pattern.sub(block, content)
    if new_content != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md updated.")
    else:
        print("No change in stats — README.md left as is.")


if __name__ == "__main__":
    main()
