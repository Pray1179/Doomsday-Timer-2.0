#!/usr/bin/env python3
"""
Image fetching pipeline for the Marvel catalogue.
Sources images from Wikipedia/Wikimedia Commons with proper attribution.
Downloads as WebP, updates JSON records.

Run: python3 scripts/fetch_images.py [--dry-run] [--batch BATCH_FILE]
"""
import json
import sys
import os
import time
import argparse
from pathlib import Path
from urllib.parse import quote, urljoin
import urllib.request
import urllib.error
import ssl

_DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) DoomsdayFanHub/1.0 (+https://github.com/praty/avengers-doomsday)"}
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import subprocess

sys.path.insert(0, str(Path(__file__).parent))
import catalogue_util as cu

ROOT = Path(__file__).resolve().parent.parent
CAT_DIR = ROOT / "data" / "catalogue"
IMG_DIR = ROOT / "assets" / "img"

# macOS Python often lacks a bundled CA store; use the system bundle so
# https requests to upload.wikimedia.org / en.wikipedia.org verify cleanly.
_SSL_CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem") \
    if os.path.exists("/etc/ssl/cert.pem") else ssl.create_default_context()

# Rate limiting: Wikipedia API allows ~50 req/s, be respectful
REQUEST_DELAY = 0.1  # seconds between requests
MAX_WORKERS = 3  # concurrent downloads

WIKIMEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIMEDIA_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# --- Search Strategies ---
# For each character, we try multiple search approaches

def search_wikimedia_image(name, aliases, portrayed_by, debut_title):
    """Search Wikimedia Commons for a character image.
    Returns (image_url, image_page_url, alt_text) or (None, None, None).
    """
    # Build search queries in priority order — prioritize MCU actor photos
    queries = []

    # 1. Actor + character (best for MCU live-action)
    if portrayed_by:
        queries.append(f"{portrayed_by} as {name}")
        queries.append(f"{portrayed_by} {name}")
        queries.append(f"{portrayed_by} Marvel")

    # 2. Character + MCU specific
    queries.append(f"{name} Marvel Cinematic Universe")
    queries.append(f"{name} MCU")

    # 3. Character name (generic)
    queries.append(name)

    # 4. Alias if different
    for alias in aliases or []:
        if alias.lower() != name.lower():
            queries.append(alias)
            queries.append(f"{alias} Marvel")

    # 5. Debut title + character
    if debut_title:
        queries.append(f"{debut_title} {name}")

    for q in queries:
        url = f"{WIKIMEDIA_API}?action=query&list=search&srsearch={quote(q)}&srnamespace=6&srlimit=5&format=json"
        try:
            req = urllib.request.Request(url, headers=_DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
                data = json.load(resp)
        except Exception as e:
            print(f"  Search failed for '{q}': {e}")
            continue

        for result in data.get("query", {}).get("search", []):
            title = result["title"]  # e.g., "File:Benedict_Cumberbatch_as_Doctor_Strange.jpg"
            if not title.startswith("File:"):
                continue

            # Relevance: skip results that clearly don't match the actor/character
            title_lower = title.lower()
            name_lower = name.lower()
            # If we have an actor, prefer files that contain their name
            if portrayed_by:
                actor_last = portrayed_by.split()[-1].lower()
                if actor_last not in title_lower and name_lower.replace(" ", "_") not in title_lower:
                    # only skip if neither actor nor character name appears
                    name_tokens = name_lower.replace("(", "").replace(")", "").split()
                    if not any(tok in title_lower for tok in name_tokens if len(tok) > 3):
                        continue

            # Get image info
            info_url = f"{WIKIMEDIA_API}?action=query&titles={quote(title)}&prop=imageinfo&iiprop=url|extmetadata&iiextmetadatalanguage=en&format=json"
            try:
                req2 = urllib.request.Request(info_url, headers=_DEFAULT_HEADERS)
                with urllib.request.urlopen(req2, timeout=10, context=_SSL_CTX) as resp:
                    info_data = json.load(resp)
            except Exception:
                continue

            pages = info_data.get("query", {}).get("pages", {})
            for page in pages.values():
                ii = page.get("imageinfo", [{}])[0]
                img_url = ii.get("url")
                if not img_url:
                    continue

                # Prefer higher quality images
                if any(x in img_url.lower() for x in [".svg", "thumb"]):
                    continue

                # Alt text from metadata or fallback (strip HTML tags)
                alt = ii.get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
                if alt:
                    import re
                    alt = re.sub(r'<[^>]+>', '', alt).strip()
                if not alt:
                    alt = f"{name} portrait"

                # Source page URL
                source_page = f"https://en.wikipedia.org/wiki/{quote(title.replace('File:', ''))}"

                return img_url, source_page, alt

        time.sleep(REQUEST_DELAY)

    return None, None, None


def search_wikipedia_summary(name, portrayed_by):
    """Use Wikipedia REST API summary to find image."""
    # Try direct page
    for title in [name, f"{name} (Marvel Cinematic Universe)", f"{name} (character)"]:
        url = f"{WIKIMEDIA_REST}{quote(title)}"
        try:
            req = urllib.request.Request(url, headers=_DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            continue
        except Exception:
            continue

        thumb = data.get("thumbnail", {}).get("source")
        if thumb:
            # Convert thumbnail to full image if possible
            # For now use thumb but mark as verified
            page_url = f"https://en.wikipedia.org/wiki/{quote(title)}"
            alt = data.get("description", f"{name} portrait")
            return thumb, page_url, alt

        time.sleep(REQUEST_DELAY)

    return None, None, None


def download_image(url, cid):
    """Download an image, save under assets/img/cat-<cid>.<ext>.

    Returns the relative URL to use (../assets/img/cat-<cid>.<ext>) or None on
    failure. Preserves the original format (jpg/png/webp) since Pillow/webp
    conversion is not guaranteed to be available.
    """
    try:
        req = urllib.request.Request(url, headers=_DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as resp:
            data = resp.read()

        # Detect extension from URL path or content-type
        path_lower = url.split("?")[0].lower()
        ext = ""
        for cand in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            if "." + cand.lstrip(".") in path_lower:
                ext = cand if cand != ".jpeg" else ".jpg"
                break
        if not ext:
            ctype = (resp.headers.get("Content-Type") or "")
            ext = {".image/jpeg": ".jpg", ".image/png": ".png",
                   ".image/webp": ".webp"}.get(ctype, ".jpg")
        if not ext:
            ext = ".jpg"

        if not data:
            return None

        local_name = f"cat-{cid}{ext}"
        local_path = IMG_DIR / local_name
        local_path.write_bytes(data)
        return f"../assets/img/{local_name}"
    except Exception as e:
        print(f"  Download failed: {e}")
        return None


def process_character(record, dry_run=False):
    """Process a single character record."""
    cid = record["id"]
    name = record["name"]
    alias = record["alias"]
    aliases = record.get("aliases", [])
    portrayed = record.get("portrayed_by", "")
    debut = record.get("debut_title", "")

    # Skip if already verified
    if record.get("image_verified") and record.get("image_url"):
        return False, "already verified"

    # Skip if comics-only (no live-action portrayal)
    # Heuristic: no portrayed_by or known comic-only continuities
    continuity = record.get("continuity", "")
    comic_only = ["Howard the Duck (1986)", "Captain America (1990)", "Man-Thing (2005)", "Nick Fury: Agent of S.H.I.E.L.D."]
    if continuity in comic_only and not portrayed:
        return False, "comic-only, no actor"

    print(f"[{cid}] {name} ({continuity}) - {portrayed or 'no actor'}")

    # Try Wikimedia Commons search first (best quality)
    img_url, source_url, alt = search_wikimedia_image(name, aliases, portrayed, debut)
    source = "Wikimedia Commons"

    # Fallback to Wikipedia summary
    if not img_url:
        img_url, source_url, alt = search_wikipedia_summary(name, portrayed)
        source = "Wikipedia"

    if not img_url:
        return False, "no image found"

    # Determine local filename
    ext = ".webp"
    local_name = f"cat-{cid}{ext}"
    local_path = IMG_DIR / local_name
    local_url = f"../assets/img/{local_name}"

    if dry_run:
        print(f"  Found: {img_url}")
        print(f"  Source: {source_url} ({source})")
        print(f"  Alt: {alt[:120] if alt else ''}")
        print(f"  Would save to: ../assets/img/cat-{cid}.<ext>")
        return True, "dry-run"

    # Download
    local_url = download_image(img_url, cid)
    if local_url:
        # Update record
        record["image_url"] = local_url
        record["image_source_url"] = source_url
        record["image_source_name"] = source
        record["image_alt"] = alt
        record["image_verified"] = True
        print(f"  ✓ Saved to {local_url}")
        return True, "updated"
    else:
        return False, "download failed"


def load_all_records():
    """Load all catalogue records from batch files."""
    records = []
    batch_files = sorted(CAT_DIR.glob("*.json"))
    for bf in batch_files:
        if bf.name == "_README.md":
            continue
        with bf.open(encoding="utf-8") as f:
            doc = json.load(f)
        recs = doc.get("characters") if isinstance(doc, dict) else doc
        for r in recs:
            r["_batch_file"] = bf.name
            records.append(r)
    return records, batch_files


def save_batch_file(batch_file, records):
    """Save records back to their batch file, preserving structure."""
    # Group by batch
    by_batch = {}
    for r in records:
        bn = r.pop("_batch_file", None)
        if bn:
            by_batch.setdefault(bn, []).append(r)

    for bn, recs in by_batch.items():
        bf = CAT_DIR / bn
        with bf.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        # Preserve top-level structure
        if isinstance(doc, dict) and "characters" in doc:
            doc["characters"] = recs
            out = doc
        else:
            out = recs
        with bf.open("w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
            f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Fetch character images from Wikipedia/Wikimedia")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fetched without downloading")
    parser.add_argument("--batch", help="Process only one batch file (e.g., 'mcu-avengers.json')")
    parser.add_argument("--limit", type=int, help="Max records to process")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Parallel workers")
    args = parser.parse_args()

    records, batch_files = load_all_records()
    print(f"Loaded {len(records)} records from {len(batch_files)} batch files")

    # Filter
    if args.batch:
        records = [r for r in records if r["_batch_file"] == args.batch]
        print(f"Filtered to batch '{args.batch}': {len(records)} records")

    pending = [r for r in records if not r.get("image_verified")]
    print(f"Pending verification: {len(pending)}")

    if args.limit:
        pending = pending[:args.limit]
        print(f"Limited to first {args.limit}")

    updated = 0
    failed = 0

    if args.workers > 1:
        # Parallel with rate limiting
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process_character, r, args.dry_run): r for r in pending}
            for fut in as_completed(futures):
                r = futures[fut]
                try:
                    ok, msg = fut.result()
                    if ok:
                        updated += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"  Error on {r['id']}: {e}")
                    failed += 1
    else:
        for r in pending:
            ok, msg = process_character(r, args.dry_run)
            if ok:
                updated += 1
            else:
                failed += 1
            time.sleep(REQUEST_DELAY)

    if not args.dry_run and updated > 0:
        save_batch_file(batch_files, records)
        print(f"\nSaved {updated} updated records to batch files")

    print(f"\nDone. Updated: {updated}, Failed/Skipped: {failed}")


if __name__ == "__main__":
    main()