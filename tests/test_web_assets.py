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


def test_animated_bars_are_not_stuck_at_zero_without_motion():
    """useMounted gates the bar width so a CSS transition has somewhere to
    animate from. Under reduced motion the transition is disabled, so if the
    hook still started at false every bar would render empty and the gap
    cards would silently lose their only visualisation.
    """
    js = JS.read_text(encoding="utf-8")
    body = js[js.index("export function useMounted"):]
    body = body[: body.index("export function useTilt")]
    assert "useState(() => prefersReducedMotion())" in body, (
        "useMounted must start true under reduced motion, or bars stay at zero"
    )


def test_the_tilt_never_runs_where_it_would_be_unwelcome():
    """A panel that follows the pointer is exactly the movement the reduced
    -motion setting asks us not to make, and on a touch screen there is no
    pointer to drive it."""
    js = JS.read_text(encoding="utf-8")
    body = js[js.index("export function useTilt"):]
    assert "prefersReducedMotion()" in body
    assert "(hover: hover)" in body and "(pointer: fine)" in body


def test_the_hero_preview_is_labelled_as_an_example():
    """The panel beside the headline shows fixed sample numbers. On a page
    whose whole argument is that its figures are checkable, presenting a
    mock-up as real output would be the one dishonest thing on it."""
    app = (SRC / "App.jsx").read_text(encoding="utf-8")
    preview = app[app.index("function Preview()"):]
    preview = preview[: preview.index("const PREVIEW_ROWS")]
    assert "Example result" in preview, (
        "the sample dashboard must say it is an example"
    )


def test_reveal_does_not_snapshot_the_dom_once():
    """Sections can mount after the effect runs.

    The results view swaps a loading skeleton for its real content when the
    request finishes, which mounts new [data-reveal] nodes without changing
    `view`. A single querySelectorAll at effect time never saw them, and the
    whole body of the results page stayed at opacity 0 -- an invisible page
    with no error anywhere to explain it.
    """
    js = JS.read_text(encoding="utf-8")
    body = js[js.index("export function useReveal"):]
    body = body[: body.index("export function useCountUp")]
    assert "MutationObserver" in body, (
        "useReveal must pick up nodes mounted after it ran"
    )
    assert "if (!targets.length) return" not in body, (
        "the early return skipped wiring up the observer entirely"
    )
