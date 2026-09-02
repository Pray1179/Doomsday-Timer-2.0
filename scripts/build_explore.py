#!/usr/bin/env python3
"""Doomsday Fan Hub — Explore-tier generator (Phase 2).

Reads data/cast.json (source of truth) and emits the five explore pages:
characters, universes, watch-guide, timeline, stats. Pure stdlib, deterministic.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cast.json"
EXPLORE = ROOT / "explore"
SITE = "https://doomsdayhub.example"


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def unit_key(u):
    """Return a slug-safe css key for a unit/universe label."""
    return str(u).split("(")[0].strip().lower().replace(" ", "-")


# === CHARACTER EMBLEMS ===
# Official portraits need per-character CDN URLs (data/image_urls.json) which
# are not always available. Until one is, each card shows a deterministic SVG
# monogram — a unit-colored ring around the character's initials — so the grid
# never looks half-baked. Written into assets/img/<slug>.svg by build_emblems().
EMBLEM_UNIT_COLORS = {
    "Avengers": "#e63946",
    "X-Men": "#9b5de5",
    "Wakandans": "#c8b33a",
    "Fantastic Four": "#1aa35c",
    "New Avengers": "#3a7bd5",
    "Villain": "#00cc55",
}


def _initials(char_name):
    """Up to two monogram letters from the primary character name.

    The alias after '/' is ignored; filler words ('the', 'von') are skipped.
    'Victor von Doom / Doctor Doom' -> VD, 'Thor' -> T, 'Sam Wilson / Captain
    America' -> SW.
    """
    primary = char_name.split("/")[0].strip()
    toks = [t for t in primary.split()
            if t.lower() not in ("the", "of", "a", "an", "von", "van", "de", "da")]
    if not toks:
        return primary[:1].upper()
    if len(toks) == 1:
        return toks[0][0].upper()
    return (toks[0][0] + toks[1][0]).upper()


def _emblem_svg(slug, name, color):
    """Small deterministic SVG emblem: dark shield, accent ring, initials."""
    init = _initials(name)
    safe_name = esc(name)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-label="{safe_name} emblem">
  <defs>
    <radialGradient id="bg" cx="50%" cy="36%" r="80%">
      <stop offset="0%" stop-color="#26263c"/>
      <stop offset="55%" stop-color="#15151f"/>
      <stop offset="100%" stop-color="#07070c"/>
    </radialGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color}"/>
      <stop offset="100%" stop-color="{color}"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="184" height="184" rx="36" fill="url(#bg)" stroke="rgba(255,255,255,0.07)" stroke-width="2"/>
  <circle cx="100" cy="100" r="66" fill="none" stroke="{color}" stroke-width="3" opacity="0.4"/>
  <circle cx="100" cy="100" r="52" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.28" stroke-dasharray="2 7" stroke-linecap="round"/>
  <text x="100" y="127" text-anchor="middle" font-family="Arial Black, 'Helvetica Neue', sans-serif"
        font-size="58" font-weight="800" fill="#ffffff" letter-spacing="3">{init}</text>
  <circle cx="100" cy="168" r="3.5" fill="{color}" opacity="0.85"/>
</svg>
"""


def build_emblems(doc):
    """Write assets/img/<slug>.svg for every character. Deterministic."""
    img = ROOT / "assets" / "img"
    img.mkdir(parents=True, exist_ok=True)
    written = 0
    for c in doc["characters"]:
        color = EMBLEM_UNIT_COLORS.get(c["unit"], "#00cc55")
        out = img / f"{c['slug']}.svg"
        out.write_text(_emblem_svg(c["slug"], c["character"]["name"], color),
                       encoding="utf-8")
        written += 1
    return written


def page_head(title, desc, canonical, extra_jsonld=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Avengers: Doomsday</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{esc(canonical)}">
<link rel="canonical" href="{SITE}{esc(canonical)}">
<link rel="stylesheet" href="../assets/css/styles.css">
<script type="application/ld+json">{extra_jsonld}</script>
</head>"""


def site_nav(active):
    items = [
        ("characters", "Characters", "characters.html"),
        ("watch-guide", "Watch Guide", "watch-guide.html"),
        ("timeline", "Timeline", "timeline.html"),
        ("stats", "Stats", "stats.html"),
        ("memorial", "Memorial", "memorial.html"),
    ]
    lis = "".join(
        f'<li><a href="{href}" {"class=\"active\"" if key == active else ""}>{label}</a></li>'
        for key, label, href in items)
    return ('<nav class="nav"><div class="nav-inner"><a class="brand" href="../index.html">'
            '<span class="av">AVENGERS</span><span class="sep">:</span><span class="dd">DOOMSDAY</span></a>'
            f'<ul>{lis}</ul></div></nav>')


def foot():
    return ('<footer class="foot"><a href="../index.html">↑ Back to the hub</a>'
            '<p style="margin-top:0.5rem;font-size:0.75rem">Data verified via agent-reach. Bios are not invented.</p></footer>')


def character_cards(chars):
    cards = []
    for c in sorted(chars, key=lambda x: x["slug"]):
        uk = unit_key(c["unit"])
        cards.append(f"""<a class="cast-card" href="../pages/{c['slug']}.html" data-unit="{uk}">
  <div class="img"><img src="../assets/img/{c['slug']}.svg" alt="{esc(c['character']['name'])}"
    onerror="this.remove()"></div>
  <div class="name">{esc(c['character']['name'])}</div>
  <div class="char">{esc(c['unit'])}</div>
</a>""")
    return "\n".join(cards)


def build_characters(doc):
    units = ["Avengers", "X-Men", "Fantastic Four", "Wakandans", "New Avengers", "Villain"]
    pills = "".join(f'<button class="pill" data-unit="{unit_key(u)}">{esc(u)}</button>' for u in units)
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList", "name": "Doomsday Cast",
        "itemListElement": [{"@type": "Person", "name": c["character"]["name"]}
                            for c in doc["characters"]]})
    return (page_head("All Characters", "Browse every confirmed Doomsday cast member.",
                      "/explore/characters.html", jsonld)
            + "<body>"
            + site_nav("characters")
            + f"""<header class="hero char-hero">
  <h1>All Characters</h1>
  <p class="lede">Search and filter every confirmed cast member.</p>
  <div style="margin-top:2rem">
    <input id="explore-filter" class="cmd-input" placeholder="Search by name, unit, or universe…" autocomplete="off">
    <div class="pill-row">{pills}</div>
  </div>
</header>
<main class="wrap"><div class="cast-grid" id="explore-grid">
{character_cards(doc['characters'])}
</div></main>
<script>window.CAST_EXPLORE = true;</script>"""
            + foot() + """
<script>
(function(){
  var grid=document.getElementById('explore-grid');
  var input=document.getElementById('explore-filter');
  var cards=[].slice.call(grid.querySelectorAll('.cast-card'));
  var activeUnit=null;
  document.querySelectorAll('.pill').forEach(function(p){p.addEventListener('click',function(){
    document.querySelectorAll('.pill').forEach(function(x){x.classList.remove('on')});
    p.classList.add('on'); activeUnit=activeUnit===p.dataset.unit?null:p.dataset.unit; filter();
  });});
  function filter(){
    var q=(input.value||'').toLowerCase();
    cards.forEach(function(card){
      var hit=card.dataset.unit===activeUnit || !activeUnit;
      if(hit && q) hit = card.textContent.toLowerCase().indexOf(q)>-1;
      card.style.display = hit?'':'none';
    });
  }
  input.addEventListener('input', filter);
})();
</script>
<script src="../assets/js/main.js"></script></body></html>""")


def group_by_universe(chars):
    g = {}
    for c in chars:
        g.setdefault(c["character"]["universe"], []).append(c)
    return g


def build_universes(doc):
    groups = group_by_universe(doc["characters"])
    blocks = []
    for uni in sorted(groups, key=str):
        cards = "\n".join(
            f'<a class="cast-card" href="../pages/{c["slug"]}.html"><div class="img">'
            f'<img src="../assets/img/{c["slug"]}.svg" alt="" onerror="this.remove()"></div>'
            f'<div class="name">{esc(c["character"]["name"])}</div>'
            f'<div class="char">{esc(c["unit"])}</div></a>'
            for c in sorted(groups[uni], key=lambda x: x["slug"]))
        blocks.append(f'<section class="card uni-block" data-uni="{unit_key(uni)}">'
                      f'<h2>{esc(uni)} <span class="count">({len(groups[uni])})</span></h2>'
                      f'<div class="cast-grid">{cards}</div></section>')
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage",
                         "name": "Doomsday Universes"})
    return (page_head("Universes", "Where Doomsday's cast comes from across the Multiverse.",
                      "/explore/universes.html", jsonld)
            + "<body>" + site_nav("universes")
            + '<header class="hero char-hero"><h1>The Multiverse</h1>'
            + '<p class="lede">Every confirmed player, grouped by home universe.</p></header>'
            + '<main class="wrap">' + "\n".join(blocks) + "</main>"
            + foot()
            + '<script src="../assets/js/main.js"></script>'
            + '<script src="../assets/js/universes.js"></script></body></html>')


def build_watch_guide(doc):
    blocks = []
    for c in sorted(doc["characters"], key=lambda x: x["slug"]):
        ch = c["character"]
        app = [esc(w) for w in (ch.get("appearances") or [])]
        film_li = "".join(
            f"<li><span class='wg-n'>{i:02d}</span><span class='wg-t'>{w}</span></li>"
            for i, w in enumerate(app, 1)) if app else "<li>No filmography logged yet</li>"
        watch = [esc(w) for w in (ch.get("watch_before") or [])]
        watch_li = "".join(f"<li>{w}</li>" for w in watch) if watch else "<li>No essential list yet</li>"
        first = c["actor"].get("mcu_first_appearance", "—")
        latest = ch.get("latest_appearance", "—")
        blocks.append(
            f'<section class="card"><h3><a href="../pages/{c["slug"]}.html">{esc(ch["name"])}</a>'
            f' <span class="muted">({esc(c["actor"]["name"])})</span></h3>'
            f'<p class="muted">First seen: {esc(first)} · Latest: {esc(latest)} · '
            f'{len(app)} total appearances · Unit: {esc(c["unit"])}</p>'
            f'<h4 class="wg-sub">Complete filmography</h4>'
            f'<ol class="wg-film">{film_li}</ol>'
            f'<h4 class="wg-sub">Essential before Doomsday</h4>'
            f'<ul class="watch">{watch_li}</ul></section>')
    return (page_head("Watch Guide", "Every MCU appearance per character.", "/explore/watch-guide.html")
            + "<body>" + site_nav("watch-guide")
            + '<header class="hero char-hero"><h1>Watch Guide</h1>'
            + '<p class="lede">The complete MCU filmography for every confirmed cast member.</p>'
            + '</header>'
            + '<main class="wrap">' + "\n".join(blocks) + "</main>"
            + foot() + "</body></html>")


def build_timeline(doc):
    rel = doc["release"]
    rows = [
        (rel.get("phase", "Phase Six"), "Now", f'{rel["title"]} sits in {rel["phase"]}.'),
        (rel["date"], "Release", f'{rel["title"]} opens.'),
        (rel.get("sequel_date", "2027-12-17"), "Sequel",
         f'{rel.get("sequel_title", "Avengers: Secret Wars")} follows.'),
    ]
    lis = "".join(f'<li class="tl-item"><span class="tl-date">{esc(d)}</span>'
                  f'<span class="tl-label">{esc(l)}</span><p class="muted">{esc(t)}</p></li>'
                  for d, l, t in rows)
    return (page_head("Timeline", "Where Doomsday sits in the Multiverse Saga.",
                      "/explore/timeline.html")
            + "<body>" + site_nav("timeline")
            + '<header class="hero char-hero"><h1>Timeline</h1>'
            + '<p class="lede">Key dates and phases, drawn from the release block.</p></header>'
            + '<main class="wrap"><ul class="timeline">' + lis + "</ul></main>"
            + foot() + "</body></html>")


def sitemap_xml(doc):
    urls = ["https://doomsdayhub.example/", "https://doomsdayhub.example/index.html"]
    urls += [f"https://doomsdayhub.example/explore/{name}" for name in
             ("characters.html", "watch-guide.html", "timeline.html", "stats.html", "memorial.html")]
    urls += [f"https://doomsdayhub.example/pages/{c['slug']}.html" for c in doc["characters"]]
    items = "".join(f"  <url><loc>{u}</loc></url>\n" for u in sorted(set(urls)))
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + items + "</urlset>\n"


def robots_txt():
    return "User-agent: *\nAllow: /\n\nSitemap: https://doomsdayhub.example/sitemap.xml\n"


def not_found_html():
    return (page_head("Not Found", "This page wandered off into the Multiverse.",
                      "/explore/404.html")
            + "<body>" + site_nav("")
            + '<main class="wrap" style="text-align:center;padding-top:6rem"><h1>404</h1>'
            + '<p class="lede">This page slipped through a portal. Choose a side below or head home.</p>'
            + '<p style="margin-top:2rem"><a href="../index.html" class="btn btn-primary">Back to DOOMSDAY</a></p></main>'
            + foot() + "</body></html>")


def build_meta(doc):
    (ROOT / "sitemap.xml").write_text(sitemap_xml(doc), encoding="utf-8")
    (ROOT / "robots.txt").write_text(robots_txt(), encoding="utf-8")
    not_found = EXPLORE / "404.html"
    not_found.parent.mkdir(exist_ok=True)
    not_found.write_text(not_found_html(), encoding="utf-8")


def counts_by(chars, keyfn):
    return dict(Counter(keyfn(c) for c in chars))


def _bar(label, n, total, color):
    pct = (n / total * 100) if total else 0
    return (f'<div class="stat-row"><span class="stat-label">{esc(label)}</span>'
            f'<div class="bar"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'
            f'<span class="stat-num">{n}</span></div>')


def build_stats(doc):
    chars = doc["characters"]
    total = len(chars)
    unit_colors = {"Avengers": "var(--accent-avengers)", "X-Men": "var(--accent-xmen)",
                   "Fantastic Four": "var(--accent-fantastic)", "Wakandans": "var(--accent-wakandans)",
                   "New Avengers": "var(--accent-newavengers)", "Villain": "var(--accent-villain)"}
    by_unit = counts_by(chars, lambda c: c["unit"])
    by_uni = counts_by(chars, lambda c: c["character"]["universe"])
    bars_unit = "".join(_bar(u, n, total, unit_colors.get(u, "var(--accent-villain)"))
                        for u, n in sorted(by_unit.items()))
    bars_uni = "".join(_bar(u, n, total, "var(--accent-fantastic)")
                       for u, n in sorted(by_uni.items()))
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "Dataset",
                         "name": "Doomsday Cast Stats", "characters": total})
    return (page_head("Stats", "Cast breakdown by faction and universe.", "/explore/stats.html", jsonld)
            + "<body>" + site_nav("stats")
            + f'<header class="hero char-hero"><h1>Stats</h1>'
            + f'<p class="lede">{total} confirmed cast members.</p></header>'
            + '<main class="wrap">'
            + '<section class="card"><h2>By Faction</h2>' + bars_unit + "</section>"
            + '<section class="card"><h2>By Universe</h2>' + bars_uni + "</section>"
            + "</main>" + foot()
            + '<script src="../assets/js/main.js"></script></body></html>')


def build_all():
    doc = load()
    EXPLORE.mkdir(exist_ok=True)
    written_emblems = build_emblems(doc)
    print(f"  wrote {written_emblems} character emblems to assets/img/")
    (EXPLORE / "characters.html").write_text(build_characters(doc), encoding="utf-8")
    (EXPLORE / "watch-guide.html").write_text(build_watch_guide(doc), encoding="utf-8")
    (EXPLORE / "timeline.html").write_text(build_timeline(doc), encoding="utf-8")
    (EXPLORE / "stats.html").write_text(build_stats(doc), encoding="utf-8")
    build_meta(doc)
    import build_mcu
    build_mcu.build_all()
    # Catalogue generator runs last so the final on-disk characters.html is the
    # full character catalogue (the 30-confirmed badge is preserved in it).
    import build_catalogue
    build_catalogue.build_all()


if __name__ == "__main__":
    build_all()
    print(f"explore generator ready — {len(load()['characters'])} characters in source")