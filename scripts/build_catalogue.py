#!/usr/bin/env python3
"""Character catalogue generator: merge, validate, emblems, pages, coverage.

Reads every data/catalogue/*.json batch file, validates the merged record set
strictly, writes the single source of truth at data/catalogue.json, generates
SVG emblems and static pages under explore/, and prints a coverage report.

Independent generator: never imports build_explore (avoids a cycle) and does
not modify data/cast.json, pages/, or the other build scripts' outputs.
"""
import json
import re
import sys
from pathlib import Path

import catalogue_util as cu

ROOT = cu.ROOT
CATALOGUE_OUT = ROOT / "data" / "catalogue.json"
EXPLORE = ROOT / "explore"
DETAIL_DIR = EXPLORE / "catalogue"
IMG_DIR = ROOT / "assets" / "img"

CONTINUITY_COLORS = cu.CONTINUITY_COLORS
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SITE = "https://doomsdayhub.example"

# --- Page shell (duplicated small helpers; build_catalogue never imports
# --- build_explore to avoid a cycle, so it keeps its own tiny page head/nav).

NAV_ITEMS = [
    ("characters", "Characters", "characters.html"),
    ("watch-guide", "Watch Guide", "watch-guide.html"),
    ("timeline", "Timeline", "timeline.html"),
    ("stats", "Stats", "stats.html"),
    ("memorial", "Memorial", "memorial.html"),
]


def _site_nav(active, prefix=""):
    """prefix='' at explore/ depth, '../' inside explore/catalogue/."""
    lis = "".join(
        f'<li><a href="{prefix}{href}" {"class=\"active\"" if key == active else ""}>{label}</a></li>'
        for key, label, href in NAV_ITEMS)
    return (f'<nav class="nav"><div class="nav-inner"><a class="brand" href="{prefix}../index.html">'
            '<span class="av">AVENGERS</span><span class="sep">:</span><span class="dd">DOOMSDAY</span></a>'
            f'<ul>{lis}</ul></div></nav>')


def _foot(prefix=""):
    return (f'<footer class="foot"><a href="{prefix}../index.html">↑ Back to the hub</a>'
            '<p style="margin-top:0.5rem;font-size:0.75rem">Catalogue data: on-screen Marvel / MCU &amp; '
            'multiverse records with sources. Verified images are attributed; unverified show a pending chip.</p></footer>')


def die(msg):
    print(f"\033[31mCATALOGUE FAIL:\033[0m {msg}", file=sys.stderr)
    sys.exit(1)


def validate(records):
    """Strict validation. Raises SystemExit(1) on the first violation."""
    if not isinstance(records, list):
        die(f"records must be a list, got {type(records).__name__}")
    seen = {}
    for r in records:
        if not isinstance(r, dict):
            die(f"record is not an object: {r!r}")
        cid = r.get("id", "")
        if not SLUG_RE.match(cid):
            die(f"bad id shape: {cid!r} (must be lowercase kebab)")
        if cid in seen:
            die(f"duplicate id: {cid}")
        seen[cid] = True
        for f in cu.REQUIRED:
            if f not in r or r[f] in (None, ""):
                die(f"{cid} missing required field: {f}")
        for f in ("team_or_affiliation", "related_titles", "source_notes"):
            if not isinstance(r.get(f), list):
                die(f"{cid} {f} must be a list")
        if not isinstance(r.get("verified"), bool):
            die(f"{cid} verified must be a bool")
        if r.get("image_url"):
            if not (r["image_url"].startswith("https://") or r["image_url"].startswith("../")):
                die(f"{cid} image_url must be https:// or relative path (../)")
            if r["image_url"].startswith("https://"):
                for f in ("image_alt", "image_source_url", "image_source_name"):
                    if not r.get(f):
                        die(f"{cid} has image_url but missing {f}")


def load_normalized():
    recs = cu.load_all()
    validate(recs)
    recs.sort(key=lambda r: r.get("id", ""))
    return recs


def merge(records):
    """Normalize (trim strings) and write data/catalogue.json."""
    normalized = []
    for r in records:
        out = dict(r)
        for k, v in out.items():
            if isinstance(v, str):
                out[k] = v.strip()
        normalized.append(out)
    normalized.sort(key=lambda r: r["id"])
    CATALOGUE_OUT.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def coverage_report(records):
    """Counts for the coverage summary (full split logic)."""
    total = len(records)
    with_img = [r for r in records if r.get("image_url")]
    verified_img = [r for r in with_img if r.get("image_verified")]
    tags_of = lambda t: [r for r in records if t in (r.get("tags") or [])]
    by_cont = {}
    for r in records:
        c = r.get("continuity", "Other")
        by_cont[c] = by_cont.get(c, 0) + 1
    return {
        "total": total,
        "images": len(with_img),
        "verified_images": len(verified_img),
        "pending_images": len(with_img) - len(verified_img),
        "spider_man": len(tags_of("spider-man")),
        "mcu": len(tags_of("mcu")),
        "multiverse_and_legacy": len(tags_of("multiverse")) + len(tags_of("legacy")),
        "xmen": len(tags_of("x-men")),
        "fantastic_four": len(tags_of("fantastic-four")),
        "by_continuity": by_cont,
    }


def _write_coverage(cov):
    """Emit a human/machine-readable coverage report at data/catalogue-coverage.json."""
    REPORT = ROOT / "data" / "catalogue-coverage.json"
    REPORT.write_text(json.dumps(cov, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_emblems(records):
    """Deterministic SVG monogram for every record. Returns count written."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in records:
        color = CONTINUITY_COLORS.get(r.get("continuity", ""), "#00cc55")
        svg = cu.initial_portrait(r["name"], color)
        (IMG_DIR / f"cat-{r['id']}.svg").write_text(svg, encoding="utf-8")
        n += 1
    return n


# --- Task 7: sitemap ---

SITEMAP_BASE = "https://doomsdayhub.example"


def _cast_pages():
    """Cast slugs from data/cast.json (the 30-page roster), never cycle-imported."""
    cast = ROOT / "data" / "cast.json"
    if not cast.exists():
        return []
    try:
        doc = json.loads(cast.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [f"{SITEMAP_BASE}/pages/{c['slug']}.html" for c in doc.get("characters", [])]


def sitemap_entries(records):
    urls = [f"{SITEMAP_BASE}/", f"{SITEMAP_BASE}/index.html"]
    urls += [f"{SITEMAP_BASE}/explore/{n}" for n in
             ("characters.html", "watch-guide.html",
              "timeline.html", "stats.html", "memorial.html")]
    urls += _cast_pages()
    urls += [f"{SITEMAP_BASE}/explore/catalogue/{r['id']}.html" for r in records]
    return sorted(set(urls))


def build_sitemap(records):
    items = "".join(f"  <url><loc>{u}</loc></url>\n" for u in sitemap_entries(records))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + items + "</urlset>\n")
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(records) + 7  # catalogue pages + hub/standalone/cast page total count


# --- Task 4: listing page (replaces explore/characters.html) ---


def _status_color(status: str) -> str:
    return {
        "Active": "#1aa35c",
        "Deceased": "#e63946",
        "MIA": "#c8b33a",
        "Variant": "#00b3cc",
        "Legacy": "#9b5de5",
    }.get(status, "#00cc55")


def _status_glyph(status: str) -> str:
    return {
        "Active": "●",
        "Deceased": "✕",
        "MIA": "?",
        "Variant": "◆",
        "Legacy": "★",
    }.get(status, "●")


def _tag_chips(tags):
    return "".join(f'<span class="chip tag">{cu.esc(t)}</span>' for t in (tags or []))


def _cat_card(r):
    """Single catalogue card HTML — cinematic recognition card.

    The media panel always carries the dossier emblem (colour-graded to the
    character's universe); a verified photo layers over it and removes itself
    on error. Status + Doomsday flags are glass chips overlaid on the media,
    and the body holds exactly one meta row. No "pending" text — a missing
    photo reads as an ID record, not an error.
    """
    cont = r.get("continuity", "Other")
    cont_color = CONTINUITY_COLORS.get(cont, "#00cc55")
    status = r.get("status", "Active")
    status_c = _status_color(status)
    has_img = bool(r.get("image_url"))
    img_verified = r.get("image_verified", False)

    if has_img and img_verified:
        photo = (
            f'<img class="cat-photo" src="{cu.esc(r["image_url"])}" '
            f'alt="{cu.esc(r.get("image_alt", r["name"]))}" '
            f'loading="lazy" width="200" height="200" onerror="this.remove()">'
        )
    else:
        photo = ""

    status_pill = (
        f'<span class="cat-status" style="--sc:{status_c}">'
        f'<span class="cat-status-dot"></span>{cu.esc(status)}</span>'
    )

    doom_badge = ""
    if r.get("doomsday_cast_slug"):
        doom_badge = '<span class="cat-doom"><span class="cat-doom-bolt">⚡</span>Doomsday</span>'

    return f"""
<a class="cat-card" href="./catalogue/{r['id']}.html"
   data-uni="{cu.esc(cont)}"
   data-team="{cu.esc('|'.join(r.get('team_or_affiliation') or []))}"
   data-type="{cu.esc(r.get('character_type', 'Hero'))}"
   style="--ring:{cont_color}">
  <div class="cat-media">
    <img class="cat-emblem" src="../assets/img/cat-{r['id']}.svg"
         alt="{cu.esc(r['name'])} emblem" loading="lazy" width="200" height="200">
    {photo}
    <span class="cat-view" aria-hidden="true">View profile →</span>
    {doom_badge}
    {status_pill}
  </div>
  <div class="cat-body">
    <h3 class="cat-name">{cu.esc(r['name'])}</h3>
    <p class="cat-alias">{cu.esc(r['alias'])}</p>
    <div class="cat-meta">
      <span class="cat-uni" style="--uc:{cont_color}">{cu.esc(cont)}</span>
      <span class="cat-type">{cu.esc(r.get('character_type', 'Hero'))}</span>
    </div>
  </div>
</a>""".strip()


# Ordering: the 30 confirmed Doomsday cast lead, then the original Avengers
# roster, then everyone else ranked by on-screen relevance to the hub.
OG_AVENGERS_IDS = {
    "iron-man-tony-stark", "captain-america-steve-rogers", "thor",
    "hulk-bruce-banner", "black-widow-natasha-romanoff", "hawkeye-clint-barton",
}

# Relevance priority by continuity: MCU is the hub's home frame, the multiversal
# franchises that feed Doomsday come next, legacy TV after, then older one-off films.
CONTINUITY_PRIORITY = {
    "MCU": 0,
    "Multiverse": 1,
    "X-Men": 2,
    "Fantastic Four": 2,
    "Sony's Spider-Man Universe": 3,
    "Spider-Man (Raimi trilogy)": 3,
    "The Amazing Spider-Man (Webb duology)": 3,
    "Agents of S.H.I.E.L.D.": 4,
    "Netflix Marvel": 4,
    "Legacy TV": 4,
}


def _listing_order(records):
    """Sort catalogue records: Doomsday-30 first, then original Avengers, then
    the rest by on-screen relevance (continuity priority, then name)."""
    return sorted(records, key=lambda r: (
        0 if r.get("doomsday_cast_slug") else 1,          # confirmed roster first
        0 if r.get("id") in OG_AVENGERS_IDS else 1,       # then the original six
        CONTINUITY_PRIORITY.get(r.get("continuity", "Other"), 9),
        (r.get("name") or "").lower(),
    ))


def build_listing(records, cast_doc):
    """Full catalogue listing page — replaces explore/characters.html."""
    # Order records (deterministic): top-30 → original Avengers → by relevance.
    ordered = _listing_order(records)

    # Gather unique filter values — only emit pills that actually match records.
    # Continuities and character types are kept whole; teams with a single member
    # are dropped as near-empty filters that clutter the list.
    unis = sorted(set(r.get("continuity", "Other") for r in records))
    team_counts = {}
    for r in records:
        for t in (r.get("team_or_affiliation") or []):
            team_counts[t] = team_counts.get(t, 0) + 1
    teams = sorted(t for t, n in team_counts.items() if n >= 2)
    types = sorted(set(r.get("character_type", "Hero") for r in records))

    # Filter chips — tucked inside a collapsed dropdown so the hero stays compact.
    uni_chips = "".join(
        f'<button class="pill" data-uni="{cu.esc(u)}">{cu.esc(u)}</button>' for u in unis)
    team_chips = "".join(
        f'<button class="pill" data-team="{cu.esc(t)}">{cu.esc(t)}</button>' for t in teams)
    type_chips = "".join(
        f'<button class="pill" data-type="{cu.esc(t)}">{cu.esc(t)}</button>' for t in types)

    filters_html = f"""<details class="cat-filters">
  <summary><span class="filters-icon">⚙</span> Filters
    <span class="filters-count">universe · team · type</span>
    <span class="filters-caret" aria-hidden="true">▾</span>
  </summary>
  <div class="cat-filters-body">
    <div class="filter-group">
      <div class="filter-label">Universe (continuity)</div>
      <div class="pill-row">{uni_chips}</div>
    </div>
    <div class="filter-group">
      <div class="filter-label">Team / Affiliation</div>
      <div class="pill-row">{team_chips}</div>
    </div>
    <div class="filter-group">
      <div class="filter-label">Character Type</div>
      <div class="pill-row">{type_chips}</div>
    </div>
    <button id="catalogue-clear" class="btn btn-secondary" style="margin-top:0.75rem">Clear filters</button>
  </div>
</details>"""

    # Count summary — includes every catalogue record.
    total = len(records)
    tags_of = lambda t: sum(1 for r in records if t in (r.get("tags") or []))
    mcu = tags_of("mcu")
    legacy = tags_of("multiverse") + tags_of("legacy")
    spidey = tags_of("spider-man")
    xmen = tags_of("x-men")
    ff = tags_of("fantastic-four")
    confirmed = sum(1 for r in records if r.get("doomsday_cast_slug"))

    count_html = f"""<div class="count-sum">
  <span>All characters: <strong>{total}</strong></span>
  <span>Confirmed Doomsday: <strong>{confirmed}</strong></span>
  <span>MCU: <strong>{mcu}</strong></span>
  <span>Legacy / Multiverse: <strong>{legacy}</strong></span>
  <span>Spider-Man: <strong>{spidey}</strong></span>
  <span>X-Men: <strong>{xmen}</strong></span>
  <span>Fantastic Four: <strong>{ff}</strong></span>
</div>"""

    # Grid cards — in the curated order (not alphabetical).
    grid = "\n".join(_cat_card(r) for r in ordered)

    # Doomsday 30 badge (cross-link note at top)
    badge = """<div class="badge-doomsday">
  <span class="badge-icon">⚡</span>
  <strong>30 confirmed Doomsday cast</strong> — characters with a "<em>Confirmed for Doomsday</em>" badge
  cross-link to their cast pages. The 30-member Doomsday roster stays intact; this catalogue adds the wider on-screen universe.
</div>"""

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList", "name": "Marvel Character Catalogue",
        "itemListElement": [{"@type": "Person", "name": r["name"]} for r in ordered]})

    # Page head needs proper relative paths from explore/ depth
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All Characters — Avengers: Doomsday</title>
<meta name="description" content="Complete on-screen Marvel character catalogue: MCU, X-Men, Fantastic Four, Spider-Verse, legacy multiverse. Search, filter, and explore.">
<meta property="og:title" content="All Characters — Avengers: Doomsday">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/explore/characters.html">
<link rel="canonical" href="{SITE}/explore/characters.html">
<link rel="stylesheet" href="../assets/css/styles.css?v=cards-rewrite-20260901b">
<style>
/* CACHE-PROOF: character grid base only — card styling lives in styles.css */
.cat-grid{{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(184px,1fr))!important;gap:1.25rem!important;align-items:start!important}}
</style>
<script type="application/ld+json">{jsonld}</script>
</head>"""

    return f"""{head}
<body>
{_site_nav("characters")}
<header class="hero char-hero">
  <h1>All Characters</h1>
  <p class="lede">The on-screen Marvel character catalogue — MCU, X-Men, Fantastic Four, Spider-Verse, legacy multiverse.</p>
  {badge}
  <div class="cat-toolbar">
    <input id="catalogue-search" class="cmd-input" placeholder="Search name, alias, actor, team, summary…" autocomplete="off">
    {count_html}
    {filters_html}
  </div>
</header>
<main class="wrap"><div class="cat-grid" id="cat-grid">
{grid}
</div></main>
{_foot()}
<script src="../assets/js/catalogue.js"></script>
<script src="../assets/js/main.js"></script></body></html>"""


# --- Task 5: detail pages (explore/catalogue/<id>.html) ---

_KNOWN = None


def _known_ids():
    """Frozenset of every catalogue id, computed once (cached)."""
    global _KNOWN
    if _KNOWN is None:
        _KNOWN = frozenset(r["id"] for r in cu.load_all())
    return _KNOWN


def _sibling_link(cid, label):
    """Link to a sibling catalogue page when it exists, else plain text."""
    if cid in _known_ids():
        return f'<a class="sib" href="./{cid}.html">{cu.esc(label)}</a>'
    if cid.count("-") > 0:
        # A readable id-like label without an underscore
        return f'<span class="sib plain">{cu.esc(label or cid)}</span>'
    return f'<span class="sib plain">{cu.esc(label or cid)}</span>'


def _chip(label, kind, color=""):
    style = f' style="--chip-bg:{cu.esc(color)}"' if color else ""
    return f'<span class="chip {cu.esc(kind)}"{style}>{cu.esc(label)}</span>'


def build_detail(record, prev_id, next_id, cast_doc):
    r = record
    cid = r["id"]
    cont = r.get("continuity", "Other")
    cont_color = CONTINUITY_COLORS.get(cont, "#00cc55")
    status = r.get("status", "Active")
    status_c = _status_color(status)
    status_g = _status_glyph(status)
    verified = r.get("verified", True)

    # --- image block with attribution ---
    if r.get("image_url") and r.get("image_verified"):
        # Stored URLs are relative to explore/ (the listing's depth). Detail
        # pages live one level deeper (explore/catalogue/), so bump "../" -> "../../".
        src = r["image_url"]
        if src.startswith("../"):
            src = "../" + src
        img_tag = (f'<img class="photo" src="{cu.esc(src)}" '
                   f'alt="{cu.esc(r.get("image_alt", r["name"]))}" '
                   f'loading="lazy" width="400" height="400" onerror="this.remove()">')
        img_note = (f'<div class="img-attr">Image: {cu.esc(r.get("image_source_name", ""))} — '
                    f'<a href="{cu.esc(r.get("image_source_url", "#"))}">source page</a></div>')
    else:
        # No verified frame on file — the dossier emblem (color-graded to the
        # character's universe) carries the portrait slot. No "pending" note.
        img_tag = ""
        img_note = ""
    img_html = f"""
    <div class="detail-portrait" style="--ring:{cont_color}">
      <img class="fallback" src="../../assets/img/cat-{cid}.svg" alt="{cu.esc(r['name'])} emblem"
           loading="lazy" width="400" height="400">
      {img_tag}
      {img_note}
    </div>"""

    # --- identity header ---
    played = ""
    if r.get("portrayed_by"):
        played = f'<p class="muted detail-actor">Portrayed by <strong>{cu.esc(r["portrayed_by"])}</strong></p>'
    identity = f"""
<div class="detail-id">
  <h1>{cu.esc(r['name'])}</h1>
  <p class="detail-alias">{cu.esc(r['alias'])}</p>
  {played}
  <div class="detail-chips">
    {_chip(cont, "uni", cont_color)}
    {_chip(status, "status", status_c)}
    {_chip(r.get("character_type", "Hero"), "type")}
    {_chip(r.get("universe", "Universes unknown"), "universe")}
  </div>
</div>"""

    # --- summary + debut + related + allies/enemies ---
    unw = '<span class="unverified-flag" title="Unverified data">⚠ content unverified</span>' if not verified else ""
    debut = r.get("debut_title", "—")
    related = "".join(f"<li>{cu.esc(t)}</li>" for t in (r.get("related_titles") or []))
    allies = "".join(_sibling_link(a, a) for a in (r.get("allies") or []))
    enemies = "".join(_sibling_link(e, e) for e in (r.get("enemies") or []))
    tags = "".join(_chip(t, "tag") for t in (r.get("tags") or []))
    notes = " ".join(n for n in (r.get("source_notes") or []))
    notes_cells = []
    if notes:
        notes_cells.append(f'<div class="source-notes"><h3>Source notes</h3><p>{cu.esc(notes)}</p></div>')
    if r.get("notes"):
        notes_cells.append(f'<div class="source-notes extra"><h3>Notes</h3><p>{cu.esc(r["notes"])}</p></div>')

    doomday_link = ""
    if r.get("doomsday_cast_slug"):
        doomday_link = (f'<p class="doomday-link"><a class="badge doomsday" '
                        f'href="../../pages/{r["doomsday_cast_slug"]}.html" '
                        f'target="_blank" rel="noopener">⚡ Confirmed for Doomsday — view cast page</a></p>')

    # --- prev / next nav ---
    nav = ""
    prev_lnk = f'<a class="pnav" href="./{prev_id}.html">← {cu.esc(prev_id)}</a>' if prev_id else \
        '<span class="pnav disabled">← first</span>'
    next_lnk = f'<a class="pnav" href="./{next_id}.html">{cu.esc(next_id)} →</a>' if next_id else \
        '<span class="pnav disabled">last →</span>'
    pagenav = f'<nav class="pnav-row">{prev_lnk} {next_lnk}</nav>'

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Person", "name": r["name"],
        "alternateName": r.get("alias", ""), "description": r.get("summary", ""),
        "url": f"{SITE}/explore/catalogue/{cid}.html"})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{cu.esc(r['name'])} — {cu.esc(r.get('alias', ''))} | Avengers: Doomsday</title>
<meta name="description" content="{cu.esc(r.get('summary', ''))[:155]}">
<meta property="og:title" content="{cu.esc(r['name'])}">
<meta property="og:type" content="profile">
<meta property="og:url" content="{SITE}/explore/catalogue/{cid}.html">
<link rel="canonical" href="{SITE}/explore/catalogue/{cid}.html">
<link rel="stylesheet" href="../../assets/css/styles.css">
<script type="application/ld+json">{jsonld}</script>
</head>
<body class="faction-{cu.esc(_faction(cont))}">
{_site_nav("characters", prefix="../")}
<header class="hero char-hero">
  <div class="wrap detail-fixed">
    <a class="backlink" href="../characters.html">← All characters</a>
    <div class="detail-grid">
      {img_html}
      {identity}
    </div>
    {unw}
    {doomday_link}
  </div>
</header>
<main class="wrap">
  <section class="card">
    <h2>Summary</h2>
    <p>{cu.esc(r.get('summary', ''))}</p>
  </section>
  <section class="card">
    <h2>Debut</h2>
    <p class="detail-debut">{cu.esc(debut)}</p>
  </section>
  <section class="card">
    <h2>Key &amp; related titles</h2>
    <ul class="rel-list">{related if related else '<li>None logged</li>'}</ul>
  </section>
  <section class="card">
    <h2>Allies &amp; enemies</h2>
    <div class="rel-cols">
      <div><h3>Allies</h3>{allies if allies else '<p class="muted">None in catalogue</p>'}</div>
      <div><h3>Enemies</h3>{enemies if enemies else '<p class="muted">None in catalogue</p>'}</div>
    </div>
  </section>
  <section class="card">
    <h2>Tags</h2>
    <div class="rel-tags">{tags}</div>
  </section>
  {''.join(notes_cells)}
  {pagenav}
</main>
{_foot(prefix="../")}
<script src="../../assets/js/main.js"></script></body></html>"""


def _faction(cont):
    """Map a continuity to the site's faction class (for colour theming)."""
    return {
        "MCU": "avengers", "Raimi": "newavengers", "Webb": "newavengers",
        "SSU": "villain", "X-Men": "xmen", "Fantastic Four": "fantastic",
        "Legacy TV": "newavengers", "Multiverse": "villain",
    }.get(cont, "villain")


def build_all():
    recs = load_normalized()
    merge(recs)
    n_emo = build_emblems(recs)
    cov = coverage_report(recs)
    print(f"Merged {cov['total']} catalogue records -> data/catalogue.json")
    print(f"Wrote {n_emo} emblem SVGs -> assets/img/cat-<id>.svg")
    print("Coverage:", json.dumps(cov, indent=2))

    # Write listing page (replaces explore/characters.html)
    listing = build_listing(recs, {})
    EXPLORE.mkdir(parents=True, exist_ok=True)
    (EXPLORE / "characters.html").write_text(listing, encoding="utf-8")
    print(f"  wrote explore/characters.html ({len(recs)} cards)")

    # Write detail pages
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(recs):
        prev_id = recs[i - 1]["id"] if i > 0 else None
        next_id = recs[i + 1]["id"] if i < len(recs) - 1 else None
        html = build_detail(r, prev_id, next_id, {})
        (DETAIL_DIR / f"{r['id']}.html").write_text(html, encoding="utf-8")
    print(f"  wrote {len(recs)} detail pages -> explore/catalogue/")

    # Rewrite the site sitemap (runs last, so it is authoritative) + coverage report
    build_sitemap(recs)
    _write_coverage(cov)
    print("  wrote sitemap.xml + coverage report")

    print("ALL CATALOGUE GENERATION OK")


if __name__ == "__main__":
    build_all()