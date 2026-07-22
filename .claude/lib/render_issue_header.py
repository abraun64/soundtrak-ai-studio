#!/usr/bin/env python3
"""
render_issue_header — SYS-094 (parts 1-3, forward-only). Build a Debrief-style issue
header AS A BUILD ARTIFACT from a single source, so it can never drift from the body.

The stale-mirror bug (2026-07-09 / SYS-094): an edition's body lived verbatim in BOTH
edition.md AND issue-header.html; a rework of one silently left the other stale. The fix
is to stop hand-copying. issue-header.html is now GENERATED from:

  - edition.md   — the article body (THE single source for the prose)
  - header.yaml  — the per-edition data (kicker / headline / standfirst / evidence / hero)
  - a slotted look-kit template (the constant chrome, {{SLOT}} placeholders)

so the HTML is derived, not mirrored, and it carries a provenance stamp (content hashes of
its sources) for a content-based staleness check that supersedes the mtime heuristic.

FORWARD-ONLY: this is the authoring path for NEW editions (#5 onward on The Debrief).
Editions #1-#4 are approved + frozen and are NOT regenerated.

Body conventions in edition.md (kept deliberately light):
  - `## Heading` / paragraphs                    → <h2>/<p>
  - first paragraph after the first `##`         → <p class="lede">
  - a `> quote` blockquote line                  → <p class="pull">
  - an HTML comment `<!-- HERO -->`              → the hero <figure> from header.yaml

Usage:
  python render_issue_header.py --asset <asset_dir>            # reads asset_dir/header.yaml
  python render_issue_header.py --header <header.yaml> --template <tmpl> --edition <edition.md> --out <html>

Exit 0 on success, 1 on a missing input / unfilled required slot.
"""
from __future__ import annotations
import argparse
import hashlib
import html as _html
import re
import sys
from pathlib import Path


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _render_body(edition_md: str, hero_html: str) -> str:
    """edition.md prose -> the <div class="body"> inner HTML, with the hero figure injected
    at the <!-- HERO --> marker and the lede/pull conventions applied."""
    try:
        import markdown as _md
    except ImportError:
        raise SystemExit("pyyaml + markdown required (pip install markdown pyyaml)")
    # split off the hero marker so markdown doesn't mangle the raw figure HTML
    HERO = "<!-- HERO -->"
    parts = edition_md.split(HERO)
    out_chunks = []
    for i, chunk in enumerate(parts):
        html = _md.markdown(chunk.strip(), extensions=["extra"])
        out_chunks.append(html)
        if i < len(parts) - 1:
            out_chunks.append(hero_html)
    body = "\n".join(out_chunks)
    # first <p> after the first <h2> becomes the lede
    body = re.sub(r"(</h2>\s*)<p>", r'\1<p class="lede">', body, count=1)
    # a blockquote becomes a pull-quote paragraph
    body = re.sub(r"<blockquote>\s*<p>(.*?)</p>\s*</blockquote>", r'<p class="pull">\1</p>', body, flags=re.S)
    return body


def _hero_figure(hero: dict) -> str:
    if not hero:
        return ""
    esc = lambda s: _html.escape(str(s or ""))
    return (
        '<figure class="fig">\n'
        '  <div class="surf">\n'
        '    <div class="surf__bar">\n'
        '      <span class="surf__dot surf__dot--live"></span><span class="surf__dot"></span><span class="surf__dot"></span>\n'
        f'      <span class="surf__title">The Debrief <code>{esc(hero.get("code"))}</code></span>\n'
        '    </div>\n'
        f'    <img class="shot" src="{esc(hero.get("image"))}" alt="{esc(hero.get("alt"))}">\n'
        '  </div>\n'
        f'  <figcaption>{esc(hero.get("caption"))}</figcaption>\n'
        '</figure>'
    )


def _evidence_rows(ev: dict) -> str:
    esc = lambda s: _html.escape(str(s or ""))
    rows = []
    for lbl in ("STARTED", "ENDED", "CHANGED"):
        rows.append(f'<div class="ev-row"><span class="lbl">{lbl}</span><span class="dots"></span>'
                    f'<span class="val">{esc(ev.get(lbl.lower()))}</span></div>')
    for learned in (ev.get("learned") or []):
        rows.append(f'<div class="ev-row learned"><span class="lbl">LEARNED</span><span class="dots"></span>'
                    f'<span class="val">{esc(learned)}</span></div>')
    return "\n              ".join(rows)


def render(header: dict, template: str, edition_md: str,
           edition_src_name: str = "edition.md", header_src_name: str = "header.yaml") -> tuple[str, list[str]]:
    """Fill the slotted template. Returns (html, unfilled_required_slots)."""
    esc = lambda s: _html.escape(str(s or ""))
    hero = header.get("hero") or {}
    ev = header.get("evidence") or {}
    subs = {
        "LESSON_NUM": esc(header.get("lesson_num") or header.get("edition_num")),
        "EDITION_NUM": esc(header.get("edition_num")),
        "KICKER_SUB": esc(header.get("kicker_sub")),
        "HEADLINE": esc(header.get("headline")),
        "STANDFIRST": esc(header.get("standfirst")),
        "BYLINE": esc(header.get("byline") or "the operator"),
        "BODY": _render_body(edition_md, _hero_figure(hero)),
        "EVIDENCE_ARIA": esc(ev.get("aria")),
        "EVIDENCE_CODE": esc(ev.get("code")),
        "EVIDENCE_ROWS": _evidence_rows(ev),
        "EVIDENCE_DATED": esc(ev.get("dated")),
        "PROMISE": esc(header.get("promise") or
                       "The Debrief is a lesson from building Soundtrak's AI Studio, with the evidence behind it. "
                       "If you are wiring AI into your own go-to-market, send yourself the next lesson."),
    }
    html = template
    for k, v in subs.items():
        html = html.replace("{{" + k + "}}", v)
    # provenance stamp (content-based, supersedes the mtime heuristic — SYS-094 part 3)
    prov = (f"<!-- GENERATED by render_issue_header.py — do not hand-edit. "
            f"sources: {edition_src_name}@{_sha(edition_md)} + {header_src_name}@{_sha(str(header))} -->")
    html = html.replace("<body>", f"<body>\n{prov}", 1) if "<body>" in html else prov + "\n" + html
    unfilled = re.findall(r"\{\{([A-Z_]+)\}\}", html)
    return html, unfilled


def run_asset(asset_dir: Path) -> int:
    try:
        import yaml
    except ImportError:
        raise SystemExit("pyyaml required")
    header_path = asset_dir / "header.yaml"
    if not header_path.exists():
        print(f"{asset_dir.name}: no header.yaml — this asset isn't on the single-source path (fine for #1-#4).", file=sys.stderr)
        return 1
    header = yaml.safe_load(header_path.read_text(encoding="utf-8")) or {}
    tmpl_rel = header.get("template", "issue-header-template.slotted.html")
    # template may live in the asset or a shared look-kit — try asset dir, then campaign look-kit
    tmpl_path = asset_dir / tmpl_rel
    if not tmpl_path.exists():
        cands = list((asset_dir.parent).glob(f"*look-kit*/{Path(tmpl_rel).name}"))
        tmpl_path = cands[0] if cands else tmpl_path
    edition_path = asset_dir / header.get("body_source", "edition.md")
    for label, p in (("template", tmpl_path), ("edition body", edition_path)):
        if not p.exists():
            print(f"{asset_dir.name}: {label} not found: {p}", file=sys.stderr)
            return 1
    html, unfilled = render(header, tmpl_path.read_text(encoding="utf-8"),
                            edition_path.read_text(encoding="utf-8"),
                            edition_src_name=edition_path.name)
    out = asset_dir / header.get("out", "issue-header.html")
    out.write_text(html, encoding="utf-8")
    print(f"Rendered {out.name} from {edition_path.name} + header.yaml (single source).")
    if unfilled:
        print(f"  ! unfilled slots: {sorted(set(unfilled))}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Render a Debrief issue header from a single source (SYS-094).")
    ap.add_argument("--asset")
    ap.add_argument("--header"); ap.add_argument("--template"); ap.add_argument("--edition"); ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.asset:
        return run_asset(Path(a.asset))
    if a.header and a.template and a.edition and a.out:
        import yaml
        header = yaml.safe_load(Path(a.header).read_text(encoding="utf-8")) or {}
        html, unfilled = render(header, Path(a.template).read_text(encoding="utf-8"),
                                Path(a.edition).read_text(encoding="utf-8"), edition_src_name=Path(a.edition).name)
        Path(a.out).write_text(html, encoding="utf-8")
        print(f"Rendered {a.out}" + (f"  ! unfilled: {sorted(set(unfilled))}" if unfilled else ""))
        return 1 if unfilled else 0
    ap.error("give --asset <dir>, or --header/--template/--edition/--out")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
