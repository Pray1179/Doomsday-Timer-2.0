#!/usr/bin/env python3
"""Doomsday Fan Hub — MCU timeline / roster / memorial generator.

Reads data/mcu.json (MCU release-order reference) plus data/cast.json and emits:
  - explore/timeline.html   (full MCU release timeline: films, series, legacy, announced)
  - explore/watch-guide.html (3-section collapsible guide, data-driven)
  - explore/stats.html       (derived Avengers counts + roster history + memorial link)
  - explore/memorial.html    (fallen heroes)

Imports the shared page/nav/foot helpers from build_explore. Pure stdlib, deterministic.
"""
import json
from datetime import date
from pathlib import Path

import build_explore as ex  # shared esc / page_head / site_nav / foot / load
import catalogue_util as cu  # shared catalogue record loader / continuity colours

ROOT = Path(__file__).resolve().parent.parent
MCU = ROOT / "data" / "mcu.json"
E_ = ex.esc


def load_mcu():
    with open(MCU, encoding="utf-8") as f:
        return json.load(f)


def fmt_date(iso):
    """2026-12-18 -> 'Dec 18, 2026'."""
    try:
        y, m, d = map(int, iso.split("-"))
        return date(y, m, d).strftime("%b %-d, %Y")
    except Exception:
        return iso or "—"


# ---------------------------------------------------------------- timeline

def _phase_index(phase):
    """Map a 'Phase N' label to a 1-based integer for the CSS hook.

    Data uses word numerals ('Phase One'), so resolve both words and digits.
    """
    word = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    low = str(phase).strip().lower()
    for w, n in word.items():
        if w in low:
            return str(n)
    digits = "".join(ch for ch in low if ch.isdigit())
    return digits if digits else "0"


# Solid/hollow status marker. Status is encoded as SHAPE (filled vs ring) and
# COLOR, never color alone — the dot glyph itself carries the released/unreleased
# distinction so it survives for non-sighted users (the legend text repeats it).
def _status_marker(released, color_class=""):
    if released:
        # ● solid dot in the phase color (color_class sets the tint via CSS)
        return f'<span class="mv-marker mv-released {color_class}" aria-hidden="true">●</span>'
    # ○ hollow amber-outline dot for announced / unreleased
    return f'<span class="mv-marker mv-announced" aria-hidden="true">○</span>'


def _tl_phase(phase, saga, year):
    """Compact centered phase marker sitting on the center rail."""
    idx = _phase_index(phase)
    return (f'<div class="tl-phase phase-{idx}"><span class="tl-phase-name">{E_(phase)}</span>'
            f'<span class="tl-phase-saga">{E_(saga)}</span>'
            f'<span class="tl-phase-year">{year}</span></div>')


def _tl_item(m, side, released=True, href=None, num=None):
    """One alternating card on the center rail with a status node on the line.

    side is "l" (left) or "r" (right). released controls the ANNOUNCED badge +
    amber styling AND the node glyph (● released / ○ announced). href wraps the
    card in a link (used for announced titles). The node sits at left:50% on the
    center rail; the card takes half the rail width minus a gap so the node
    always has a clear corridor.
    """
    idx = _phase_index(m["phase"])
    phase_cls = f"phase-{idx}"
    side_cls = "tl-left" if side == "l" else "tl-right"
    ann_cls = "" if released else " announced"
    num_span = f'<span class="tl-num">{num:02d}</span>' if num else '<span class="tl-num">—</span>'
    badge = "" if released else '<span class="badge upcoming">ANNOUNCED</span>'
    date_lbl = fmt_date(m["release_date"]) if released else fmt_date(m.get("expected_date", ""))
    # Status node: solid (●) for released, hollow (○) for announced — placed on
    # the center rail via CSS (.tl-node at left:50%, transformX(-50%)). Shape
    # encodes state first; color is the phase accent for released, amber for
    # announced — never color alone.
    node_cls = f"tl-node {'mv-released' if released else 'mv-announced'}"
    node_glyph = "●" if released else "○"
    node_span = f'<span class="{node_cls}" aria-hidden="true">{node_glyph}</span>'
    # Title row (with the ANNOUNCED chip, when unreleased) + a meta row for
    # date + phase badge. Identical structure for released and announced cards
    # so unreleased entries keep the same clean geometry as the rest of the rail.
    # Poster thumbnail — a real film poster where we have one (Secret Wars &
    # Blade have no published art yet, so their cards render text-only). The
    # alt text keeps the poster meaningful rather than decorative.
    poster = (f'<div class="tl-media"><img src="{m["poster_url"]}" '
              f'alt="{E_(m["title"])} theatrical poster" loading="lazy"></div>'
              if m.get("poster_url") else "")
    head = (f'<div class="tl-head"><h3 class="tl-title">{E_(m["title"])}</h3>'
            f'{badge}</div>')
    card = (
        f'<div class="tl-card{ann_cls} {phase_cls}">'
        f'{num_span}'
        f'{poster}'
        f'<div class="tl-body">{head}'
        f'<div class="tl-meta"><span class="tl-date">{date_lbl}</span>'
        f'<span class="badge tl-phase-badge">{E_(m["phase"])}</span></div>'
        f'<p class="muted tl-blurb">{E_(m.get("blurb", ""))}</p></div>'
        f'</div>')
    if href:
        return f'<div class="tl-item {side_cls}">{node_span}<a class="tl-link" href="{href}">{card}</a></div>'
    return f'<div class="tl-item {side_cls}">{node_span}{card}</div>'


def _is_dated(a):
    """True if an announcement has a real release date (not Date TBA)."""
    d = str(a.get("expected_date", "")).strip().lower()
    return bool(d) and "tba" not in d


def _merge_entries(movies, announced):
    """Flatten films + DATED announced titles into a single rail sequence.

    Yields ("phase", info) and ("item", m) tuples. Dated announcements (Doomsday,
    Secret Wars) fall after the last released film and are appended at the end,
    numbered continuing from the film count (39, 40). Undated ("TBA") announcements
    — Blade — are deliberately EXCLUDED here: they have no numbered slot on the
    rail and are rendered in their own Date TBA block in build_timeline. The
    left/right alternation is driven by the caller counting ITEMS only, so phase
    markers never break the rhythm.
    """
    dated = [a for a in announced if _is_dated(a)]
    entries = []
    prev_phase = None
    for m in movies:
        if m["phase"] != prev_phase:
            entries.append(("phase", m))
            prev_phase = m["phase"]
        entries.append(("item", m))
    for a in dated:
        if prev_phase != a.get("phase"):
            entries.append(("phase", a))
            prev_phase = a.get("phase")
        entries.append(("item", a))
    return entries


def _undated_announced(announced):
    """Announcements with no set date (Date TBA), e.g. Blade."""
    return [a for a in announced if not _is_dated(a)]


def _build_tl_rail(movies, announced):
    lis = ["<div class=\"tl-track\" aria-hidden=\"true\">"
           "<span class=\"tl-track-bar\"></span>"
           "<span class=\"tl-track-dot\"></span></div>"]
    side = "r"  # next item goes right first, then alternates
    side_for = {"l": "l", "r": "r"}
    num = 0
    for kind, m in _merge_entries(movies, announced):
        if kind == "phase":
            # phase-year: use release year for films, expected year for announced
            y = m.get("release_date", m.get("expected_date", ""))[:4]
            lis.append(_tl_phase(m["phase"], m.get("saga", ""), y))
            continue
        num += 1
        released = "expected_date" not in m
        href = None
        if not released:
            href = f'https://www.marvel.com/movies/{m["title"].lower().replace(" ","-").replace("*","")}'
        lis.append(_tl_item(m, side_for[side], released=released, href=href, num=num))
        side = "l" if side == "r" else "r"
    return "".join(lis)


def _series_bundle(title, items, phase_field=True):
    rows = []
    for s in items:
        d = s.get("release_date", s.get("year", ""))
        rows.append(f'<div class="sr-item"><span class="sr-title">{E_(s["title"])}</span>'
                    f'<span class="sr-date">{E_(d)}</span>'
                    + (f'<span class="badge">{E_(s.get("phase", ""))}</span>' if phase_field and s.get("phase") else "")
                    + (f'<span class="muted">{E_(s.get("blurb", ""))}</span>' if s.get("blurb") else "")
                    + "</div>")
    return (f'<details class="acc"><summary>{E_(title)} <span class="count">({len(items)})</span></summary>'
            f'<div class="acc-body">{"".join(rows)}</div></details>')


def build_timeline(cast_doc):
    mcu = load_mcu()
    films = mcu["movies"]
    announced = mcu["announced"]
    series = mcu["series"]
    defenders = mcu["defenders"]
    legacy = mcu["legacy_tv_shows"]
    meta = mcu["meta"]

    # One continuous center rail — released films and DATED announced titles merged,
    # no separate "Upcoming" section. The rail is exactly 38 films + #39 Doomsday +
    # #40 Secret Wars. Undated announcements (Blade) are held out into their own
    # "Announced · Date TBA" block below, never given a numbered slot on the rail.
    rail = _build_tl_rail(films, announced)
    rail_count = len(films) + len([a for a in announced if _is_dated(a)])

    # Shared legend — shows BOTH encodings (phase color + status shape) so the
    # timeline is legible without relying on color alone.
    legend = (
        '<div class="mv-legend" role="img" aria-label="Phase colors: I gold, II steel blue, '
        'III crimson, IV violet, V emerald, VI electric cyan. Status: solid dot means released, '
        'hollow dot means announced or unreleased.">'
        '<div class="lg-row lg-phases">'
        '<span class="lg-item p1">PHASE I <b>gold</b></span>'
        '<span class="lg-item p2">II <b>blue</b></span>'
        '<span class="lg-item p3">III <b>red</b></span>'
        '<span class="lg-item p4">IV <b>violet</b></span>'
        '<span class="lg-item p5">V <b>green</b></span>'
        '<span class="lg-item p6">VI <b>cyan</b></span>'
        '</div>'
        '<div class="lg-row lg-status">'
        '<span class="lg-item"><span class="lg-dot filled">●</span> RELEASED</span>'
        '<span class="lg-item"><span class="lg-dot hollow">○</span> ANNOUNCED / UNRELEASED</span>'
        '</div>'
        '</div>')

    # Legacy TV — flat grid
    legacy_rows = "".join(
        f'<div class="sr-item"><span class="sr-title">{E_(l["title"])}</span>'
        f'<span class="sr-date">{E_(l.get("year", ""))} · {E_(l.get("network", ""))} · S{l.get("seasons","—")}</span></div>'
        for l in legacy)

    src = mcu["sources"]
    source_note = " · ".join(
        f'<a href="{v["url"]}">{E_(v["label"])}</a>' for v in src.values())

    tba = _undated_announced(announced)
    tba_rows = "".join(
        f'<div class="sr-item"><span class="sr-title">{E_(a["title"])}</span>'
        f'<span class="sr-date">Date TBA</span>'
        + (f'<span class="badge">{E_(a.get("phase", ""))}</span>' if a.get("phase") else "")
        + (f'<span class="muted">{E_(a.get("blurb", ""))}</span>' if a.get("blurb") else "")
        + "</div>" for a in tba)

    html = (ex.page_head("Timeline", "Full MCU release timeline, 2008 to now.",
                         "/explore/timeline.html")
            + "<body>" + ex.site_nav("timeline")
            + f'<header class="hero char-hero"><h1>Timeline</h1>'
            + f'<p class="lede">The Marvel Cinematic Universe in release order — {len(films)} films from Iron Man (2008) to now, plus the announced multiversal double-bill.</p></header>'
            + '<main class="wrap">'

            + f'<section><h2>Release Timeline <span class="count">({rail_count})</span></h2>'
            + f'<p class="muted">{E_(meta["note"])}</p>'
            + legend
            + f'<div class="tl-rail">{rail}</div></section>'

            + (f'<section><h2>Announced · Date TBA</h2>'
               f'<p class="muted">Officially announced — no date set yet.</p>'
               f'<div class="sr-list">{tba_rows}</div></section>'
               if tba_rows else "")

            + '<section><h2>Series &amp; Specials</h2>'
            + _series_bundle("Disney+ series & specials", series)
            + _series_bundle("Defenders Saga — legacy, officially reintegrated", defenders, phase_field=False)
            + "</section>"

            + '<section><h2>Legacy Marvel Television <span class="badge">canon status uncertain</span></h2>'
            + f'<p class="muted">{E_(mcu["legacy_tv"]["note"])}</p>'
            + f'<div class="sr-list">{legacy_rows}</div></section>'

            + f'<footer class="foot"><a href="../index.html">↑ Back to the hub</a>'
            + f'<p style="margin-top:0.5rem;font-size:0.75rem">Snapshot {E_(meta["snapshot_date"])} · {source_note}</p></footer>'
            + "</main>"
            + '<script src="../assets/js/main.js"></script></body></html>')
    return html


# ---------------------------------------------------------------- watch guide

def _poster_for(poster_map, title):
    """Look up a movie poster URL for a filmography title.

    Filmography titles carry a trailing year ("Iron Man (2008)") while the
    poster map is keyed by plain movie title ("Iron Man"). Strip the year
    (and any " — Season N" suffix, for TV entries, which simply won't match)
    to resolve the poster lookup.
    """
    if not poster_map:
        return ""
    url = poster_map.get(title)
    if url:
        return url
    base = title
    year_idx = base.rfind(" (")
    if year_idx != -1 and base.endswith(")"):
        base = base[:year_idx]
    dash = base.find(" — ")
    if dash != -1:
        base = base[:dash]
    return poster_map.get(base, "")


def _route_item(item, numbered=True, poster_map=None):
    """Render a route item with optional poster thumbnail."""
    n = f'<span class="r-n">{item.get("n", "▶")}</span>' if numbered else ""
    why = f'<span class="r-why muted">{E_(item.get("why", ""))}</span>' if item.get("why") else ""
    when = f'<span class="r-when badge">{E_(item.get("when", ""))}</span>' if item.get("when") else ""
    poster = ""
    # An item may carry its own poster_url (e.g. Loki, a series outside the
    # film poster map); fall back to the film map keyed by exact title.
    poster_url = item.get("poster_url", "") or (poster_map or {}).get(item.get("title", ""), "")
    if poster_url:
        poster = f'<img class="r-poster" src="{poster_url}" alt="{E_(item["title"])}" loading="lazy">'
    li_class = 'r-item r-item-poster' if poster else 'r-item'
    return f'<li class="{li_class}">{poster}{n}<div class="r-body"><span class="r-title">{E_(item["title"])}</span>{when}{why}</div></li>'


def _phase_marathon(movies):
    """Movie marathon grouped by phase, each phase a <details class="acc">."""
    phases = []
    order = []
    for m in movies:
        if m["phase"] not in order:
            order.append(m["phase"])
    for ph in order:
        items = [m for m in movies if m["phase"] == ph]
        body = "".join(
            (f'<li class="r-item r-item-poster"><img class="r-poster" src="{m["poster_url"]}" '
             f'alt="{E_(m["title"])}" loading="lazy">'
             if m.get("poster_url") else '<li class="r-item">')
            + f'<span class="r-n">{m["n"]:02d}</span>'
            f'<div class="r-body"><span class="r-title">{E_(m["title"])}</span>'
            f'<span class="r-when badge">{fmt_date(m["release_date"])}</span></div></li>'
            for m in items)
        phases.append(f'<details class="acc"><summary>{E_(ph)} <span class="count">({len(items)})</span></summary>'
                      f'<ol class="route">{body}</ol></details>')
    return "".join(phases)


def _char_route(c, poster_map=None):
    ch = c["character"]
    app = [E_(w) for w in (ch.get("appearances") or [])]
    film_li = ""
    if app:
        for i, w in enumerate(app, 1):
            poster = ""
            poster_url = _poster_for(poster_map, w)
            if poster_url:
                poster = f'<img class="wg-poster" src="{poster_url}" alt="{E_(w)}" loading="lazy">'
            film_li += f"<li>{poster}<span class='wg-n'>{i:02d}</span><span class='wg-t'>{w}</span></li>"
    else:
        film_li = "<li>No filmography logged yet</li>"
    watch = [E_(w) for w in (ch.get("watch_before") or [])]
    watch_li = "".join(f"<li>{w}</li>" for w in watch) if watch else "<li>No essential list yet</li>"
    first = c["actor"].get("mcu_first_appearance", "—")
    latest = ch.get("latest_appearance", "—")
    return (f'<details class="acc"><summary><a href="../pages/{c["slug"]}.html">{E_(ch["name"])}</a>'
            f' <span class="muted">({E_(c["actor"]["name"])} · {E_(c["unit"])})</span></summary>'
            f'<div class="acc-body">'
            f'<p class="muted">First seen: {E_(first)} · Latest: {E_(latest)} · {len(app)} total appearances</p>'
            f'<h4 class="wg-sub">Complete filmography</h4>'
            f'<ol class="wg-film">{film_li}</ol>'
            f'<h4 class="wg-sub">Essential before Doomsday</h4>'
            f'<ul class="watch">{watch_li}</ul>'
            f'</div></details>')


def _og_route(rec, poster_map=None, label="Original Avenger"):
    """Per-cast route described by a catalogue record.

    Renders the same accordion shape as _char_route but from catalogue fields
    (id, related_titles, debut_title), linking through to the detail page.
    `label` is the muted tag shown next to the name (e.g. "Original Avenger"
    or a unit name like "Wakandans").
    """
    app = [E_(w) for w in (rec.get("related_titles") or [])]
    film_li = ""
    if app:
        for i, w in enumerate(app, 1):
            poster = ""
            poster_url = _poster_for(poster_map, w)
            if poster_url:
                poster = f'<img class="wg-poster" src="{poster_url}" alt="{E_(w)}" loading="lazy">'
            film_li += f"<li>{poster}<span class='wg-n'>{i:02d}</span><span class='wg-t'>{w}</span></li>"
    else:
        film_li = "<li>No filmography logged yet</li>"
    name = f'{rec["name"]} / {rec["alias"]}'
    who = rec.get("portrayed_by") or "—"
    first = rec.get("debut_title") or "—"
    summary = f'<p class="muted">{E_(rec.get("summary", ""))}</p>' if rec.get("summary") else ""
    cat_link = f'<a href="catalogue/{rec["id"]}.html">{E_(rec["name"])}</a>'
    return (f'<details class="acc"><summary>{cat_link}'
            f' <span class="muted">({E_(who)} · {E_(rec["alias"])} · {E_(label)})</span></summary>'
            f'<div class="acc-body">'
            f'<p class="muted">First seen: {E_(first)} · {len(app)} catalogue appearances</p>'
            f'{summary}'
            f'<h4 class="wg-sub">Complete filmography</h4>'
            f'<ol class="wg-film">{film_li}</ol></div></details>')


def build_watch_guide(cast_doc):
    mcu = load_mcu()
    essential = mcu["watch_routes"]["essential_before_doomsday"]
    films = mcu["movies"]
    team_routes = mcu["watch_routes"]["team_routes"]

    # Build poster lookup map for all movies + announced
    poster_map = {}
    for m in films:
        if m.get("poster_url"):
            poster_map[m["title"]] = m["poster_url"]
    for a in mcu.get("announced", []):
        if a.get("poster_url"):
            poster_map[a["title"]] = a["poster_url"]

    # Essential route numbered
    ess_items = [{"n": i + 1, **it} for i, it in enumerate(essential["items"])]
    ess_li = "".join(_route_item(it, poster_map=poster_map) for it in ess_items)

    # Team + cast routes grouped by unit
    units = ["Avengers", "X-Men", "Fantastic Four", "Wakandans", "New Avengers", "Villain"]
    team_extra = "".join(
        f'<details class="acc"><summary>{E_(team)} — shared route <span class="badge">TEAM</span></summary>'
        f'<ul class="watch">{"".join(f"<li>{E_(w)}</li>" for w in ws)}</ul></details>'
        for team, ws in team_routes.items())
    og_by_id = {r["id"]: r for r in cu.load_all()}
    unit_sections = []
    for u in units:
        members = sorted([c for c in cast_doc["characters"] if c["unit"] == u], key=lambda x: x["slug"])
        if not members:
            continue
        inner = "".join(_char_route(c, poster_map=poster_map) for c in members)
        # T'Challa isn't one of the confirmed 30-cast, but he's the iconic
        # Wakandan hero — fold his catalogue route into the Wakandans section.
        if u == "Wakandans" and "tchalla" in og_by_id:
            inner += _og_route(og_by_id["tchalla"], poster_map=poster_map, label="Wakandans")
        unit_sections.append(f'<details class="acc unit"><summary>{E_(u)} <span class="count">({len(members)})</span></summary>'
                             f'<div class="acc-body">{team_extra if u in team_routes else ""}{inner}</div></details>')

    # Original Avengers + key heroes not already represented in the confirmed
    # 30 cast route above. Captain America, Thor and Loki appear there via
    # their actors in the unit sections; Iron Man, Hulk, Black Widow and
    # Hawkeye do not and are covered here.
    og_extra = ["iron-man-tony-stark", "hulk-bruce-banner",
                "black-widow-natasha-romanoff", "hawkeye-clint-barton",
                "captain-america-steve-rogers", "thor"]
    og_routes = "".join(_og_route(og_by_id[i], poster_map=poster_map) for i in og_extra if i in og_by_id)
    og_section = (f'<details class="acc unit"><summary>Original Avengers &amp; Core Heroes'
                  f' <span class="count">({len([i for i in og_extra if i in og_by_id])})</span></summary>'
                  f'<div class="acc-body"><p class="muted">Captain America, Thor and Loki have '
                  f'confirmation-cast routes in the unit sections. The remaining core '
                  f'heroes are below.</p>'
                  f'{og_routes}</div></details>') if og_routes else ""

    html = (ex.page_head("Watch Guide", "Three routes to get ready for Doomsday.",
                         "/explore/watch-guide.html")
            + "<body>" + ex.site_nav("watch-guide")
            + '<header class="hero char-hero"><h1>Watch Guide</h1>'
            + '<p class="lede">Three routes — pick your depth. Everything collapses so you never face a wall of content.</p></header>'
            + '<main class="wrap">'

            + '<details class="acc open"><summary><span class="r-n">1</span>Essential before Doomsday <span class="count">(short)</span></summary>'
            + f'<div class="acc-body"><p class="muted">{E_(essential["note"])}</p><ol class="route">{ess_li}</ol></div></details>'

            + '<details class="acc"><summary><span class="r-n">2</span>Complete MCU movie marathon <span class="count">({0})</span></summary>'.format(len(films))
            + f'<p class="muted" style="padding:0 1.2rem">Every released theatrical film, 2008 → 2026.</p>'
            + _phase_marathon(films) + "</details>"

            + '<details class="acc"><summary><span class="r-n">3</span>Series &amp; character routes <span class="count">(per cast member)</span></summary>'
            + '<div class="acc-body">' + og_section + "".join(unit_sections) + "</div></details>"

            + "</main>"
            + '<script src="../assets/js/main.js"></script></body></html>')
    return html


# ---------------------------------------------------------------- stats

def _stat_card(label, value, sub, color="var(--accent-villain)"):
    return (f'<div class="stat-card"><div class="stat-big" style="color:{color}">{value}</div>'
            f'<div class="stat-l">{E_(label)}</div><div class="muted">{E_(sub)}</div></div>')


def _roster_era(era):
    bits = []
    for k, label in (("members", "Members"), ("core", "Core six"), ("assist", "Key allies"),
                     ("added", "Added"), ("removed", "Removed"), ("departed", "Departed"),
                     ("team_ironman", "Team Iron Man"), ("team_cap", "Team Cap"),
                     ("restored", "Restored")):
        if era.get(k):
            vals = era[k] if isinstance(era[k], list) else [era[k]]
            bits.append(f'<p class="muted"><strong>{label}:</strong> {E_("; ".join(vals))}</p>')
    note = f'<p class="muted">{E_(era.get("note", ""))}</p>' if era.get("note") else ""
    return (f'<details class="acc"><summary>{E_(era["era"])} <span class="badge">{E_(era.get("member_type", ""))}</span>'
            f'<span class="count muted"> · {E_(era.get("film", ""))}</span></summary>'
            f'<div class="acc-body">{note}{"".join(bits)}</div></details>')


def _count_unique(eras, keys=("members", "core", "assist", "added")):
    names = set()
    for e in eras:
        for k in keys:
            for v in e.get(k, []) if isinstance(e.get(k), list) else []:
                name = v.split(" (")[0].split(" / ")[0].strip()
                names.add(name)
    return len(names)


def build_stats(cast_doc):
    mcu = load_mcu()
    chars = cast_doc["characters"]
    total_cast = len(chars)

    # Full on-screen catalogue — every character, not just the confirmed 30.
    catalogue = cu.load_all()
    total_cat = len(catalogue)
    confirmed_in_cat = sum(1 for r in catalogue if r.get("doomsday_cast_slug"))

    # Continuity grouping over the whole catalogue (MCU, X-Men, legacy, …).
    cont_colors = dict(cu.CONTINUITY_COLORS)
    cont_colors.update({"Blade (trilogy)": "var(--accent-villain)",
                        "Sony's Spider-Man Universe": "var(--accent-fantastic)",
                        "Legacy TV": "var(--accent-newavengers)"})
    by_cont = {}
    for r in catalogue:
        by_cont[r.get("continuity", "Other")] = by_cont.get(r.get("continuity", "Other"), 0) + 1
    bars_cont = "".join(ex._bar(c, n, total_cat, cont_colors.get(c, "var(--accent-villain)"))
                        for c, n in sorted(by_cont.items()))

    # Team / affiliation grouping over the whole catalogue.
    by_team = {}
    for r in catalogue:
        for t in (r.get("team_or_affiliation") or []):
            by_team[t] = by_team.get(t, 0) + 1
    bars_team = "".join(ex._bar(t, n, total_cat, "var(--accent-fantastic)")
                        for t, n in sorted(by_team.items()) if n >= 2)

    # Character-type split over the whole catalogue.
    by_type = ex.counts_by(catalogue, lambda r: r.get("character_type", "Hero"))
    bars_type = "".join(ex._bar(t, n, total_cat, "var(--accent-villain)")
                        for t, n in sorted(by_type.items()))

    unit_colors = {"Avengers": "var(--accent-avengers)", "X-Men": "var(--accent-xmen)",
                   "Fantastic Four": "var(--accent-fantastic)", "Wakandans": "var(--accent-wakandans)",
                   "New Avengers": "var(--accent-newavengers)", "Villain": "var(--accent-villain)"}
    by_unit = ex.counts_by(chars, lambda c: c["unit"])
    by_uni = ex.counts_by(chars, lambda c: c["character"]["universe"])

    bars_unit = "".join(ex._bar(u, n, total_cast, unit_colors.get(u, "var(--accent-villain)"))
                        for u, n in sorted(by_unit.items()))
    bars_uni = "".join(ex._bar(u, n, total_cast, "var(--accent-fantastic)")
                       for u, n in sorted(by_uni.items()))

    eras = mcu["avengers_roster"]
    original_avengers = len(eras[0]["members"])           # the 2012 six
    formal_avengers = _count_unique([eras[0], eras[1]])   # founding + Ultron additions
    new_avengers = len(eras[6]["members"])                # Thunderbolts* New Avengers
    era_ann = [e for e in eras if e.get("member_type") == "announced"]
    ann_participants = era_ann[0] if era_ann else {"note": ""}
    fallen = (len(mcu["memorial"]["featured"]) + len(mcu["memorial"]["guardians_allies"])
              + len(mcu["memorial"]["world"]))

    roster_html = "".join(_roster_era(e) for e in eras)
    roster_intro = ("Every era where characters are explicitly shown as Avengers or a formal "
                    "Avengers roster. Allies and coalitions are labeled separately from the roster.")

    jsonld = json.dumps({"@context": "https://schema.org", "@type": "Dataset",
                         "name": "Doomsday Cast Stats", "characters": total_cat})

    return (ex.page_head("Stats", "Full on-screen character catalogue, derived Avengers counts and roster history.",
                         "/explore/stats.html", jsonld)
            + "<body>" + ex.site_nav("stats")
            + f'<header class="hero char-hero"><h1>Stats</h1>'
            + f'<p class="lede">{total_cat} on-screen characters catalogued · {total_cast} confirmed Doomsday cast.</p></header>'
            + '<main class="wrap">'

            # ---- Derived counts ---- #
            + '<section><h2>By the Numbers</h2><p class="muted">Counts derived from data — not hand-written.</p>'
            + '<div class="stat-grid">'
            + _stat_card("Characters catalogued", total_cat, "MCU, X-Men, Fantastic Four, Spider-Verse, legacy")
            + _stat_card("Confirmed Doomsday cast", total_cast, "from cast.json on-screen roster")
            + _stat_card("Original Avengers", original_avengers, "the 2012 founding six")
            + _stat_card("Formal Avengers ever", formal_avengers, "founding + Ultron-era additions")
            + _stat_card("New Avengers", new_avengers, "branded in Thunderbolts*")
            + _stat_card("Fallen heroes & allies", fallen, "honored in the Memorial")
            + '</div><p class="muted" style="margin-top:.5rem">'
            + f'{E_(ann_participants["note"])}</p></section>'

            # ---- Full catalogue breakdown ---- #
            + '<section class="card"><h2>Catalogue — By Continuity</h2>'
            + f'<p class="muted">All {total_cat} on-screen characters, grouped by their home continuity.</p>'
            + bars_cont + "</section>"
            + '<section class="card"><h2>Catalogue — By Type</h2>'
            + f'<p class="muted">Hero / villain / ally split across the full catalogue.</p>'
            + bars_type + "</section>"
            + '<section class="card"><h2>Catalogue — Leading Teams &amp; Affiliations</h2>'
            + f'<p class="muted">Teams with 2+ catalogue members.</p>'
            + bars_team + "</section>"

            # ---- Confirmed-30 cast focus ---- #
            + '<section class="card"><h2>Doomsday Cast — By Faction</h2>' + bars_unit + "</section>"
            + '<section class="card"><h2>Doomsday Cast — By Universe</h2>' + bars_uni + "</section>"

            # ---- Roster history ---- #
            + f'<section><h2>Avengers Roster History</h2><p class="muted">{roster_intro}</p>'
            + roster_html + "</section>"

            + '<section class="card cta-row"><p>Honor those lost across the eras.</p>'
            + '<a class="btn btn-primary" href="memorial.html">Visit the Memorial</a></section>'

            + "</main>"
            + '<script src="../assets/js/main.js"></script></body></html>')


# ---------------------------------------------------------------- memorial

def _mem_initials(m):
    return "".join(w[0] for w in m["name"].replace(" / ", " ").split()[:2]).upper()


def _mem_local_img(cid):
    """Return relative path to local catalogue photo if it exists, else None."""
    if not cid:
        return None
    img = ROOT / "assets" / "img" / f"cat-{cid}.jpg"
    if img.exists():
        return f"../assets/img/cat-{cid}.jpg"
    return None


def _mem_card(m, small=False):
    cls = E_(m["class"])
    cid = m.get("catalogue_id")
    local = _mem_local_img(cid)
    img_url = local or m.get("image_url")
    if img_url:
        face = (f'<div class="mem-img{" small" if small else ""}">'
                f'<img src="{E_(img_url)}" alt="{E_(m["name"])}" loading="lazy" '
                f'onerror="this.parentNode.classList.add(\'noimg\');this.remove()">'
                f'<span class="mem-initials">{E_(_mem_initials(m))}</span></div>')
    else:
        face = f'<div class="mem-img small"><span class="mem-initials">{E_(_mem_initials(m))}</span></div>'
    body = (f'{face}'
            f'<h3>{E_(m["name"])}</h3>'
            f'<p class="mem-alias muted">{E_(m["alias"])}</p>'
            f'<span class="mem-status">{E_(m["status"])}</span>'
            f'<p class="muted mem-how">{E_(m["how"])}</p>'
            f'<p class="mem-where muted">{E_(m["appears_in"])}</p>')
    cid = m.get("catalogue_id")
    if cid:
        href = f'catalogue/{E_(cid)}.html'
        body += f'<a class="mem-more" href="{href}">Character page &rarr;</a>'
    return f'<div class="mem-card {cls}{" small" if small else ""}" tabindex="0">{body}</div>'


def build_memorial_page():
    mcu = load_mcu()
    mem = mcu["memorial"]
    featured = "".join(_mem_card(m) for m in mem["featured"])
    # Secondary rosters — Guardians' lab animals and solo-film allies. Kept
    # smaller (compact portrait cards) beneath the core fallen heroes.
    guardians = "".join(_mem_card(m, small=True) for m in mem["guardians_allies"])
    world = "".join(_mem_card(m, small=True) for m in mem["world"])

    return (ex.page_head("Memorial", "Remembering the heroes lost across the MCU.",
                         "/explore/memorial.html")
            + "<body>" + ex.site_nav("memorial")
            + '<header class="hero char-hero mem-hero"><h1>Memorial</h1>'
            + f'<p class="lede">In memory of the fallen. {E_(mem["intro"])}</p></header>'
            + "<main class=\"wrap\">"
            + '<section><h2>Original Avengers &amp; Core Fallen</h2>'
            + f'<div class="mem-grid">{featured}</div></section>'
            + "<section><h2>Also Fallen &mdash; Guardians' Friends</h2>"
            + f'<div class="mem-grid mem-grid-small">{guardians}</div></section>'
            + '<section><h2>Also Fallen — Across the Multiverse</h2>'
            + f'<div class="mem-grid mem-grid-small">{world}</div></section>'
            + '<section class="card"><p class="muted">A note on statuses: "Dead, but an alternate version exists" covers Loki and Gamora, '
            + 'whose variants live on in other timelines. "Bodily dead / active as a ghost" reflects Vision, whose original body was destroyed '
            + 'while White Vision continues. We do not label Blipped characters, fake-outs or unconfirmed deaths as gone.</p></section>'
            + "</main>"
            + '<script src="../assets/js/main.js"></script></body></html>')


def build_all():
    cast = ex.load()
    EXPLORE = ROOT / "explore"
    EXPLORE.mkdir(exist_ok=True)
    (EXPLORE / "timeline.html").write_text(build_timeline(cast), encoding="utf-8")
    (EXPLORE / "watch-guide.html").write_text(build_watch_guide(cast), encoding="utf-8")
    (EXPLORE / "stats.html").write_text(build_stats(cast), encoding="utf-8")
    (EXPLORE / "memorial.html").write_text(build_memorial_page(), encoding="utf-8")


if __name__ == "__main__":
    build_all()
    mcu = load_mcu()
    print(f"mcu generator ready — {len(mcu['movies'])} films, "
          f"{len(mcu['series'])} series, {len(mcu['memorial']['featured'])} memorial entries")
