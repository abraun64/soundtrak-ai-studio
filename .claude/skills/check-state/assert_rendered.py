#!/usr/bin/env python3
"""
assert_rendered — SYS-135: prove a claim about a RENDERED surface, not its source.

The recurring failure this guards against: CM edits a campaign's markdown/yaml,
then tells the operator "the dashboard now shows X" — but the render never fired
(a stale worktree hook, a skipped re-render, a file:// tab serving cache), so the
operator opens the surface and X is not there. Trust in the gallery erodes.

Rule (CM contract): before telling the operator a surface is updated, assert the
RENDERED .html file actually contains the expected text. This helper is that
assertion, callable from CM's turn or any hook.

Usage:
  # every needle must be present (AND) — the common case
  python .claude/skills/check-state/assert_rendered.py campaigns/foo/dashboard.html "Phase 4" "Approved"

  # at least one needle present (OR)
  python .claude/skills/check-state/assert_rendered.py --any campaigns/foo/gallery.html "Launch tile" "Hero"

  # substring match is case-sensitive by default; --ignore-case to relax
  python .claude/skills/check-state/assert_rendered.py --ignore-case foo.html "approved"

Exit codes:
  0  file exists AND the needle condition holds  → safe to tell the operator "updated"
  1  a needle is missing (or --any found none)   → DO NOT claim updated; re-render first
  2  the file does not exist / cannot be read    → the render never produced a surface

Prints a one-line PASS/FAIL so the result is legible in a hook log or CM turn.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Assert a rendered surface contains the expected text (SYS-135).")
    ap.add_argument("file", help="path to the RENDERED .html surface to check")
    ap.add_argument("needles", nargs="+", help="text that must appear in the rendered file")
    ap.add_argument("--any", action="store_true",
                    help="pass if ANY needle is present (default: ALL must be present)")
    ap.add_argument("--ignore-case", action="store_true",
                    help="case-insensitive substring match")
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"FAIL (exit 2): rendered surface does not exist — {path}. "
              "The render never ran; re-render before telling the operator it is updated.",
              file=sys.stderr)
        return 2
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"FAIL (exit 2): cannot read {path} — {e}", file=sys.stderr)
        return 2

    hay = text.lower() if args.ignore_case else text
    def present(n: str) -> bool:
        return (n.lower() if args.ignore_case else n) in hay

    results = [(n, present(n)) for n in args.needles]
    missing = [n for n, ok in results if not ok]
    found = [n for n, ok in results if ok]

    if args.any:
        ok = bool(found)
        if ok:
            print(f"PASS: {path.name} contains at least one of "
                  f"{args.needles} (found: {found}).")
            return 0
        print(f"FAIL (exit 1): {path.name} contains NONE of {args.needles}. "
              "The rendered surface is stale/wrong — re-render, do not claim updated.",
              file=sys.stderr)
        return 1

    # ALL mode
    if not missing:
        print(f"PASS: {path.name} contains all expected text {args.needles}.")
        return 0
    print(f"FAIL (exit 1): {path.name} is missing {missing}. "
          "The rendered surface does not reflect the source — re-render "
          "(and reload the file:// tab) before telling the operator it is updated.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
