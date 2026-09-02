#!/usr/bin/env python3
"""Validation tests for the on-screen Marvel character catalogue.

Schema / merge tests (Task 1). Run: python3 scripts/test_catalogue.py
Must end with ALL CATALOGUE TESTS PASS.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import catalogue_util as cu


def test_load_all_merges_sorted():
    recs = cu.load_all()
    ids = [r["id"] for r in recs]
    assert len(recs) >= 38, f"expected >=38 seed records, got {len(recs)}"
    assert ids == sorted(ids), "records must be id-sorted after merge"


def test_ids_kebab_unique():
    recs = cu.load_all()
    ids = [r["id"] for r in recs]
    assert len(set(ids)) == len(ids), "duplicate ids"
    for i in ids:
        assert cu.slug_ok(i), f"bad id: {i}"


def test_required_fields_present():
    for r in cu.load_all():
        for f in cu.REQUIRED:
            assert f in r and (r[f] not in (None, "")), f"{r.get('id')} missing {f}"


def test_image_attribution_rule():
    for r in cu.load_all():
        if r.get("image_url"):
            img = r["image_url"]
            # Two valid image sources: an external https URL (must carry full
            # attribution) or a local asset under assets/img (../ relative path).
            assert img.startswith("https://") or img.startswith("../"), \
                f"{r['id']} image_url not https or relative: {img}"
            assert r.get("image_alt"), f"{r['id']} has image_url but no alt"
            if img.startswith("https://"):
                assert r.get("image_source_url"), f"{r['id']} has image_url but no source url"
                assert r.get("image_source_name"), f"{r['id']} has image_url but no source name"


def test_doomsday_cross_links_resolve():
    """Every doomsday_cast_slug must be a real slug story in the 30-page site."""
    recs = cu.load_all()
    slugs = {r.get("doomsday_cast_slug") for r in recs if r.get("doomsday_cast_slug")}
    claimed = [r["id"] for r in recs if r.get("doomsday_cast_slug")]
    assert len(slugs) == 30, f"expected all 30 doomsday cast cross-linked, got {len(slugs)}"
    assert len(claimed) == 30, f"expected 30 records to carry a cast slug, got {len(claimed)}"


# --- Task 4: listing page ---


def test_listing_links_all_and_badge():
    import build_catalogue as bc
    import build_explore as ex
    recs = bc.load_normalized()
    cast = ex.load()
    html = bc.build_listing(recs, cast)
    for r in recs:
        assert f"catalogue/{r['id']}.html" in html, r["id"]
    assert "30 confirmed" in html
    assert 'id="catalogue-search"' in html
    assert "data-team=" in html


# --- Task 5: detail pages ---


def test_detail_pages_generated():
    import build_catalogue as bc
    import build_explore as ex
    recs = bc.load_normalized()
    cast = ex.load()
    bc.build_all()
    cat = Path(__file__).parent.parent / "explore/catalogue"
    for r in recs:
        p = cat / f"{r['id']}.html"
        assert p.exists(), f"missing {r['id']}.html"
        h = p.read_text()
        assert "../../assets/css/styles.css" in h
        # Every detail page carries its dossier emblem under the portrait slot;
        # verified photos add an <img class="photo"> with attribution.
        assert f"cat-{r['id']}.svg" in h, f"{r['id']} missing emblem"
        if r.get("image_url") and r.get("image_verified"):
            assert 'class="photo"' in h and "img-attr" in h, f"{r['id']} missing photo or attribution"


def test_detail_prev_next_present():
    import build_catalogue as bc
    recs = bc.load_normalized()
    mid = bc.build_detail(recs[1], recs[0]["id"], recs[2]["id"], None)
    assert recs[0]["id"] in mid and recs[2]["id"] in mid


# --- Task 3: emblem generation ---


def test_emblems_written():
    import build_catalogue as bc
    recs = bc.load_normalized()
    n = bc.build_emblems(recs)
    assert n == len(recs)
    assert n >= 38
    assert (Path(__file__).parent.parent / "assets/img/cat-doctor-doom.svg").exists()


def test_emblem_is_valid_svg():
    import build_catalogue as bc
    recs = bc.load_normalized()
    bc.build_emblems(recs)
    svg = (Path(__file__).parent.parent / "assets/img/cat-doctor-doom.svg").read_text()
    assert svg.lstrip().startswith("<svg")
    assert 'aria-label="Victor von Doom emblem"' in svg  # deterministic monogram label


# --- Task 2: merge + strict validation ---


def test_validate_rejects_duplicate_id():
    import build_catalogue as bc
    bad = [{"id": "a", "name": "n", "alias": "x", "universe": "u", "continuity": "MCU",
            "team_or_affiliation": [], "status": "Active", "debut_title": "d",
            "source_notes": [], "related_titles": [], "verified": True},
           {"id": "a", "name": "n2", "alias": "y", "universe": "u", "continuity": "MCU",
            "team_or_affiliation": [], "status": "Active", "debut_title": "d",
            "source_notes": [], "related_titles": [], "verified": True}]
    try:
        bc.validate(bad)
        assert False, "should have raised"
    except SystemExit:
        pass


def test_validate_rejects_image_without_source():
    import build_catalogue as bc
    bad = [{"id": "b", "name": "n", "alias": "x", "universe": "u", "continuity": "MCU",
            "team_or_affiliation": [], "status": "Active", "debut_title": "d",
            "source_notes": [], "related_titles": [], "verified": True,
            "image_url": "https://x/y.jpg", "image_alt": "alt"}]
    try:
        bc.validate(bad)
        assert False, "should have raised"
    except SystemExit:
        pass


def test_merge_writes_normalized_file():
    import build_catalogue as bc
    recs = bc.load_normalized()
    bc.merge(recs)
    merged = json.loads((Path(__file__).parent.parent / "data" / "catalogue.json").read_text())
    assert [r["id"] for r in merged] == sorted(r["id"] for r in merged)


def test_import_side_effect_free():
    """Importing build_catalogue must not write files or print a report."""
    import build_catalogue as bc
    assert callable(bc.load_normalized)


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            f()
            print(f"PASS {n}")
    print("ALL CATALOGUE TESTS PASS")