#!/usr/bin/env python3
"""Shared utilities for the character catalogue generator and tests."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_DIR = ROOT / "data" / "catalogue"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

REQUIRED = frozenset([
    "id", "name", "alias", "universe", "continuity",
    "team_or_affiliation", "status", "debut_title",
    "source_notes", "related_titles", "verified"
])

CONTINUITY_COLORS = {
    "MCU": "#e63946",
    "Raimi": "#3a7bd5",
    "Webb": "#3a7bd5",
    "SSU": "#1aa35c",
    "X-Men": "#9b5de5",
    "Fantastic Four": "#1aa35c",
    "Legacy TV": "#00cc55",
    "Multiverse": "#00b3cc",
}


def slug_ok(s: str) -> bool:
    return bool(SLUG_RE.match(s))


def esc(t) -> str:
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _shade(hexc: str, k: float) -> str:
    """Scale a #rrggbb colour by factor k (k<1 darkens toward black, k>1 lightens)."""
    c = hexc.lstrip("#")
    if len(c) != 6:
        return hexc
    vals = [max(0, min(255, round(int(c[i:i + 2], 16) * k))) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(vals)


def _initials(name: str) -> str:
    """Monogram letters, skipping filler words ("of", "the", "von", …)."""
    primary = name.split("/")[0].strip()
    toks = [t for t in primary.split()
            if t.lower() not in ("the", "of", "a", "an", "von", "van", "de", "da")]
    if not toks:
        return primary[:1].upper()
    if len(toks) == 1:
        return toks[0][0].upper()
    return (toks[0][0] + toks[1][0]).upper()


def initial_portrait(name: str, color: str) -> str:
    """Deterministic SVG dossier emblem for characters without a photo.

    Reads as an ID record (colour-tinted backdrop, soft halo, dashed orbit,
    viewfinder corner ticks, centred monogram) — not a generic white box.
    """
    init = _initials(name)
    safe_name = esc(name)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-label="{safe_name} emblem">
  <defs>
    <radialGradient id="bg" cx="50%" cy="40%" r="95%">
      <stop offset="0%" stop-color="{_shade(color, 0.24)}"/>
      <stop offset="55%" stop-color="{_shade(color, 0.09)}"/>
      <stop offset="100%" stop-color="#030608"/>
    </radialGradient>
    <radialGradient id="halo" cx="50%" cy="46%" r="52%">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="200" height="200" fill="url(#bg)"/>
  <circle cx="100" cy="102" r="80" fill="url(#halo)"/>
  <circle cx="100" cy="102" r="58" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.55"
          stroke-dasharray="1.5 9" stroke-linecap="round" transform="rotate(-90 100 102)"/>
  <text x="100" y="129" text-anchor="middle" font-family="'Arial Black','Helvetica Neue',Arial,sans-serif"
        font-size="54" font-weight="800" fill="#ffffff" letter-spacing="5">{init}</text>
  <g stroke="{color}" stroke-width="3" stroke-linecap="round" fill="none" opacity="0.85">
    <path d="M8 32 V8 H32"/>
    <path d="M192 32 V8 H168"/>
    <path d="M8 168 V192 H32"/>
    <path d="M192 168 V192 H168"/>
  </g>
</svg>"""


def load_all() -> list[dict]:
    """Load all catalogue batch files, concatenate, sort by id."""
    recs = []
    for p in sorted(CATALOGUE_DIR.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        chars = doc.get("characters", [])
        if isinstance(chars, list):
            recs.extend(chars)
    recs.sort(key=lambda r: r.get("id", ""))
    return recs


if __name__ == "__main__":
    recs = load_all()
    print(f"Loaded {len(recs)} records from {len(list(CATALOGUE_DIR.glob('*.json')))} files")
    for r in recs:
        print(f"  {r.get('id')}: {r.get('name')} ({r.get('continuity')})")