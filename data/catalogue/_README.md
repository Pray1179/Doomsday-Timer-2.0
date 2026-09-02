# Catalogue batch files

Each `*.json` file here is one franchise group and holds a single object:

```json
{
  "characters": [ /* array of catalogue records, see schema below */ ]
}
```

`scripts/build_catalogue.py` merges **every** `*.json` in this directory (in
sorted filename order), validates, and writes the single source of truth at
`data/catalogue.json` (generated — do not hand-edit). `_README.md` itself is
ignored because it is not `.json`.

## Record schema (fields every record must have)

```
id                   lowercase-kebab, unique across all files (e.g. "peter-parker-mcu")
name                 display name ("Peter Parker")
alias                primary alias ("Spider-Man")
aliases[]            extra aliases (optional)
portrayed_by         actor (optional)
universe             display label ("Earth-616 / MCU")
continuity           grouping key: MCU | Raimi | Webb | SSU | X-Men |
                     Fantastic Four | Legacy TV | Multiverse | Other
team_or_affiliation[]  teams/factions
character_type       Hero | Villain | Ally | Anti-hero | Team-support | Neutral
tags[]               cross-cutting: spider-man, x-men, fantastic-four, avengers,
                     guardians, wakandans, defenders, new-avengers, thunderbolts,
                     villain, multiverse, mcu, ...
status               Active | Deceased | MIA | Variant | Legacy
debut_title          first on-screen appearance, with year
debut_year           4-digit year (optional)
summary              one-to-two sentence description
image_url            official credited image (https only) or ""
image_source_url     source page the image came from
image_source_name    publisher label ("Marvel.com", "Wikipedia file page")
image_alt            descriptive alt text
image_verified       bool — false → SVG fallback + "Image pending" chip
source_notes[]       provenance / uncertainty notes
related_titles[]     key titles this character appears in
allies[] / enemies[] sibling catalogue ids where they exist
verified             bool — false → rendered with an "unverified" marker
notes                 extra uncertainty / variant note (optional)
doomsday_cast_slug   set only when this character maps to an existing
                     pages/<slug>.html (the 30-confirmed Doomsday cast)
sources[]            [{url, publisher, verified_at}]
```

Rules enforced by validation:

- `id` must match `^[a-z0-9]+(?:-[a-z0-9]+)*$` and be unique.
- All required fields present and non-empty.
- `image_url` set ⇒ must be `https://` and carry `image_alt`,
  `image_source_url`, `image_source_name`.
- Variants are **separate records** (one per actor/continuity) — never merge
  into one record.
- Uncertain continuity/identity ⇒ `verified:false` plus a `source_notes` clause.

## Current files

| File | Group |
|---|---|
| `doomsday-30.json` | 30 confirmed Avengers: Doomsday cast, cross-linked via `doomsday_cast_slug` |
| `mcu-avengers.json` | Core MCU / Earth-616 heroes |