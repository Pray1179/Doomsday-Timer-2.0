#!/usr/bin/env python3
"""Fetch Wikipedia poster thumbnails for all MCU films and announced titles."""
import json
import ssl
import time
import urllib.request
import urllib.parse
import sys
from pathlib import Path

# macOS Python sometimes can't find its CA bundle; build an unverified context.
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

ROOT = Path("/Users/praty/HackClaude/avengers-doomsday")
MCU = ROOT / "data" / "mcu.json"

# Map film titles to Wikipedia article names (where they differ)
TITLE_MAP = {
    "Marvel's The Avengers": "The Avengers (2012 film)",
    "Avengers: Age of Ultron": "Avengers: Age of Ultron",
    "Avengers: Infinity War": "Avengers: Infinity War",
    "Avengers: Endgame": "Avengers: Endgame",
    "Avengers: Doomsday": "Avengers: Doomsday",
    "Avengers: Secret Wars": "Avengers: Secret Wars",
    "Captain America: The First Avenger": "Captain America: The First Avenger",
    "Captain America: The Winter Soldier": "Captain America: The Winter Soldier",
    "Captain America: Civil War": "Captain America: Civil War",
    "Captain America: Brave New World": "Captain America: Brave New World",
    "Spider-Man: Homecoming": "Spider-Man: Homecoming",
    "Spider-Man: Far From Home": "Spider-Man: Far From Home",
    "Spider-Man: No Way Home": "Spider-Man: No Way Home",
    "Spider-Man: Brand New Day": "Spider-Man: Brand New Day",
    "Ant-Man and the Wasp: Quantumania": "Ant-Man and the Wasp: Quantumania",
    "The Fantastic Four: First Steps": "The Fantastic Four: First Steps",
    "Doctor Strange in the Multiverse of Madness": "Doctor Strange in the Multiverse of Madness",
    "Thor: The Dark World": "Thor: The Dark World",
    "Thor: Ragnarok": "Thor: Ragnarok",
    "Thor: Love and Thunder": "Thor: Love and Thunder",
    "Iron Man": "Iron Man",
    "Iron Man 2": "Iron Man 2",
    "Iron Man 3": "Iron Man 3",
    "The Incredible Hulk": "The Incredible Hulk (film)",
    "Black Panther": "Black Panther (film)",
    "Black Widow": "Black Widow (2021 film)",
    "Black Panther: Wakanda Forever": "Black Panther: Wakanda Forever",
    "Guardians of the Galaxy": "Guardians of the Galaxy (film)",
    "Guardians of the Galaxy Vol. 2": "Guardians of the Galaxy Vol. 2",
    "Guardians of the Galaxy Vol. 3": "Guardians of the Galaxy Vol. 3",
    "Shang-Chi and the Legend of the Ten Rings": "Shang-Chi and the Legend of the Ten Rings",
    "Eternals": "Eternals (film)",
    "Doctor Strange": "Doctor Strange (2016 film)",
    "Ant-Man": "Ant-Man (film)",
    "Ant-Man and the Wasp": "Ant-Man and the Wasp",
    "Captain Marvel": "Captain Marvel (film)",
    "Deadpool & Wolverine": "Deadpool & Wolverine",
    "The Marvels": "The Marvels (film)",
    "Thunderbolts*": "Thunderbolts* (film)",
    "Blade": "Blade (upcoming film)",
}


def fetch_poster(title, retries=3):
    """Fetch Wikipedia page summary, extract thumbnail URL."""
    wiki_title = TITLE_MAP.get(title, title)
    encoded = urllib.parse.quote(wiki_title.replace(" ", "_"), safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "avengers-doomsday-fan-site/1.0"})
            with urllib.request.urlopen(req, timeout=15, context=_CTX) as resp:
                data = json.loads(resp.read())
                if "thumbnail" in data and "source" in data["thumbnail"]:
                    return data["thumbnail"]["source"]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
            else:
                print(f"  FAILED: {title} -> {wiki_title}: {e}", file=sys.stderr)
    return None


def main():
    mcu = json.loads(MCU.read_text())
    updated = 0
    failed = 0

    for m in mcu["movies"]:
        if m.get("poster_url"):
            updated += 1
            continue
        poster = fetch_poster(m["title"])
        if poster:
            m["poster_url"] = poster
            updated += 1
            print(f"  OK {m['title']}")
        else:
            failed += 1
            print(f"  FAIL {m['title']}")
        time.sleep(2)

    for a in mcu["announced"]:
        if a.get("poster_url"):
            updated += 1
            continue
        poster = fetch_poster(a["title"])
        if poster:
            a["poster_url"] = poster
            updated += 1
            print(f"  OK {a['title']} (announced)")
        else:
            failed += 1
            print(f"  FAIL {a['title']} (announced)")
        time.sleep(2)

    MCU.write_text(json.dumps(mcu, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nDone: {updated} updated, {failed} failed")


if __name__ == "__main__":
    main()
