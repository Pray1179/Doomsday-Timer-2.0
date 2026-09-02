#!/usr/bin/env python3
"""Fetch faction background images for the homepage hero.

For each faction, search Wikimedia Commons for a wide (landscape) image of the
team/theme, prefer a large JPEG/PNG, and save it to assets/img/faction/<key>.jpg.
Images are used under fair-use-for-fan-site / freely-licensed Commons files.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import ssl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "assets", "img", "faction"))

_SSL_CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
_DEFAULT_HEADERS = {
    "User-Agent": "AvengersDoomsdayFanSite/1.0 (contact@example.com)",
    "Accept": "application/json",
}

API = "https://commons.wikimedia.org/w/api.php"
REQUEST_DELAY = 0.4

FACTIONS = [
    # key, search query (team first, then a broad scene term)
    ("avengers", "Avengers Endgame film screenshot team"),
    ("xmen", "X-Men film team group"),
    ("fantastic", "Fantastic Four film team"),
    ("wakandans", "Black Panther film T'Challa Wakanda"),
    ("newavengers", "Doctor Strange film"),
    ("doom", "Doctor Doom Marvel comics villain"),
]


def api(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
        return json.load(r)


def search(filename_query, tries=12):
    """Return a list of (title, width, height, mime) landscape candidates."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {filename_query}",
        "gsrnamespace": "6",
        "gsrlimit": str(tries),
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
    }
    data = api(params)
    pages = (data.get("query") or {}).get("pages", {}) or {}
    out = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < h:                      # skip portrait
            continue
        mime = ii.get("mime", "")
        if mime not in ("image/jpeg", "image/png"):
            continue
        out.append({
            "title": p.get("title"),
            "width": w, "height": h,
            "mime": mime,
            "url": ii.get("url"),
            "descurl": ii.get("descriptionurl"),
        })
    out.sort(key=lambda x: (-x["width"], x["height"]))
    return out


def download(url, dest):
    req = urllib.request.Request(url, headers={
        "User-Agent": _DEFAULT_HEADERS["User-Agent"],
        "Accept": "image/*",
    })
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as r:
        with open(dest, "wb") as f:
            f.write(r.read())


def main():
    os.makedirs(OUT, exist_ok=True)
    for key, query in FACTIONS:
        dest = os.path.join(OUT, f"{key}.jpg")
        picked = None
        # Try a few query variants until we land a landscape image.
        variants = [query]
        # Fall back to just the key term.
        variants.append(key if key != "doom" else "Doctor Doom")
        for q in variants:
            try:
                cands = search(q)
            except Exception as e:
                print(f"[{key}] search '{q}' failed: {e}")
                cands = []
            if cands:
                picked = cands[0]
                break
            print(f"[{key}] no landscape hits for '{q}'")
            time.sleep(REQUEST_DELAY)

        if not picked:
            print(f"[{key}] SKIP - no suitable image found")
            continue
        try:
            download(picked["url"], dest)
            size = os.path.getsize(dest)
            print(f"[{key}] OK  {picked['title']}  {picked['width']}x{picked['height']}  {size//1024}KB")
            with open(os.path.join(OUT, f"{key}.src.txt"), "w") as f:
                f.write(picked["descurl"] + "\n" + picked["title"] + "\n")
        except Exception as e:
            print(f"[{key}] download failed: {e}")
        time.sleep(REQUEST_DELAY)


if __name__ == "__main__":
    main()
