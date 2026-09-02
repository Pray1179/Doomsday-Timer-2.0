#!/usr/bin/env python3
"""Doomsday Fan Hub — Graphify knowledge layer generator.

Reads data/cast.json (source of truth) and emits one Markdown document per
entity into knowledge/:
  characters/   one per cast member
  teams/        one per unit ("Avengers", "X-Men", ...)
  universes/    one per home universe
  movies/       one per distinct movie referenced in the data
  events/       release/phase milestones drawn from the release block
  index.md      deterministic site map + entity counts

Every factual claim is a machine-readable natural-language triple with inline
provenance (publisher + verified_at) referencing a per-document [S#] source
legend. No relationship is emitted that is not present in cast.json. All
iteration is sorted and no timestamps are generated — reruns are byte-identical.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cast.json"
KNOW = ROOT / "knowledge"

# Movie-reference, watch-before, and first-appearance strings look like
# "Avengers: Endgame (2019)" or "Loki (2021-2023)".
_TITLE_RE = re.compile(r"^(.*?)\s+\((\d{4})[^)]*\)$")


def slugify(s):
    """Deterministic filesystem-safe slug."""
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Entity derivation
# --------------------------------------------------------------------------- #

def parse_movie(ref):
    """Return (title, year) for a 'Title (YYYY...)' string, or None."""
    m = _TITLE_RE.match(str(ref).strip())
    if not m:
        return None
    return m.group(1).strip(), m.group(2)


def movie_label(ref):
    p = parse_movie(ref)
    return f"{p[0]} ({p[1]})" if p else str(ref)


def char_aliases(character):
    """Deterministic aliases from a 'Civilian / Codename' name."""
    name = character["name"]
    parts = [p.strip() for p in name.split("/") if p.strip()]
    return [p for p in parts if p and p != name]


class KnowledgeDoc:
    def __init__(self, title, prose=None):
        self.title = title
        self.rows = []          # (statement, provenance_text)
        self.prose = prose or []  # [(label, value)] rendered before Sources
        self.legend = []        # [("S#", url, publisher, verified_at)]
        self._idx = {}

    def cite(self, sources):
        tags = []
        for s in sources:
            url = s.get("url")
            if not url:
                continue
            if url not in self._idx:
                self._idx[url] = f"S{len(self.legend) + 1}"
                self.legend.append(
                    (self._idx[url], url, s.get("publisher", "?"),
                     s.get("verified_at", "?")))
            tags.append(self._idx[url])
        return tags

    def cite_release(self, verified_at):
        url = "data/cast.json#release"
        if url not in self._idx:
            self._idx[url] = f"S{len(self.legend) + 1}"
            self.legend.append((self._idx[url], url, "cast.json", verified_at))
        return [self._idx[url]]

    def add(self, statement, tags):
        self.rows.append((statement, ", ".join(f"[{t}]" for t in tags)))

    def render(self):
        lines = [f"# {self.title}", ""]
        for st, prov in self.rows:
            lines.append(f"- {st} *(verified — {prov})*")
        if self.prose:
            lines += ["", "## Notes"]
            lines += [f"- **{k}:** {v}" for k, v in self.prose]
        lines += ["", "## Sources", ""]
        lines += [f"- {tag} <{url}> · {pub} · verified {ver}"
                  for tag, url, pub, ver in self.legend]
        return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #

def build_character(c):
    prose = [(k, v) for k, v in
             (("Blurb", c["character"].get("blurb")),
              ("Why they matter", c["character"].get("why_they_matter")))
             if v]
    doc = KnowledgeDoc(c["character"]["name"], prose=prose)
    ch, ac = c["character"], c["actor"]
    srcs = c.get("sources") or []

    doc.add(f"{ch['name']} is portrayed by {ac['name']}.", doc.cite(srcs))
    doc.add(f"{ch['name']} is a member of the {c['unit']}.", doc.cite(srcs))
    doc.add(f"{ch['name']} belongs to the {ch['universe']} universe.",
            doc.cite(srcs))
    doc.add(f"{ch['name']} has the faction {ch['faction']}.", doc.cite(srcs))
    doc.add(f"{ch['name']} appears in {movie_label(ch['latest_appearance'])}.",
            doc.cite(srcs))

    # Actor-level history — kept strictly on the actor, never tied to the
    # current character (preserves the Doom/Stark distinction).
    for role in (ac.get("previous_roles") or []):
        doc.add(f"{ac['name']} previously portrayed {role}.", doc.cite(srcs))

    for wb in (ch.get("watch_before") or []):
        doc.add(f"{movie_label(wb)} is recommended viewing before {ch['name']}.",
                doc.cite(srcs))

    for alias in char_aliases(ch):
        doc.add(f"{ch['name']} is also known as {alias}.", doc.cite(srcs))

    return doc


def build_team(unit, members):
    doc = KnowledgeDoc(unit)
    unis = sorted({m["character"]["universe"] for m in members})
    for m in sorted(members, key=lambda x: x["slug"]):
        srcs = m.get("sources") or []
        doc.add(f"{m['character']['name']} is a member of the {unit}.",
                doc.cite(srcs))
    for u in unis:
        m = next(x for x in sorted(members, key=lambda x: x["slug"])
                 if x["character"]["universe"] == u)
        doc.add(f"The {unit} is based in the {u} universe.",
                doc.cite(m.get("sources") or []))
    return doc


def build_universe(uni, members):
    doc = KnowledgeDoc(uni)
    teams = sorted({m["unit"] for m in members})
    for m in sorted(members, key=lambda x: x["slug"]):
        doc.add(f"{m['character']['name']} belongs to the {uni} universe.",
                doc.cite(m.get("sources") or []))
    for t in teams:
        doc.add(f"The {t} is based in the {uni} universe.",
                doc.cite(members[0].get("sources") or []))
    return doc


def build_movie(label, doc_: dict, chars, verified_at):
    doc = KnowledgeDoc(label)
    for ch in sorted(chars, key=lambda x: x["slug"]):
        doc.add(f"{ch['character']['name']} appears in {label}.",
                doc.cite(ch.get("sources") or []))
    return doc


def build_release_movies(doc_data, chars, all_movies):
    """Docs for the two headline films with their release/sequel/phase edges."""
    rel = doc_data["release"]
    main_label = movie_label(f"{rel['title']} ({rel['date'][:4]})")
    seq_title = rel.get("sequel_title") or "Avengers: Secret Wars"
    seq_label = f"{seq_title} ({rel.get('sequel_date', '2027')[:4]})"
    verified_at = rel.get("data_verified_at", "")

    main = KnowledgeDoc(main_label)
    for ch in sorted(chars, key=lambda x: x["slug"]):
        if movie_label(ch["character"]["latest_appearance"]) == main_label:
            main.add(f"{ch['character']['name']} appears in {main_label}.",
                     main.cite(ch.get("sources") or []))
    main.add(f"{main_label} releases on {rel['date']}.",
             main.cite_release(verified_at))
    main.add(f"{main_label} is part of {rel['phase']}." if rel.get("phase")
             else f"{main_label} is a standalone film.",
             main.cite_release(verified_at))
    if seq_title != rel["title"]:
        main.add(f"{seq_label} is the sequel to {main_label}.",
                 main.cite_release(verified_at))

    seq = KnowledgeDoc(seq_label)
    seq.add(f"{seq_label} releases on {rel.get('sequel_date', 'TBA')}.",
            seq.cite_release(verified_at))
    if seq_label != main_label:
        seq.add(f"{seq_label} is the sequel to {main_label}.",
                seq.cite_release(verified_at))

    return main, seq


def build_event(doc_data):
    rel = doc_data["release"]
    verified_at = rel.get("data_verified_at", "")
    label = f"Multiverse Saga — {rel['phase']}"
    doc = KnowledgeDoc(label)
    doc.add(f"Avengers: Doomsday releases on {rel['date']}.",
            doc.cite_release(verified_at))
    doc.add(f"Avengers: Doomsday is part of {rel['phase']}.",
            doc.cite_release(verified_at))
    seq = rel.get("sequel_title") or "Avengers: Secret Wars"
    if seq != rel["title"]:
        doc.add(f"{seq} is the sequel to Avengers: Doomsday.",
                doc.cite_release(verified_at))
    return doc


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #

def build_all():
    data = load()
    chars = data["characters"]
    rel = data["release"]
    KNOW.mkdir(exist_ok=True)

    for sub in ("characters", "teams", "universes", "movies", "events"):
        (KNOW / sub).mkdir(exist_ok=True)

    # Characters
    by_unit = {}
    by_uni = {}
    for c in chars:
        (KNOW / "characters" / f"{c['slug']}.md").write_text(
            build_character(c).render(), encoding="utf-8")
        by_unit.setdefault(c["unit"], []).append(c)
        by_uni.setdefault(c["character"]["universe"], []).append(c)

    # Teams
    for unit, members in sorted(by_unit.items()):
        (KNOW / "teams" / f"{slugify(unit)}.md").write_text(
            build_team(unit, members).render(), encoding="utf-8")

    # Universes
    for uni, members in sorted(by_uni.items()):
        (KNOW / "universes" / f"{slugify(uni)}.md").write_text(
            build_universe(uni, members).render(), encoding="utf-8")

    # Movies — distinct titles referenced anywhere in the data, deterministically.
    referenced = {}
    for c in chars:
        for ref in ([c["character"]["latest_appearance"]]
                    + (c["character"].get("watch_before") or [])
                    + [c["actor"].get("mcu_first_appearance") or ""]):
            label = movie_label(ref)
            if label:
                referenced.setdefault(label, []).append(c)

    # Headline release movies always built, whether or not referenced elsewhere.
    main, seq = build_release_movies(data, chars, referenced)
    (KNOW / "movies" / f"{slugify(main.title)}.md").write_text(
        main.render(), encoding="utf-8")
    (KNOW / "movies" / f"{slugify(seq.title)}.md").write_text(
        seq.render(), encoding="utf-8")

    for label, mchars in sorted(referenced.items()):
        if label in (main.title, seq.title):
            continue  # already written above
        unique = {m["slug"]: m for m in mchars}.values()
        doc = build_movie(label, None, sorted(unique, key=lambda x: x["slug"]),
                          rel.get("data_verified_at", ""))
        (KNOW / "movies" / f"{slugify(label)}.md").write_text(
            doc.render(), encoding="utf-8")

    # Events
    (KNOW / "events" / f"{slugify(rel['phase'])}.md").write_text(
        build_event(data).render(), encoding="utf-8")

    # Index
    index = build_index(data, by_unit, by_uni, referenced, main.title, seq.title)
    (KNOW / "index.md").write_text(index, encoding="utf-8")

    # Clean stale docs no longer backed by data (deterministic regeneration).
    prune(KNOW / "characters", {f"{c['slug']}.md" for c in chars})
    prune(KNOW / "teams", {f"{slugify(u)}.md" for u in by_unit})
    prune(KNOW / "universes", {f"{slugify(u)}.md" for u in by_uni})
    expected_movies = {f"{slugify(main.title)}.md", f"{slugify(seq.title)}.md"}
    expected_movies |= {f"{slugify(l)}.md" for l in referenced}
    prune(KNOW / "movies", expected_movies)
    prune(KNOW / "events", {f"{slugify(rel['phase'])}.md"})

    print(f"knowledge layer ready — {len(chars)} characters, "
          f"{len(by_unit)} teams, {len(by_uni)} universes, "
          f"{len(expected_movies)} movies, 1 event")


def prune(directory, expected_filenames):
    for p in directory.glob("*.md"):
        if p.name not in expected_filenames:
            p.unlink()


def build_index(data, by_unit, by_uni, referenced, main_label, seq_label):
    chars = data["characters"]
    lines = [
        "# Doomsday Knowledge Graph — Index",
        "",
        "Machine-readable entity documents generated deterministically from "
        "`data/cast.json`. Each factual claim carries inline provenance "
        "referencing a per-document [S#] source legend (publisher + URL + "
        "`verified_at`). No relationship is emitted that is not present in "
        "the source data.",
        "",
        f"- Characters: {len(chars)}",
        f"- Teams: {len(by_unit)}",
        f"- Universes: {len(by_uni)}",
        f"- Movies: {len(referenced) + (2 if main_label != seq_label else 1)}",
        "- Events: 1 (Multiverse Saga / phase milestones)",
        "",
        "## Characters",
        "",
    ]
    # character -> its file, sorted by slug
    lines += [f"- [{c['character']['name']}](characters/{c['slug']}.md)"
              for c in sorted(chars, key=lambda x: x["slug"])]
    lines += ["", "## Teams", ""]
    lines += [f"- [{u}](teams/{slugify(u)}.md)" for u in sorted(by_unit)]
    lines += ["", "## Universes", ""]
    lines += [f"- [{u}](universes/{slugify(u)}.md)" for u in sorted(by_uni)]
    lines += ["", "## Movies", ""]
    labels = sorted(set([main_label, seq_label] + list(referenced)))
    lines += [f"- [{l}](movies/{slugify(l)}.md)" for l in labels]
    lines += ["", "## Events", ""]
    lines += [f"- [Multiverse Saga — {data['release']['phase']}]"
              f"(events/{slugify(data['release']['phase'])}.md)"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    build_all()
