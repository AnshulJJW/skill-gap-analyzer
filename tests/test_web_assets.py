"""Frontend invariants that are one line away from regressing.

These check the stylesheet and the JSX as text. They cannot tell you the page
looks good -- only that the specific mistakes made once before are still
fixed.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "src"
CSS = SRC / "index.css"
JS = SRC / "motion.js"
HTML = ROOT / "web" / "index.html"

VIEWS = ["App.jsx", "Results.jsx", "JDResults.jsx", "ui.jsx", "encouragement.js"]


def _views() -> str:
    return "\n".join((SRC / name).read_text(encoding="utf-8") for name in VIEWS)


# --------------------------------------------------------------- theming


def test_stylesheet_does_not_repaint_itself_for_dark_mode():
    """The palette is a deliberate choice, not a function of an OS setting.

    The page used to render as a completely different product depending on
    the reader's theme.
    """
    assert "prefers-color-scheme" not in CSS.read_text(encoding="utf-8")


def test_native_controls_are_pinned_to_the_light_scheme():
    """Without this a dark OS paints textareas, selects and scrollbars dark
    inside the white page -- which CSS variables cannot reach."""
    assert "color-scheme: light" in CSS.read_text(encoding="utf-8")


# ----------------------------------------------------------------- fonts


def test_fonts_are_linked_from_the_head_not_imported_from_css():
    """An @import serializes: the browser must fetch and parse index.css
    before it even asks for the fonts, so the fallback paints first and swaps
    late. A <link> starts both requests in parallel."""
    assert "@import" not in CSS.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    assert "fonts.googleapis.com" in html
    for family in ("Inter", "JetBrains+Mono"):
        assert family in html, f"{family} is no longer requested"


def test_every_font_family_declares_a_real_fallback():
    """If the font request fails the page must still be readable."""
    css = CSS.read_text(encoding="utf-8")
    for var, fallback in (("--font", "sans-serif"), ("--mono", "monospace")):
        line = next(ln for ln in css.splitlines() if ln.strip().startswith(var))
        assert line.rstrip().rstrip(";").endswith(fallback), (
            f"{var} has no generic fallback: {line.strip()!r}"
        )


# ---------------------------------------------------------------- layout


def test_three_item_grids_never_lay_out_two_across():
    """auto-fit dropped to two columns at mid-widths, orphaning the third
    item in the left cell with a hole beside it -- which also breaks the
    reading order of a numbered sequence. Three or one, never two."""
    css = CSS.read_text(encoding="utf-8")
    # Every declaration, not just the first: a later rule overrides an
    # earlier one, so checking only the first occurrence would pass while
    # the page orphaned items.
    rules = [ln.strip() for ln in css.splitlines() if ln.strip().startswith(".grid-3 {")]
    assert rules, ".grid-3 is no longer defined"
    for rule in rules:
        assert "auto-fit" not in rule, f".grid-3 can orphan its third item: {rule!r}"
    assert any("repeat(3, 1fr)" in r for r in rules), rules


# ---------------------------------------------------------------- motion


def test_nothing_is_hidden_unless_javascript_asked_for_it():
    """The reveal animation must never be able to blank the page.

    Hiding lives behind .motion-on, a class only motion.js adds. If the
    script does not run, every selector below simply never matches and the
    page renders finished.
    """
    for line in CSS.read_text(encoding="utf-8").splitlines():
        if "[data-reveal]" in line:
            assert ".motion-on" in line, (
                f"reveal rule is not gated on .motion-on: {line.strip()!r}"
            )


def test_motion_yields_to_the_reduced_motion_setting():
    """Scroll-triggered movement is genuinely unpleasant with a vestibular
    disorder, and the media query is the reader saying so."""
    js = JS.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in js
    assert js.count("prefersReducedMotion()") >= 3, (
        "useReveal and useCountUp must each check before animating"
    )


def test_hover_lift_is_pointer_only():
    """On a touch screen :hover sticks after a tap, leaving a card raised
    until something else is touched."""
    assert "@media (hover: hover)" in CSS.read_text(encoding="utf-8")


# ------------------------------------------------------------------ copy

# Marketing and AI-branding vocabulary. The product argues from measured
# numbers; language that sells instead of stating undercuts that, and reads
# as generated. Kept as a list rather than a vibe so it survives edits.
BANNED = [
    "ai-powered", "ai-driven", "ai-based", "powered by ai", "ai engine",
    "ai insights", "machine intelligence", "next-generation", "cutting-edge",
    "state-of-the-art", "revolutionary", "seamless", "supercharge",
    "unlock your", "unleash", "limitless", "transform your", "elevate your",
    "empower", "harness the", "game-changing", "effortlessly", "blazing",
    "world-class", "best-in-class", "leverage the",
]


def test_no_marketing_or_ai_branding_language_in_the_interface():
    text = _views().lower()
    hits = [phrase for phrase in BANNED if phrase in text]
    assert not hits, f"marketing language in the UI copy: {hits}"


def test_the_supportive_note_never_judges_the_reader():
    """The gap is a fact about a job market, not about the person. Wording
    that makes it personal is the thing this feature exists to avoid."""
    text = (SRC / "encouragement.js").read_text(encoding="utf-8").lower()
    for phrase in ("not qualified", "insufficient", "far behind", "poor",
                   "you lack", "weak", "failure", "unfortunately"):
        assert phrase not in text, f"judgemental wording in the note: {phrase!r}"
