# Doomsday Fan Hub

Static fan site for **Avengers: Doomsday** (Dec 18, 2026). Cinematic homepage + deep fan-service behind the Explore tier.

## Quick start

```bash
# Full deterministic rebuild (run from avengers-doomsday/)
python3 scripts/build_explore.py  # 1) emblems + explore/* + meta, then calls build_mcu
python3 scripts/test_site.py      # 2) link crawl + determinism
python3 scripts/test_explore.py   # 3) generator unit tests
```

Optional: `python3 scripts/fetch_images.py` (needs network; run from a shell with internet)

## Build pipeline

| Step | Script | Output | Notes |
|---|---|---|---|
| 1 | `build_explore.py` | `explore/characters.html`, `universes.html`, `watch-guide.html`, `timeline.html` (trivial), `stats.html`, `memorial.html`, `sitemap.xml`, `robots.txt`, `explore/404.html`, 30 SVG emblems | Loads `data/cast.json`; invokes `build_mcu.py` last |
| 2 | `build_mcu.py` | `explore/timeline.html` (full 40-entry rail), `watch-guide.html`, `stats.html`, `memorial.html` | Overwrites the trivial timeline + stats from step 1; reads `data/mcu.json` |
| 3 | `test_site.py` | — | Double-build + link crawl; fails on broken refs |
| 4 | `test_explore.py` | — | Unit tests for all generator helpers |

The on-disk `explore/timeline.html` is **always `build_mcu`'s output** — the one with the 40-entry alternating center rail, phase markers, solid/hollow status dots on the line, and the "Announced · Date TBA" block for Blade.

## Data sources

- `data/cast.json` — **source of truth** for characters: 30 verified cast members, each with actor/character split, unit/faction, universe, `watch_before` list, `appearances`, and `sources[]` with `verified_at` provenance. Bios are **not invented**; facts trace to sources.
- `data/mcu.json` — MCU reference dataset: `movies[38]`, `announced[3]` (Doomsday, Secret Wars, Blade TBA), `series[24]`, `defenders[13]`, `legacy_tv_shows`, `watch_routes`, `avengers_roster`, `memorial`, `meta`. Snapshot: **2026-08-30**.

## Key pages

| Path | Description |
|---|---|
| `index.html` | Homepage — hero, countdown, faction chooser, trailer, Intel Database (4 link cards) |
| `explore/timeline.html` | **40-entry center rail**: 38 released films + #39 Doomsday + #40 Secret Wars; alternating left/right cards; phase markers on the line; ● released / ○ announced status dots riding the rail; sticky scroll-tracking ball; "Announced · Date TBA" section for Blade |
| `explore/watch-guide.html` | Three routes: Essential (numbered), Complete MCU marathon (collapsible by phase), Series & character routes (per cast member) |
| `explore/stats.html` | Derived counts: confirmed cast, original/formal/new Avengers, announced participants, fallen heroes; bar charts by faction & universe; Avengers roster history accordions |
| `explore/memorial.html` | Fallen heroes in three grids: Forever Remembered, Guardians & Allies, Of Wakanda/Asgard/Earth |
| `explore/characters.html` | Search/filter grid of 30 cast cards (unit pills, initials avatars) |
| `explore/universes.html` | Cast grouped by home universe (Earth-616, Earth-828, X-Men universe) |
| `pages/*.html` | 30 character pages — bios, intel `.kv` rows, watch paths, prev/next nav |

## Design system

- **Fonts**: Bebas Neue (display), Orbitron (UI/labels/countdown), Rajdhani (body), Inter (readable long-form)
- **Theme**: Dark cinematic (`--bg #020804`, `--surface #0a1a10`); `--accent` swaps per-faction via `body.faction-<slug>` (Avengers red, X-Men violet, Fantastic green, Wakandans gold, New Avengers blue, Villain green)
- **Timeline rail**: CSS custom properties `--p1…--p6` for phase colors; `.tl-rail::before` = continuous center line; `.tl-node` = per-event status dot on the line; `.tl-track-dot` = sticky scroll ball; mobile collapses to single column (line + nodes at 18px)
- **Intel `.kv` rows** (character pages): compact data-table look, uppercase keys, tabular-nums values, hover → `translateX(3px)` + accent left border

## Tests

All suites must pass before shipping:

```bash
python3 scripts/test_site.py
python3 scripts/test_explore.py
```

Output ends with `ALL … TESTS PASS`. The site test is a **double-build + full link crawl** — deterministic byte output and no broken internal refs.

## License

Avengers: Doomsday © Marvel Studios / Disney. This is a fan project, not affiliated.
