#!/usr/bin/env python3
"""
inline_guide_css — keep the self-contained guide's CSS in step with the shared stylesheet.

Most guide pages link `docs/guide/style.css` as a sibling. That is right for pages read
inside the repo. The ORGANISATION guide is different: it is the page you SEND to a
prospective customer, often before they have installed anything, and a linked stylesheet
does not travel with a single file. It arrives unstyled.

So that one page carries a verbatim inline copy — which creates a duplicate, and a
duplicate nobody checks is drift waiting to happen (the bug class `data-architecture.md`
exists to prevent). This is the tool that keeps them equal, plus the check that proves it.

  python .claude/lib/inline_guide_css.py            # refresh the inline copy
  python .claude/lib/inline_guide_css.py --check    # exit 1 if it has drifted

The smoke test runs --check, so style.css changing without this being re-run is caught
rather than discovered by a customer looking at a half-branded page.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "guide" / "style.css"
# Pages that must carry the stylesheet INLINE rather than linking it.
TARGETS = [ROOT / "docs" / "guide" / "org-deployment-guide.html",
           ROOT / "docs" / "guide" / "org-faq.html"]

BLOCK = re.compile(r"<style>\n(.*?)\n</style>", re.S)


def current(page: Path) -> str | None:
    m = BLOCK.search(page.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def refresh(page: Path, css: str) -> bool:
    text = page.read_text(encoding="utf-8")
    if not BLOCK.search(text):
        print(f"  {page.name}: no <style> block to refresh", file=sys.stderr)
        return False
    updated = BLOCK.sub(lambda _m: f"<style>\n{css}\n</style>", text, count=1)
    if updated == text:
        return False
    page.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report drift, change nothing")
    a = ap.parse_args()

    if not SOURCE.is_file():
        print(f"missing {SOURCE}", file=sys.stderr)
        return 1
    css = SOURCE.read_text(encoding="utf-8").rstrip()

    drifted = []
    for page in TARGETS:
        if not page.is_file():
            continue
        if current(page) != css:
            drifted.append(page)

    if a.check:
        if drifted:
            print("inline-guide-css: DRIFT — these carry a stale copy of style.css:")
            for p in drifted:
                print(f"  {p.relative_to(ROOT)}")
            print("  fix: python .claude/lib/inline_guide_css.py")
            return 1
        print("inline-guide-css: in step with style.css.")
        return 0

    if not drifted:
        print("inline-guide-css: already in step; nothing to do.")
        return 0
    for p in drifted:
        if refresh(p, css):
            print(f"inline-guide-css: refreshed {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
