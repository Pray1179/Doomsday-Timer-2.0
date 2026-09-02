import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_explore as ex


def test_unit_key():
    assert ex.unit_key("Fantastic Four") == "fantastic-four"
    assert ex.unit_key("X-Men") == "x-men"
    assert ex.unit_key("MCU (Earth-616)") == "mcu"


def test_esc():
    assert ex.esc('a<b&"c') == "a&lt;b&amp;&quot;c"


def test_load_returns_30():
    doc = ex.load()
    assert len(doc["characters"]) == 30


def test_page_head_has_jsonld():
    h = ex.page_head("T", "D", "/pages/x.html", '{"x":1}')
    assert '<script type="application/ld+json">' in h
    assert '{"x":1}' in h


def test_site_nav_marks_active():
    assert 'class="active"' in ex.site_nav("characters")


def test_character_cards_has_data_unit():
    doc = ex.load()
    cards = ex.character_cards(doc["characters"])
    assert 'data-unit="x-men"' in cards
    assert 'href="../pages/robert-downey-jr.html"' in cards


def test_build_characters_has_grid_and_filter():
    html = ex.build_characters(ex.load())
    assert 'id="explore-filter"' in html
    assert 'class="cast-grid"' in html


def test_group_by_universe():
    g = ex.group_by_universe(ex.load()["characters"])
    assert sum(len(v) for v in g.values()) == 30
    assert set(g.keys()) == {"MCU (Earth-616)", "Earth-828", "X-Men universe"}


def test_build_watch_guide_lists_each_character():
    html = ex.build_watch_guide(ex.load())
    assert "watch-guide" in html
    assert "Essential before Doomsday" in html


def test_watch_guide_mentions_endgame():
    html = ex.build_watch_guide(ex.load())
    assert "Endgame" in html


def test_build_timeline_has_release_date():
    html = ex.build_timeline(ex.load())
    assert "2026-12-18" in html
    assert "Secret Wars" in html
    assert "Phase Six" in html


def test_counts_by_unit():
    counts = ex.counts_by(ex.load()["characters"], lambda c: c["unit"])
    assert counts["Avengers"] == 8
    assert counts["New Avengers"] == 5
    assert counts["X-Men"] == 8
    assert counts["Villain"] == 1


def test_sitemap_lists_character_pages():
    xml = ex.sitemap_xml(ex.load())
    assert "pages/robert-downey-jr.html" in xml
    assert "explore/stats.html" in xml
    assert "index.html" in xml


def test_robots_allows_all_and_points_sitemap():
    txt = ex.robots_txt()
    assert "User-agent: *" in txt
    assert "Sitemap:" in txt


def test_not_found_has_home_link():
    html = ex.not_found_html()
    assert "404" in html
    assert 'href="../index.html"' in html


def test_build_stats_shows_counts():
    html = ex.build_stats(ex.load())
    assert "30" in html  # confirmed cast
    assert "X-Men" in html
    assert 'class="bar-fill"' in html


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ALL TESTS PASS")