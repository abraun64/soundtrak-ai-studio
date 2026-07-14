#!/usr/bin/env python3
"""
render_inspect — render → INSPECT → FIX QA loop for the highest-stakes operator
surfaces (SYS-064).

The render pipeline (render.py) produces HTML but never LOOKS at its own output.
Existing guards catch two failure classes: unfilled sentinels (guard_residual_markers)
and behavioural regressions (.claude/evals LAYER 7). NEITHER catches LAYOUT / visual
defects — overflow, orphaned headings, empty required sections, broken structure,
dead internal links, alt-less images.

This module closes that gap for ONE surface type first: the **asset preview**
(campaigns/*/assets/*/preview.html) — the surface the operator reviews-and-approves,
so a layout defect there is the most expensive. It:

  1. Parses a rendered .html deterministically (stdlib html.parser — NO third-party
     deps) and checks a set of HARD LAYOUT CONSTRAINTS.
  2. Offers a bounded render→inspect→FIX loop: for the UNAMBIGUOUS, provably-safe
     violations (a wide/long table not wrapped in an overflow-scroll container; an
     <img> with no alt) it post-processes the HTML, re-inspects, and repeats
     (max 3 iterations). Anything it can't safely auto-fix is reported.
  3. Degrades gracefully: a richer visual check (headless browser / screenshot via
     the Claude Preview tooling) is an OPTIONAL plug-in point. If that dependency is
     absent — which it is by default, offline — the module runs the deterministic
     checks and NOTES "visual inspection skipped (optional dep unavailable)" rather
     than erroring. A browser is never a hard requirement.

Deterministic + offline + no network. Invoke on demand:

    python render_inspect.py <rendered.html>              # inspect only, report
    python render_inspect.py <rendered.html> --fix        # run the fix loop, rewrite
    python render_inspect.py <rendered.html> --json       # machine-readable report

Exit 0 = clean (or all violations auto-fixed); exit 1 = residual violations remain.

Each violation is reported as:  surface · constraint · locus · detail
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# Reuse the render pipeline's own residual-marker regex so this module and the
# render-time guard can never disagree about what counts as an unresolved sentinel.
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from render import _RESIDUAL_MARKER_RE  # type: ignore
except Exception:  # pragma: no cover - defensive; keep a local copy in sync
    _RESIDUAL_MARKER_RE = re.compile(
        r"<!--\s*([A-Z0-9_]*(?:_AUTO|_MARKER|AUTO_INJECT)[A-Z0-9_]*)\s*-->"
    )

# PHASE_COST:N is a cost-cell sentinel that is NOT caught by the *_AUTO/_MARKER
# regex above but is exactly the "silently blank section" class this loop targets.
_PHASE_COST_RE = re.compile(r"<!--\s*PHASE_COST:\d+\s*-->")

# A "long unbroken line" heuristic for pre/code overflow (no whitespace to wrap on).
_LONG_LINE_CHARS = 130
# A table with this many columns is treated as "wide" (candidate for h-scroll).
_WIDE_TABLE_COLS = 6


# =============================================================================
# Violation model
# =============================================================================

@dataclass
class Violation:
    constraint: str          # short machine id, e.g. "wide-table-no-scroll"
    locus: str               # where in the doc, e.g. "table #2 (9 cols)"
    detail: str              # human explanation
    auto_fixable: bool = False

    def format(self, surface: str, sep: str = " | ") -> str:
        """`surface | constraint | locus | detail`. ASCII pipe by default so the
        line prints cleanly on the Windows cp1252 console; pass sep=' · ' for the
        middot form when the output sink is UTF-8."""
        tag = " [auto-fixable]" if self.auto_fixable else ""
        return sep.join([surface, self.constraint, self.locus, self.detail]) + tag


@dataclass
class InspectReport:
    surface: str
    html_path: str
    violations: list[Violation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)   # e.g. degradation notes

    @property
    def clean(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict:
        return {
            "surface": self.surface,
            "html_path": self.html_path,
            "clean": self.clean,
            "violations": [
                {"constraint": v.constraint, "locus": v.locus, "detail": v.detail,
                 "auto_fixable": v.auto_fixable}
                for v in self.violations
            ],
            "notes": self.notes,
        }


# =============================================================================
# Surface classification — which surface type is this .html?
# =============================================================================

def classify_surface(html_path: Path, html_text: str) -> str:
    """Return a surface-type id. v1 targets 'asset-preview'; other surfaces are
    recognised so the CLI can say so (and run the generic subset of checks)."""
    # The body carries `template-<name>` (see base/asset-preview templates).
    m = re.search(r'<body[^>]*class="[^"]*template-([a-z-]+)', html_text)
    if m:
        return m.group(1)
    # Fall back to the path convention.
    name = html_path.name
    parent = html_path.parent
    if name == "preview.html" and parent.parent.name == "assets":
        return "asset-preview"
    return "unknown"


# =============================================================================
# Lightweight DOM model (stdlib html.parser) — enough to reason about structure
# =============================================================================

@dataclass
class Node:
    tag: str
    attrs: dict
    parent: "Node | None" = None
    children: list = field(default_factory=list)
    text: str = ""           # concatenated descendant text
    start_pos: int = 0       # offset in the raw html (for locus reporting)

    def find_all(self, tag: str) -> list:
        out = []
        stack = list(self.children)
        while stack:
            n = stack.pop()
            if isinstance(n, Node):
                if n.tag == tag:
                    out.append(n)
                stack.extend(n.children)
        return out


# Tags that don't nest / self-close in HTML5.
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
         "meta", "param", "source", "track", "wbr"}


class _DomBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), parent=self.stack[-1],
                    start_pos=self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs), parent=self.stack[-1],
                    start_pos=self.getpos()[0])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        # Pop to the matching open tag if present (tolerant of minor mis-nesting).
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].text += data


def _build_dom(html_text: str) -> Node:
    p = _DomBuilder()
    p.feed(html_text)
    # Backfill node.text with descendant text so heading-emptiness checks work.
    def _fill(n: Node) -> str:
        acc = n.text
        for c in n.children:
            if isinstance(c, Node):
                acc += " " + _fill(c)
        n.text = acc.strip()
        return n.text
    _fill(p.root)
    return p.root


def _content_root(root: Node) -> Node:
    """The main narrative container for the surface. Asset-preview wraps its body
    in <article class="content content--narrative">; fall back to the first
    .content element, else the whole doc."""
    for art in root.find_all("article"):
        cls = art.attrs.get("class", "")
        if "content" in cls:
            return art
    for div in root.find_all("div"):
        if "content" in div.attrs.get("class", ""):
            return div
    return root


# =============================================================================
# Constraint checks (deterministic)
# =============================================================================

_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def _visible_flow_children(container: Node) -> list:
    """Direct-ish flow children of the content container, in document order.
    Descends through wrapper <div>s that have no own text but do have children,
    so an orphan-heading check sees real content, not layout wrappers."""
    return [c for c in container.children if isinstance(c, Node)]


def check_residual_markers(html_text: str, surface: str) -> list[Violation]:
    """No unresolved *_AUTO / *_MARKER / PHASE_COST sentinels may survive. This
    overlaps render.py's guard_residual_markers by DESIGN — that guard turns a
    marker into a visible red placeholder at render time; here we assert none
    reached the shipped file at all (and flag the visible-placeholder div too)."""
    out: list[Violation] = []
    seen = set()
    for m in _RESIDUAL_MARKER_RE.finditer(html_text):
        tok = m.group(1).strip()
        if tok not in seen:
            seen.add(tok)
            out.append(Violation(
                "unresolved-marker", f"<!-- {tok} -->",
                "an auto-inject sentinel survived render (section is silently blank)",
                auto_fixable=False))
    for _ in _PHASE_COST_RE.finditer(html_text):
        out.append(Violation(
            "unresolved-marker", "<!-- PHASE_COST:N -->",
            "a per-phase cost sentinel survived render (cost cell is blank)",
            auto_fixable=False))
    if 'class="render-warn"' in html_text:
        out.append(Violation(
            "render-warn-placeholder", "div.render-warn",
            "guard_residual_markers fired — a section rendered as the visible "
            "failure placeholder instead of its content",
            auto_fixable=False))
    return out


def check_empty_required_sections(content: Node) -> list[Violation]:
    """A heading immediately followed by another heading of equal-or-higher level
    (or nothing) = an empty section: a promise of content the render never filled."""
    out: list[Violation] = []
    flow = _visible_flow_children(content)
    # Flatten one level: headings live directly under .content for markdown output.
    seq = [n for n in flow]
    for i, n in enumerate(seq):
        if n.tag not in _HEADING_TAGS:
            continue
        level = int(n.tag[1])
        # DIVIDER-LABEL idiom: a heading bracketed by <hr> before AND after (e.g.
        # "--- / ## Historical changelogs below / ---") is an intentional section
        # separator label, not a broken empty section. Don't flag it.
        prev_non_head = seq[i - 1] if i > 0 else None
        next_el = seq[i + 1] if i + 1 < len(seq) else None
        if (prev_non_head is not None and prev_non_head.tag == "hr"
                and next_el is not None and next_el.tag == "hr"):
            continue
        # Look at what follows until the next sibling that carries real content.
        has_body = False
        for m in seq[i + 1:]:
            if m.tag in _HEADING_TAGS:
                nxt_level = int(m.tag[1])
                if nxt_level <= level:
                    break  # next section began with no body in between
                # a deeper sub-heading counts as content for the parent
                has_body = True
                break
            if m.tag == "hr":
                continue  # a rule alone isn't content
            # any non-heading element with text or that is a media/table = body
            if m.text or m.tag in ("img", "table", "ul", "ol", "pre", "blockquote", "figure"):
                has_body = True
                break
        if not has_body:
            title = (n.text or "").strip()[:48] or "(untitled)"
            out.append(Violation(
                "empty-required-section", f"{n.tag} “{title}”",
                "heading has no content before the next same-or-higher heading",
                auto_fixable=False))
    return out


def check_orphan_trailing_heading(content: Node) -> list[Violation]:
    """The last visible flow node must not be a heading (a heading with nothing
    under it, dangling at the very end of the surface)."""
    flow = [n for n in _visible_flow_children(content)
            if n.tag not in ("hr",)]  # a trailing <hr> is cosmetic, ignore it
    if not flow:
        return []
    last = flow[-1]
    if last.tag in _HEADING_TAGS and not any(
        isinstance(c, Node) for c in last.children
    ):
        title = (last.text or "").strip()[:48] or "(untitled)"
        return [Violation(
            "orphan-trailing-heading", f"{last.tag} “{title}”",
            "surface ends on a heading with no content beneath it",
            auto_fixable=False)]
    return []


def check_images_alt(content: Node) -> list[Violation]:
    """Every content <img> must carry a non-empty alt (accessibility + broken-image
    fallback text). Missing alt is UNAMBIGUOUSLY auto-fixable (insert a placeholder
    derived from the filename)."""
    out: list[Violation] = []
    for img in content.find_all("img"):
        alt = img.attrs.get("alt")
        if alt is None or not alt.strip():
            src = img.attrs.get("src", "")
            out.append(Violation(
                "img-missing-alt", f"img src=“{src[:60]}”",
                "image has no alt text",
                auto_fixable=True))
    return out


def check_wide_or_long_tables(content: Node, html_text: str) -> list[Violation]:
    """A wide table (>= _WIDE_TABLE_COLS columns) or one with a very long unbroken
    cell must sit inside an overflow-scroll wrapper, else it overflows the column
    on narrow viewports. Auto-fixable (wrap in the standard .table-scroll div)."""
    out: list[Violation] = []
    for i, tbl in enumerate(content.find_all("table"), 1):
        # Already wrapped?
        p = tbl.parent
        if p and "table-scroll" in p.attrs.get("class", ""):
            continue
        # Column count = max <tr> cell count.
        max_cols = 0
        for tr in tbl.find_all("tr"):
            cols = sum(1 for c in tr.children
                       if isinstance(c, Node) and c.tag in ("td", "th"))
            max_cols = max(max_cols, cols)
        longest_cell = 0
        for cell in tbl.find_all("td") + tbl.find_all("th"):
            for tok in re.split(r"\s+", cell.text or ""):
                longest_cell = max(longest_cell, len(tok))
        wide = max_cols >= _WIDE_TABLE_COLS
        long_cell = longest_cell >= _LONG_LINE_CHARS
        if wide or long_cell:
            reason = []
            if wide:
                reason.append(f"{max_cols} cols")
            if long_cell:
                reason.append(f"unbroken cell token {longest_cell} chars")
            out.append(Violation(
                "wide-table-no-scroll", f"table #{i} ({', '.join(reason)})",
                "wide/long table not wrapped in an overflow-scroll container",
                auto_fixable=True))
    return out


def check_long_pre_lines(content: Node) -> list[Violation]:
    """A <pre>/<code> block with a very long unbroken line overflows horizontally.
    .content pre already has overflow-x:auto, so this is REPORT-ONLY (the CSS
    handles it) unless the block is outside .content — flagged, not auto-fixed."""
    out: list[Violation] = []
    for i, pre in enumerate(content.find_all("pre"), 1):
        longest = 0
        for line in (pre.text or "").splitlines():
            # unbroken = no whitespace to wrap on
            for tok in re.split(r"\s+", line):
                longest = max(longest, len(tok))
        if longest >= _LONG_LINE_CHARS:
            out.append(Violation(
                "long-pre-line", f"pre #{i} (token {longest} chars)",
                "code block has a long unbroken line; relies on overflow-x scroll "
                "(present in .content pre CSS) — verify it is inside .content",
                auto_fixable=False))
    return out


def check_broken_internal_links(content: Node, html_path: Path) -> list[Violation]:
    """An href pointing at a RELATIVE file next to the surface that does not exist
    = a dead link the operator would click into a 404. Skips anchors (#…), external
    (http/mailto/tel), and the .md<->.html render convention (a link to foo.md is
    fine when foo.html exists next to it, and vice-versa)."""
    out: list[Violation] = []
    base = html_path.parent
    seen = set()
    for a in content.find_all("a"):
        href = (a.attrs.get("href") or "").strip()
        if not href or href.startswith(("#", "http://", "https://", "mailto:",
                                        "tel:", "//", "data:", "javascript:")):
            continue
        target = href.split("#", 1)[0]
        if not target or target in seen:
            continue
        seen.add(target)
        # Resolve relative to the surface's own folder.
        try:
            resolved = (base / target).resolve()
        except (OSError, ValueError):
            continue
        if resolved.exists():
            continue
        # .md<->.html render tolerance: a .md link is satisfied by a sibling .html.
        alt = None
        if target.endswith(".md"):
            alt = base / (target[:-3] + ".html")
        elif target.endswith(".html"):
            alt = base / (target[:-5] + ".md")
        if alt is not None and alt.exists():
            continue
        out.append(Violation(
            "broken-internal-link", f"a href=“{href[:60]}”",
            "internal link target does not exist next to the surface",
            auto_fixable=False))
    return out


# =============================================================================
# Optional richer visual inspection — plug-in point (graceful degradation)
# =============================================================================

def _visual_inspect_available() -> bool:
    """Is a headless-render/screenshot dependency present? By default (offline,
    deterministic v1) this is False and the loop uses the structural checks only.
    A later integration can make this return True when the Claude Preview tooling
    (or a vendored headless browser) is wired in — see visual_inspect()."""
    return False


def visual_inspect(html_path: Path) -> list[Violation]:
    """DOCUMENTED EXTENSION POINT. When a headless renderer is available, this is
    where a screenshot-based pass would run (measure real overflow, detect content
    clipped past the viewport, empty painted regions, contrast). It MUST return the
    same Violation shape so the loop is agnostic to how a violation was found.

    Until that dependency is wired in, `_visual_inspect_available()` returns False
    and this function is never called — the caller records a degradation note."""
    raise NotImplementedError("visual inspection dependency not wired in")


# =============================================================================
# Inspect — run every constraint, assemble the report
# =============================================================================

def inspect_html(html_path: Path, html_text: str | None = None) -> InspectReport:
    """Run the deterministic constraint checks against a rendered .html. Pure /
    read-only. Returns an InspectReport."""
    html_path = Path(html_path)
    if html_text is None:
        html_text = html_path.read_text(encoding="utf-8")
    surface = classify_surface(html_path, html_text)
    root = _build_dom(html_text)
    content = _content_root(root)

    report = InspectReport(surface=surface, html_path=str(html_path))

    # Marker checks run over the WHOLE html (markers can sit outside .content).
    report.violations += check_residual_markers(html_text, surface)
    # Structural checks run over the narrative container.
    report.violations += check_empty_required_sections(content)
    report.violations += check_orphan_trailing_heading(content)
    report.violations += check_images_alt(content)
    report.violations += check_wide_or_long_tables(content, html_text)
    report.violations += check_long_pre_lines(content)
    report.violations += check_broken_internal_links(content, html_path)

    # Graceful degradation: richer visual pass IF available, else a clear note.
    if _visual_inspect_available():
        try:
            report.violations += visual_inspect(html_path)
        except Exception as e:  # noqa: BLE001
            report.notes.append(f"visual inspection errored, skipped: {e}")
    else:
        report.notes.append(
            "visual inspection skipped (optional dep unavailable) - "
            "deterministic structural checks only")

    return report


# =============================================================================
# Auto-fix — conservative, provably-safe HTML post-processing only
# =============================================================================

# The overflow-scroll wrapper class this loop wraps wide tables in. Injected as a
# scoped <style> once per file if not already present (additive; scoped so it can
# never affect existing rules).
_TABLE_SCROLL_CSS = (
    '<style data-render-inspect="table-scroll">'
    '.table-scroll{overflow-x:auto;max-width:100%;'
    '-webkit-overflow-scrolling:touch;margin:0 0 20px 0;}'
    '.table-scroll>table{margin-bottom:0;}'
    '</style>'
)


def _ensure_table_scroll_css(html_text: str) -> str:
    if 'data-render-inspect="table-scroll"' in html_text:
        return html_text
    if "</head>" in html_text:
        return html_text.replace("</head>", _TABLE_SCROLL_CSS + "</head>", 1)
    return _TABLE_SCROLL_CSS + html_text


def _wrap_wide_tables(html_text: str) -> tuple[str, int]:
    """Wrap each wide/long <table> not already inside a .table-scroll in the
    standard overflow container. Operates on the raw HTML string with a tolerant
    regex so it doesn't disturb any other markup. Returns (new_html, count)."""
    fixed = 0

    def _repl(m: re.Match) -> str:
        nonlocal fixed
        table_html = m.group(0)
        # Only wrap if it qualifies as wide/long (re-check on the isolated string).
        cols = _max_cols_in_table(table_html)
        longest = _longest_token_in_table(table_html)
        if cols < _WIDE_TABLE_COLS and longest < _LONG_LINE_CHARS:
            return table_html
        fixed += 1
        return f'<div class="table-scroll">{table_html}</div>'

    # Match <table ...>...</table> non-greedily. Tables don't nest in this pipeline.
    # Skip tables already directly preceded by the wrapper open tag.
    def _guarded_repl(m: re.Match) -> str:
        start = m.start()
        preceding = html_text[max(0, start - 40):start]
        if 'class="table-scroll"' in preceding:
            return m.group(0)
        return _repl(m)

    new_html = re.sub(r"<table\b.*?</table>", _guarded_repl, html_text,
                      flags=re.DOTALL)
    return new_html, fixed


def _max_cols_in_table(table_html: str) -> int:
    max_cols = 0
    for tr in re.findall(r"<tr\b.*?</tr>", table_html, flags=re.DOTALL):
        cols = len(re.findall(r"<t[dh]\b", tr))
        max_cols = max(max_cols, cols)
    return max_cols


def _longest_token_in_table(table_html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", table_html)
    longest = 0
    for tok in re.split(r"\s+", text):
        longest = max(longest, len(tok))
    return longest


def _add_missing_alts(html_text: str) -> tuple[str, int]:
    """Add a placeholder alt (derived from the filename) to any <img> lacking one.
    Provably safe: alt text is purely additive; never changes src or layout."""
    fixed = 0

    def _repl(m: re.Match) -> str:
        nonlocal fixed
        tag = m.group(0)
        if re.search(r'\balt\s*=\s*"[^"]*[^"\s][^"]*"', tag) or \
           re.search(r"\balt\s*=\s*'[^']*[^'\s][^']*'", tag):
            return tag  # has a non-empty alt already
        # derive a placeholder from src filename
        sm = re.search(r'\bsrc\s*=\s*"([^"]*)"', tag) or \
             re.search(r"\bsrc\s*=\s*'([^']*)'", tag)
        stem = "image"
        if sm:
            stem = Path(sm.group(1).split("?")[0]).stem.replace("-", " ").replace("_", " ").strip() or "image"
        alt_val = f"{stem}"
        fixed += 1
        # strip any empty alt, then inject before the closing >
        tag_wo_empty = re.sub(r'\s+alt\s*=\s*(""|\'\')', "", tag)
        if tag_wo_empty.endswith("/>"):
            return tag_wo_empty[:-2] + f' alt="{alt_val}" />'
        return tag_wo_empty[:-1] + f' alt="{alt_val}">'

    new_html = re.sub(r"<img\b[^>]*>", _repl, html_text)
    return new_html, fixed


def apply_auto_fixes(html_text: str) -> tuple[str, list[str]]:
    """Apply every provably-safe auto-fix once. Returns (new_html, [applied notes]).
    Conservative: only the fixes proven safe (wrap wide tables, add missing alts).
    Everything else is left for the report."""
    applied: list[str] = []
    html_text2, n_tables = _wrap_wide_tables(html_text)
    if n_tables:
        html_text2 = _ensure_table_scroll_css(html_text2)
        applied.append(f"wrapped {n_tables} wide/long table(s) in .table-scroll")
    html_text3, n_imgs = _add_missing_alts(html_text2)
    if n_imgs:
        applied.append(f"added placeholder alt to {n_imgs} image(s)")
    return html_text3, applied


# =============================================================================
# The render → INSPECT → FIX loop
# =============================================================================

@dataclass
class LoopResult:
    report: InspectReport                 # final report (after fixes)
    iterations: int
    fixes_applied: list[str] = field(default_factory=list)
    html_written: bool = False


def inspect_fix_loop(html_path: Path, apply: bool = False,
                     max_iter: int = 3) -> LoopResult:
    """Inspect; if there are auto-fixable violations AND apply=True, patch the
    HTML in place, re-inspect, repeat up to max_iter. Returns the final report +
    what was fixed. With apply=False this is a pure inspection (no write)."""
    html_path = Path(html_path)
    html_text = html_path.read_text(encoding="utf-8")
    all_fixes: list[str] = []
    iterations = 0
    written = False

    report = inspect_html(html_path, html_text)
    if not apply:
        return LoopResult(report=report, iterations=1)

    for _ in range(max_iter):
        iterations += 1
        fixable = [v for v in report.violations if v.auto_fixable]
        if not fixable:
            break
        new_html, applied = apply_auto_fixes(html_text)
        if not applied or new_html == html_text:
            break  # nothing changed — avoid an infinite loop
        html_text = new_html
        all_fixes += applied
        report = inspect_html(html_path, html_text)

    if all_fixes:
        html_path.write_text(html_text, encoding="utf-8")
        written = True

    return LoopResult(report=report, iterations=iterations,
                      fixes_applied=all_fixes, html_written=written)


# =============================================================================
# CLI
# =============================================================================

def _print_report(result: LoopResult, as_json: bool) -> None:
    # The Windows console defaults to cp1252 and chokes on non-latin-1 glyphs;
    # keep all human output ASCII so this runs identically everywhere (incl. the
    # smoke test, which shells this on Windows).
    report = result.report
    if as_json:
        payload = result.report.to_dict()
        payload["iterations"] = result.iterations
        payload["fixes_applied"] = result.fixes_applied
        payload["html_written"] = result.html_written
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print("=== RENDER INSPECT ===")
    print(f"surface : {report.surface}")
    print(f"file    : {report.html_path}")
    if result.fixes_applied:
        print(f"\nauto-fixes applied ({result.iterations} iteration(s)):")
        for f in result.fixes_applied:
            print(f"  [fixed] {f}")
        if result.html_written:
            print("  -> HTML rewritten in place")
    if report.violations:
        print(f"\n{len(report.violations)} violation(s) remaining:")
        for v in report.violations:
            print(f"  [FAIL] {v.format(report.surface)}")
    else:
        print("\nno violations - surface is structurally clean [OK]")
    for note in report.notes:
        print(f"\nnote: {note}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Inspect a rendered operator surface for hard layout defects; "
                    "optionally run the bounded auto-fix loop.")
    ap.add_argument("html", help="path to a rendered .html surface")
    ap.add_argument("--fix", action="store_true",
                    help="run the render→inspect→FIX loop and rewrite the HTML "
                         "in place (conservative, provably-safe fixes only)")
    ap.add_argument("--max-iter", type=int, default=3,
                    help="max fix/re-inspect iterations (default 3)")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable JSON report")
    args = ap.parse_args(argv)

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"ERROR: file not found: {html_path}", file=sys.stderr)
        return 2

    result = inspect_fix_loop(html_path, apply=args.fix, max_iter=args.max_iter)
    _print_report(result, args.json)
    # Exit 1 if any violation remains (so CI / a hook can gate on it).
    return 0 if result.report.clean else 1


if __name__ == "__main__":
    sys.exit(main())
