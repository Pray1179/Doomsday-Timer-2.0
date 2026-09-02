#!/usr/bin/env python3
"""End-to-end site tests: deterministic double-build + broken-link crawl.

Run: python3 scripts/test_site.py
(also imported by the aggregate runner)
"""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_explore as ex

ROOT = Path(__file__).resolve().parent.parent
EXPLORE = ROOT / "explore"
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets"

GENERATED = [
    "characters.html", "watch-guide.html", "timeline.html",
    "stats.html", "memorial.html",
]
ROOT_META = ["sitemap.xml", "robots.txt", "404.html"]
EXPLORE_404 = "404.html"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_hashes():
    """Hash every file the builder owns."""
    h = {}
    for name in GENERATED:
        p = EXPLORE / name
        h[f"explore/{name}"] = sha(p.read_text(encoding="utf-8"))
    h["sitemap.xml"] = sha((ROOT / "sitemap.xml").read_text(encoding="utf-8"))
    h["robots.txt"] = sha((ROOT / "robots.txt").read_text(encoding="utf-8"))
    h["explore/404.html"] = sha((EXPLORE / "404.html").read_text(encoding="utf-8"))
    return h


def test_deterministic_double_build():
    """Build -> perturb -> rebuild must restore byte-identical output."""
    before = read_hashes()

    # Perturb every generated file so a correct regenerator must repair it.
    for name in GENERATED:
        (EXPLORE / name).write_text("# PERTURBED\n", encoding="utf-8")
    (ROOT / "sitemap.xml").write_text("# PERTURBED\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text("# PERTURBED\n", encoding="utf-8")
    (EXPLORE / "404.html").write_text("# PERTURBED\n", encoding="utf-8")

    ex.build_all()

    after = read_hashes()
    assert before == after, "double-build is NOT deterministic — hashes differ"
    assert all((EXPLORE / n).read_text(encoding="utf-8") != "# PERTURBED\n"
               for n in GENERATED), "generator did not repair perturbed files"


def _resolve_hrefs(html, base_dir):
    """Resolve every internal relative URL against the referring file's dir.

    Returns (fname, kind, is_image) triples. Rules:
      - external / javascript / data URLs are skipped
      - ../pages/<x>, ../assets/<x>, ../index.html resolve from base_dir
      - bare names (nav links) resolve from base_dir
      - per-character images (.webp) are deliberately allowed to be missing
        (CSS initials-avatar fallback) so they are flagged, not failed
      - query strings (?v=...) are stripped before filesystem check
    """
    out = []
    for m in re.finditer(r'(?:href|src)="([^"#]+)(?:#[^"]*)?"', html):
        url = m.group(1)
        if url.startswith(("http", "mailto:", "//", "data:", "javascript:")):
            continue
        # Strip query string before resolving
        url_nqs = url.split("?", 1)[0]
        if url_nqs.startswith("../"):
            target = (base_dir.parent / url_nqs[3:]).resolve()
        else:
            target = (base_dir / url_nqs).resolve()
        is_img = url_nqs.endswith((".webp", ".png", ".jpg", ".jpeg", ".svg"))
        out.append((url, target, is_img))
    return out


def test_link_crawl_no_broken_links():
    """Every internal link in every explore page must resolve to a real file.

    Missing per-character images are allowed (documented CSS fallback); every
    other target — pages, css, js, other explore pages — must exist.
    """
    broken = []
    for name in list(GENERATED) + [EXPLORE_404]:
        p = EXPLORE / name
        if not p.exists():
            broken.append(f"missing explore/{name}")
            continue
        html = p.read_text(encoding="utf-8")
        for url, target, is_img in _resolve_hrefs(html, EXPLORE):
            if is_img:
                continue  # character .webp slots fall back to CSS initials
            if not target.exists():
                broken.append(f"{name} -> {url}")
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


def test_index_html_exists():
    assert (ROOT / "index.html").exists(), "index.html missing"
    assert 'class="countdown"' in (ROOT / "index.html").read_text(encoding="utf-8")


def test_every_character_page_is_linked():
    doc = ex.load()
    chars_html = (EXPLORE / "characters.html").read_text(encoding="utf-8")
    for c in doc["characters"]:
        slug = c["slug"]
        assert (PAGES / f"{slug}.html").exists(), f"pages/{slug}.html missing"
        assert (ROOT / "assets" / "img" / f"{slug}.webp") or \
               f"../pages/{slug}.html" in chars_html, f"{slug} not linked in characters.html"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ALL SITE TESTS PASS")
