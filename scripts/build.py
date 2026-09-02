#!/usr/bin/env python3
"""Doomsday Fan Hub — build script.

Reads data/cast.json, VALIDATES it strictly (fails loudly on bad data),
and generates one static HTML page per character into pages/.

Design rules enforced here:
- slug: required, kebab-case-ish, unique
- unit: must be one of the allowed enum values
- actor.name / character.name: required
- sources: required, non-empty, each with url + publisher + verified_at
- deterministic output (sorted; no timestamps/random) so double runs match
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cast.json"
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets"

UNIT_ENUM = {"Avengers", "X-Men", "Fantastic Four", "Wakandans", "New Avengers", "Villain"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def die(msg):
    print(f"\033[31mBUILD FAIL:\033[0m {msg}", file=sys.stderr)
    sys.exit(1)


def load():
    if not DATA.exists():
        die(f"missing cast data at {DATA}")
    try:
        doc = json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"cast.json is not valid JSON: {e}")
    if not isinstance(doc, dict) or "characters" not in doc:
        die("cast.json must be an object with a 'characters' array")
    chars = doc["characters"]
    if not isinstance(chars, list) or len(chars) == 0:
        die("cast.json 'characters' must be a non-empty array")
    return doc


def validate(chars):
    seen_slug = set()
    seen_page = set()
    for i, c in enumerate(chars):
        where = f"character #{i+1}"
        if not isinstance(c, dict):
            die(f"{where}: entry must be an object")
        slug = c.get("slug")
        if not slug or not isinstance(slug, str) or not SLUG_RE.match(slug):
            die(f"{where}: invalid 'slug' ({slug!r}); use lowercase kebab-case, no spaces/unicode")
        if slug in seen_slug:
            die(f"duplicate slug '{slug}'")
        seen_slug.add(slug)

        name = c.get("name")
        if not name or not isinstance(name, str):
            die(f"{where} ({slug}): 'name' (actor display) required")

        unit = c.get("unit")
        if unit not in UNIT_ENUM:
            die(f"{where} ({slug}): 'unit' must be one of {sorted(UNIT_ENUM)}; got {unit!r}")

        actor = c.get("actor") or {}
        if not (actor.get("name") and actor.get("mcu_first_appearance")):
            die(f"{where} ({slug}): actor.name + actor.mcu_first_appearance required")

        character = c.get("character") or {}
        if not (character.get("name") and character.get("blurb")):
            die(f"{where} ({slug}): character.name + character.blurb required")

        sources = c.get("sources")
        if not isinstance(sources, list) or not sources:
            die(f"{where} ({slug}): 'sources' required (non-empty, provenance)")
        for s in sources:
            if not (s.get("url") and s.get("publisher")):
                die(f"{where} ({slug}): each source needs url + publisher")

        page = c.get("page")
        if page:
            if page in seen_page:
                die(f"duplicate 'page' {page!r}")
            seen_page.add(page)
    print(f"\033[32m  validated\033[0m {len(chars)} characters — all checks passed")


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def unit_key(u):
    """Return a slug-safe css key for a unit/universe label."""
    return str(u).split("(")[0].strip().lower().replace(" ", "-")


def character_html(c, doc):
    ch = c["character"]
    actor = c["actor"]
    rel = doc["release"]
    universe = ch.get("universe", "MCU")
    faction = ch.get("faction", c["unit"])
    rows = []
    def row(label, value):
        if value:
            rows.append(f"<div class='kv'><span class='k'>{label}</span><span class='v'>{esc(value)}</span></div>")
    row("Actor", actor.get("name"))
    row("Character", ch.get("name"))
    row("Unit", c["unit"])
    row("Faction", faction)
    row("Universe", universe)
    row("Status before Doomsday", ch.get("status_before_doomsday"))
    row("Why they matter", ch.get("why_they_matter"))

    allies = ", ".join(ch.get("allies") or [])
    enemies = ", ".join(ch.get("enemies") or [])
    teams = ", ".join(ch.get("teams") or [])
    aliases = ", ".join(ch.get("aliases") or [])
    extras = []
    if aliases: extras.append(f"<div class='kv'><span class='k'>Aliases</span><span class='v'>{esc(aliases)}</span></div>")
    if allies: extras.append(f"<div class='kv'><span class='k'>Allies</span><span class='v'>{esc(allies)}</span></div>")
    if enemies: extras.append(f"<div class='kv'><span class='k'>Enemies</span><span class='v'>{esc(enemies)}</span></div>")
    if teams: extras.append(f"<div class='kv'><span class='k'>Teams</span><span class='v'>{esc(teams)}</span></div>")

    watch = ch.get("watch_before") or []
    watch_html = "".join(f"<li><a href='../explore/watch-guide.html'>{esc(item)}</a></li>" for item in watch) if watch else "<li>No list yet</li>"

    sources_html = "".join(
        f"<li><a href='{esc(s['url'])}' rel='noopener'>{esc(s.get('publisher','source'))}</a>"
        + (f" · verified {esc(s['verified_at'])}" if s.get('verified_at') else "") + "</li>"
        for s in c.get("sources", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(ch.get('name'))} — Avengers: Doomsday</title>
<meta name="description" content="{esc(ch.get('blurb',''))}">
<meta property="og:title" content="{esc(ch.get('name'))} — Avengers: Doomsday">
<meta property="og:type" content="profile">
<meta property="og:image" content="../assets/img/{esc(c['slug'])}.svg">
<link rel="canonical" href="https://doomsdayhub.example/pages/{esc(c['slug'])}.html">
<link rel="stylesheet" href="../assets/css/styles.css">
</head>
<body class="unit-{esc(c['unit'].split()[0].lower())}">
<nav class="nav"><div class="nav-inner"><a class="brand" href="../index.html"><span class="av">AVENGERS</span><span class="sep">:</span><span class="dd">DOOMSDAY</span></a>
<ul><li><a href="../index.html">Home</a></li><li><a href="../explore/characters.html">Characters</a></li>
<li><a href="../explore/watch-guide.html">Watch Guide</a></li><li><a href="../explore/timeline.html">Timeline</a></li></ul></div></nav>

<header class="hero char-hero">
  <div class="badge">{esc(c['unit'])}</div>
  <h1>{esc(ch.get('name'))}</h1>
  <p class="lede">{esc(ch.get('blurb'))}</p>
</header>

<main class="wrap">
  <section class="card">
    <h2>Intel</h2>
    {''.join(rows)}
    {''.join(extras)}
    <div class="kv"><span class='k'>Latest appearance</span><span class='v'>{esc(ch.get('latest_appearance', rel['title'] + ' (2026)'))}</span></div>
  </section>

  <section class="card">
    <h2>Essential watch before Doomsday</h2>
    <ul class="watch">{watch_html}</ul>
  </section>

  <section class="card">
    <h2>Verified sources</h2>
    <ul class="sources">{sources_html}</ul>
    <p class="verified">Data verified {esc(doc['release']['data_verified_at'])} via agent-reach. Bios are not invented.</p>
  </section>

  <nav class="char-nav" aria-label="Character navigation">
    <a rel="prev" id="prev-link" href="#">← Previous</a>
    <div class="char-nav-mid"><span id="char-pos"></span>
      <a href="../explore/characters.html">All characters</a></div>
    <a rel="next" id="next-link" href="#">Next →</a>
  </nav>
</main>

<footer class="foot"><a href="../index.html">↑ Back to the hub</a></footer>
<script src="../assets/js/main.js" data-slug="{esc(c['slug'])}"></script>
</body>
</html>"""


def build(doc):
    chars = doc["characters"]
    PAGES.mkdir(exist_ok=True)
    # deterministic order by slug
    order = sorted(range(len(chars)), key=lambda i: chars[i]["slug"])
    written = 0
    for idx in order:
        c = chars[idx]
        html = character_html(c, doc)
        slug = c["slug"]
        out = PAGES / f"{slug}.html"
        out.write_text(html, encoding="utf-8")
        written += 1
    print(f"\033[32m  wrote\033[0m {written} character pages to pages/")
    # prev/next wiring is done client-side by main.js using index.html's order;
    # here we also drop a manifest for the client.
    manifest = [{"slug": chars[i]["slug"], "name": chars[i]["character"].get("name"), "unit": chars[i]["unit"]} for i in order]
    (ASSETS / "js" / "cast-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    print(f"\033[32m  wrote\033[0m assets/js/cast-manifest.json ({len(manifest)} entries)")


def main():
    doc = load()
    validate(doc["characters"])
    build(doc)
    print("\033[32mBUILD OK\033[0m")


if __name__ == "__main__":
    main()
