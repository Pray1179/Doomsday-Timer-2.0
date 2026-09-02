#!/usr/bin/env python3
"""Knowledge-layer tests: determinism, per-fact provenance, and data integrity.

Run: python3 scripts/test_knowledge.py
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_knowledge as bk

ROOT = Path(__file__).resolve().parent.parent
KNOW = ROOT / "knowledge"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def all_docs():
    return sorted(p for p in KNOW.glob("**/*.md"))


def read_hashes():
    return {str(p.relative_to(KNOW)): sha(p.read_text(encoding="utf-8"))
            for p in all_docs()}


def test_deterministic_double_build():
    before = read_hashes()
    assert before, "knowledge/ is empty"
    # Perturb every doc, then rebuild — output must be identical.
    for p in all_docs():
        p.write_text("# PERTURBED\n", encoding="utf-8")
    bk.build_all()
    after = read_hashes()
    assert before == after, "knowledge regeneration is NOT deterministic"
    assert all(p.read_text(encoding="utf-8") != "# PERTURBED\n"
               for p in all_docs()), "generator did not repair perturbed docs"


def _fact_lines(doc_text):
    """The statement bullets (skip title, Notes bullets, Sources legend)."""
    lines = []
    in_sources = False
    for line in doc_text.splitlines():
        if line.startswith("## "):
            in_sources = True
            continue
        if in_sources:
            continue
        if line.startswith("- "):
            lines.append(line)
    return lines


def test_every_fact_carries_provenance():
    for p in all_docs():
        if p.name == "index.md":  # structural index, not a fact doc
            continue
        text = p.read_text(encoding="utf-8")
        for line in _fact_lines(text):
            assert "(verified —" in line, f"{p}: missing provenance: {line}"
            assert "[S" in line, f"{p}: missing source ref: {line}"


def test_doom_is_played_by_downey_not_invented():
    t = (KNOW / "characters" / "robert-downey-jr.md").read_text(encoding="utf-8")
    # Correct, data-backed claims.
    assert "is portrayed by Robert Downey Jr." in t
    assert "is also known as Doctor Doom" in t
    assert "previously portrayed Tony Stark / Iron Man" in t
    # The only place Iron Man appears is the actor-history line (never Doom=IronMan).
    for line in _fact_lines(t):
        assert not ("Doctor Doom" in line and "Iron Man" in line and "previously" not in line)


def test_fantastic_four_members_complete():
    t = (KNOW / "teams" / "fantastic-four.md").read_text(encoding="utf-8")
    members = {line[2:].split(" is a member")[0] for line in _fact_lines(t)
               if " is a member of the Fantastic Four." in line}
    assert members == {
        "Reed Richards / Mr. Fantastic", "Sue Storm / Invisible Woman",
        "Johnny Storm / Human Torch", "Ben Grimm / The Thing"}, members
    assert "based in the Earth-828 universe" in t


def test_query_answers_present_in_graph():
    doom = (KNOW / "characters" / "robert-downey-jr.md").read_text(encoding="utf-8")
    reed = (KNOW / "characters" / "pedro-pascal.md").read_text(encoding="utf-8")
    movie = (KNOW / "movies" / "avengers-doomsday-2026.md").read_text(encoding="utf-8")
    # Q1: Who plays Doctor Doom? -> RDJ portrays Doom.
    assert "Victor von Doom / Doctor Doom is portrayed by Robert Downey Jr." in doom
    # Q3 path: Doom and Reed share a node (both appear in Doomsday).
    assert "Victor von Doom / Doctor Doom appears in Avengers: Doomsday" in movie
    assert "Reed Richards / Mr. Fantastic appears in Avengers: Doomsday" in movie
    # Q2 answer surfaced via team doc (checked in test_fantastic_four_members).
    assert "Pedro Pascal" in reed


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ALL KNOWLEDGE TESTS PASS")
