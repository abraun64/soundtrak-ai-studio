#!/usr/bin/env python3
"""SYS-085 — Brief structure lint. Checks a brief.md against the LOCKED canonical section
order (docs/specs/brief.md §"Canonical section order"): flags MISSING mandatory sections,
NON-CANONICAL top-level headings (that should fold into "Anything else" or be renamed), and
sections that are OUT OF ORDER. Run before surfacing a Brief — mandatory, alongside the
review-ready gate.

Usage:
  python brief_lint.py <brief.md> [<brief.md> ...] [--quiet]   # exit 1 if any issue
"""
import re
import sys
import io
from pathlib import Path

# Console-safe output (Windows cp1252 can't encode the emoji/dashes in headings).
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

# Canonical H2 sections IN ORDER, each with distinctive lower-case match phrases (first hit wins).
# OPTIONAL sections don't trigger a "missing" error (they legitimately don't always appear).
CANONICAL = [
    ("Why this campaign",           ["why this campaign"],                         False),
    ("Business objective",          ["business objective", "objective"],           False),
    ("The offer",                   ["the offer", "offer"],                        False),
    ("Audience",                    ["audience"],                                  False),
    ("Insights that matter",        ["insights that matter", "insight"],           True),
    ("How to reach them",           ["how to reach", "routes to market", "growth"],True),
    ("Single-minded proposition",   ["single-minded proposition", "proposition"],  False),
    ("Goal & KPI",                  ["goal & kpi", "goal and kpi", "goal / kpi", "kpi"], False),
    ("Brand context",               ["brand context"],                             False),
    ("Mandatories",                 ["mandatories", "mandatory"],                  False),
    ("Budget",                      ["budget"],                                    False),
    ("Timeline",                    ["timeline"],                                  False),
    ("Tech setup",                  ["tech setup", "tech stack"],                  True),
    ("Roles",                       ["roles", "human roles"],                      True),
    ("Cadence",                     ["cadence"],                                   True),
    ("Anything else",               ["anything else"],                             True),
    ("Approval record",             ["approval record"],                           False),
]


def _norm(h: str) -> str:
    h = re.sub(r"[^\x00-\x7f]", "", h)                 # strip emoji/non-ascii decoration
    h = re.sub(r"\([^)]*\)", "", h)                    # drop parenthetical qualifiers
    return h.strip().strip("*").strip().lower()


def _map(heading: str):
    n = _norm(heading)
    for name, phrases, _opt in CANONICAL:
        if any(p in n for p in phrases):
            return name
    return None


def lint(path: Path) -> list[str]:
    heads = re.findall(r"^##\s+(.+)$", path.read_text(encoding="utf-8", errors="replace"), re.M)
    seen, order = [], []
    issues = []
    idx = {name: i for i, (name, _, _) in enumerate(CANONICAL)}
    for h in heads:
        c = _map(h)
        if c is None:
            issues.append(f"NON-CANONICAL heading: '{h.strip()}' — fold into 'Anything else' or rename")
        else:
            seen.append(c)
            order.append(idx[c])
    for name, _phrases, optional in CANONICAL:
        if not optional and name not in seen:
            issues.append(f"MISSING mandatory section: '{name}'")
    if order != sorted(order):
        issues.append("sections OUT OF ORDER vs the locked canonical sequence")
    return issues


def main() -> int:
    files = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    if not files:
        print("usage: brief_lint.py <brief.md> [<brief.md> ...] [--quiet]")
        return 2
    total = 0
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"not found: {p}"); return 2
        issues = lint(p)
        total += len(issues)
        if quiet:
            continue
        if not issues:
            print(f"OK   {p} : matches the canonical Brief template.")
        else:
            print(f"FLAG {p} : {len(issues)} issue(s) vs the locked canonical order:")
            for i in issues:
                print(f"     - {i}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
