# On-Screen Marvel Character Catalogue — Design

**Date:** 2026-08-30
**Status:** Awaiting review
**Scope owner:** Avengers: Doomsday fan hub (`avengers-doomsday/`)

## 1. Goal

Expand the site from a 30-confirmed Doomsday cast list into a **comprehensive,
image-rich, on-screen Marvel character catalogue** — a data-first subsystem that
covers MCU movies, Marvel Studios series/specials, and legacy-multiverse
characters that materially connect to the site. The system must **scale to
"every Marvel character ever created"** while the shipped milestone is
**honestly labelled** as *on-screen Marvel / MCU and multiverse coverage* — not
a claim of full comic-coverage.

Non-goals: editing `HackClaude_Project_Brief.md` or unrelated HackClaude
reference files; inventing identities, images, continuity, or claims.

## 2. Decisions (approved)

- **Catalogue size — Maximal:** initial milestone ~250+ on-screen characters.
- **Images — Official URL + SVG fallback:** record an official, clearly
  attributed `image_url` where confirmed; otherwise render the generated SVG
  initials portrait with an **"Image pending verification"** chip. Never a
  broken image icon.
- **Integration — Standalone + cross-links:** new `data/catalogue.json` and
  catalogue pages; existing `data/cast.json`, its generator(s), pages, and
  tests stay untouched. A character present in both datasets cross-links via
  `doomsday_cast_slug` → existing `pages/<slug>.html`.

## 3. Architecture

New files (existing `cast.json` / `build.py` / `build_explore.py` / `build_mcu.py`
remain untouched):

| Path | Purpose |
|---|---|
| `data/catalogue/*.json` (one per franchise group) | Batched source records; merged deterministically |
| `data/catalogue.json` (generated) | Merged, validated catalogue (the source of truth for pages/tests) |
| `scripts/build_catalogue.py` | Merge + strict validation + coverage report + page generation |
| `scripts/test_catalogue.py` | Automated validation assertions (fail-loud) |
| `explore/catalogue.html` | Search + filters + split count summary + card grid |
| `explore/catalogue/<id>.html` | Per-character detail page (generated) |
| `assets/js/catalogue.js` | Client-side search/filter (or inline `<script>`) |
| `assets/css/styles.css` | Catalogue card/detail/filter styles (added to existing file, braces balanced) |

`build_catalogue.py` does **not** call into `build_mcu.py`. It is an
independent generator. A `run_all` convenience (`build_catalogue.py` then
`build_explore.py`) is optional; the catalogue does not overwrite any existing
output.

## 4. Data schema

Each record — the user's required fields verbatim, plus a small filter/UX set:

```json
{
  "id": "peter-parker-mcu",
  "name": "Peter Parker",
  "alias": "Spider-Man",
  "aliases": ["Friendly Neighborhood Spider-Man"],
  "portrayed_by": "Tom Holland",
  "universe": "Earth-616 / MCU",
  "continuity": "MCU",
  "team_or_affiliation": ["Avengers"],
  "character_type": "Hero",
  "tags": ["spider-man", "avengers", "mcu"],
  "status": "Active",
  "debut_title": "Captain America: Civil War (2016)",
  "debut_year": 2016,
  "summary": "…",
  "image_url": "",
  "image_source_url": "",
  "image_source_name": "",
  "image_alt": "Tom Holland as Spider-Man",
  "image_verified": false,
  "source_notes": [],
  "related_titles": [],
  "allies": [],
  "enemies": [],
  "verified": true,
  "notes": "",
  "doomsday_cast_slug": null
}
```

### Field rules

- `id` — lowercase kebab, required, unique.
- `name` / `alias` / `debut_title` / `summary` — required.
- `universe` — display label (e.g. `Earth-616 / MCU`, `Earth-96283 (Raimi)`,
  `Earth-120703 (Webb)`, `Earth-10005 (X-Men)`, `Venomverse`, `Legacy TV`).
- `continuity` — canonical grouping key used for the split counts
  (`MCU`, `Raimi`, `Webb`, `X-Men`, `SSU`/Venomverse, `Legacy TV`, `Fantastic Four`,
  `Other multiverse`, …). A character belongs to **one** continuity.
- `character_type` — `Hero` | `Villain` | `Ally` | `Anti-hero` | `Team-support` |
  `Neutral` (free-form string, but the UI filter lists these).
- `tags` — cross-cutting membership for counting and filters
  (`spider-man`, `x-men`, `fantastic-four`, `avengers`, `guardians`,
  `wakandans`, `defenders`, `new-avengers`, `thunderbolts`, `villain`,
  `multiverse`, `mcu`, …). A character may carry many tags.
- `status` — `Active` | `Deceased` | `MIA` | `Variant` | `Legacy`.
- `image_*` — see §5. `image_verified` false → SVG fallback + pending chip.
- `verified` — data-confidence. `false` → rendered with an explicit
  "unverified / continuity-uncertain" marker, kept separate from confirmed canon.
- `source_notes[]` — provenance / uncertainty notes; joins with any
  `sources[{url,publisher,verified_at}]` at the record level (schema allows a
  top-level `sources[]` too).
- `doomsday_cast_slug` — set when this character maps to an existing
  `pages/<slug>.html` (e.g. Thor → `chris-hemsworth`). Renders a cross-link.

### Variants

Variants are **separate records by construction** — one `id` per actor /
continuity. No merging of the three live-action Peter Parkers, main Loki vs
TVA Loki vs variant Lokis, or main-timeline Gamora vs the 2014 variant. Variant
records set `status:"Variant"` and a `notes` clause describing the branch.

## 5. Images

Given the sandbox reaches only `en.wikipedia.org`, `www.marvel.com`, `r.jina.ai`,
`deadline.com`, `api.bilibili.com` (not `cdn.marvel.com` / `upload.wikimedia.org`):

- Every character gets a generated SVG initials portrait (reusing the existing
  `_emblem_svg` monogram pattern, **extended to also read `image_verified`**).
- When an **official, clearly attributed** `image_url` is recorded (Marvel
  official pages/studio press first; Wikipedia file page as clearly-attributed
  reliable fallback), we also store `image_source_url` + `image_source_name` +
  `image_alt` and render:
  `<img src="{url}" alt="{image_alt}" loading="lazy" width="…" height="…"
  onerror="this.remove()">` with the SVG sitting behind it.
- If `image_verified` is false or `image_url` is empty → the SVG initials
  portrait shows with an **"Image pending verification"** chip. `onerror`
  removal guarantees a broken image can never display.
- No random Google Images, uncredited fan art, or AI-generated portraits.

## 6. Interface

`explore/catalogue.html`:
- **Search** input (name, alias, portrayed_by, team, summary).
- **Filter groups:** Universe (continuity), Team (team_or_affiliation), Type
  (character_type). Filter chips + a clear-all.
- **Compact count summary**, split rather than one vague total:
  - Total distinct characters
  - MCU · legacy/multiverse · Spider-Man-related · X-Men · Fantastic Four
    (computed via tags; the UI shows "of which" membership, noting overlaps).
- **Card grid**: SVG/photo portrait, name, alias, universe/continuity chip,
  status dot, tags; card links to the detail page. Cards with unverified images
  show the pending chip.
- **"30 confirmed Doomsday cast" stays separate**: the existing
  `explore/characters.html` (and its badge) is untouched; the catalogue card
  for a Doomsday-confirmed character shows a "Confirmed for Doomsday" cross-link
  to that page.

`explore/catalogue/<id>.html` detail page: identity (name/alias/portrayed_by),
universe + continuity, character_type + status, debut title, key/related titles,
allies / enemies, image with **image-source attribution** (source name + page
link), summary, source_notes/notes (including uncertainty markers), tags,
prev/next nav, and the Doomsday-cast cross-link when present.

Preserve the existing dark cinematic green/teal design system.

## 7. Validation & coverage report

`scripts/test_catalogue.py` (and a `--report` mode on the generator) checks:
- JSON well-formedness; duplicate `id`; slug shape; required fields present.
- `image_alt` present whenever `image_url` is set; `image_source_url` +
  `image_source_name` present whenever `image_url` is set.
- `image_url` scheme is `https` (no protocol-relative/broken forms).
- No broken **local** asset references (SVG emblems exist for catalogue pages;
  cross-link targets exist).
- Determinism: double-run byte-identical (no timestamps/randomness).

Coverage report output includes: character count; image count (any `image_url`);
verified-image count (`image_verified:true`); pending-image count; Spider-Man-
related count; and the MCU / legacy-multiverse / X-Men / Fantastic Four split.

## 8. Population plan (batches, each grounded with sources)

Populated into `data/catalogue/*.json` by franchise group:
1. Doomsday-confirmed 30 (cross-linked) + core MCU Avengers/Earth-616.
2. Guardians & cosmic (incl. 2014 Gamora variant).
3. Spider-Man full spider-verse (MCU, Raimi, Webb, Miles, Gwen, symbiotes,
   allies & villains).
4. Fantastic Four + Doctor Doom.
5. X-Men film universe (plus Wolverine/Deadpool-adjacent).
6. Wakandans + Talokan + Black Panther cast.
7. Defenders / Marvel TV (Netflix, plus legacy live-action).
8. New Avengers / Thunderbolts / Valentina.
9. Magic & multiverse (Strange, Wanda, Loki/TVA, Kang, Eternals, Shang-Chi,
   Ant-Man/quantum).
10. Major villains & supporting allies across all groups; legacy multiverse
    (Ghost Rider, Blade, older F4/X-Men/Spider) to reach ~250+.

Uncertain material (vague continuity, unreleased plot assumptions) gets
`verified:false` + a `source_notes` clause and is labeled separately from
confirmed canon.

## 9. Tests

- Existing `test_site.py`, `test_explore.py`, `test_knowledge.py` must still pass
  (the catalogue generator is additive and non-overwriting).
- New `test_catalogue.py` must pass (ALL … TESTS PASS) before shipping.
- `sitemap.xml` / `robots.txt` updated to include catalogue pages.

## 10. Open items for the plan

- Exact generated-detail-page count cap / pagination if >500 chars.
- Whether `catalogue.html` nav supersedes or supplements `characters.html`
  (default: supplements; `characters.html` stays the Doomsday-confirmed view).
