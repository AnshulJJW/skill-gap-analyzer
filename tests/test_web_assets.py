"""The frontend renders identically regardless of the reader's OS theme.

The page looked like a different product in a dark-mode browser than in a
light one: different palette, and different fonts. Both causes are one-line
regressions to reintroduce, so they are pinned here.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "web" / "src" / "index.css"
HTML = ROOT / "web" / "index.html"


def test_stylesheet_does_not_repaint_itself_for_dark_mode():
    """The palette is a deliberate choice, not a function of an OS setting."""
    assert "prefers-color-scheme" not in CSS.read_text(encoding="utf-8")


def test_native_controls_are_pinned_to_the_light_scheme():
    """Without this a dark OS paints textareas, selects and scrollbars dark
    inside the cream page -- which was most of the reported mismatch."""
    assert "color-scheme: light" in CSS.read_text(encoding="utf-8")


def test_fonts_are_linked_from_the_head_not_imported_from_css():
    """An @import serializes: the browser must fetch and parse index.css
    before it even asks for the fonts, so Georgia and Segoe UI paint first
    and swap late. A <link> starts both requests in parallel."""
    css = CSS.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    assert "@import" not in css, "font @import is back in index.css"
    assert "fonts.googleapis.com" in html
    for family in ("Fraunces", "Karla", "JetBrains+Mono"):
        assert family in html, f"{family} is no longer requested"


def test_every_font_family_declares_a_real_fallback():
    """If the font request fails the page must still be readable."""
    css = CSS.read_text(encoding="utf-8")
    for var, fallback in (("--display", "serif"),
                          ("--body", "sans-serif"),
                          ("--mono", "monospace")):
        line = next(ln for ln in css.splitlines() if ln.strip().startswith(var))
        assert line.rstrip().rstrip(";").endswith(fallback), (
            f"{var} has no generic fallback: {line.strip()!r}"
        )
