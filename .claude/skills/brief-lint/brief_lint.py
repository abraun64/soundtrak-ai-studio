#!/usr/bin/env python3
"""SYS-085 — Brief structure lint. Checks a brief.md against the LOCKED canonical section
order (docs/specs/brief.md §"Canonical section order"): flags MISSING mandatory sections,
NON-CANONICAL top-level headings (that should fold into "Anything else" or be renamed), and
sections that are OUT OF ORDER. Run before surfacing a Brief — mandatory, alongside the
review-ready gate.

v4 (2026-09-06) additionally checks the EXHAUSTIVE-INTAKE contract, on briefs that claim it. A
v4 brief is SELF-IDENTIFYING: it carries an interview coverage ledger. That avoids grandfathering
by date (fragile) — a brief either claims the higher bar or it doesn't, and the ones that claim it
are held to it:
  - it must also carry "What we already know" (the evidence base the ledger reports coverage of);
  - no ledger row may be left without a status.
A ledger with blank rows is WORSE than no ledger: it reads as coverage while proving nothing, which
is the one failure this whole mechanism exists to prevent.

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
    # v4 evidence base. OPTIONAL in the order check so briefs written before the exhaustive
    # intake don't all flag; REQUIRED for any brief that carries a coverage ledger (below).
    ("What we already know",        ["what we already know", "evidence base"],     True),
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


# The ledger's summary line and its rows. A row is "| <topic> | <status> | <note> |"; the status
# cell is the one that must never be empty.
_LEDGER_MARK = re.compile(r"interview coverage", re.I)
_ROW = re.compile(r"^\|\s*([A-H]\d[^|]*)\|([^|]*)\|", re.M)


def _ledger_issues(text: str, seen: list) -> list[str]:
    """The v4 exhaustive-intake checks. No-op unless the brief carries a coverage ledger."""
    if not _LEDGER_MARK.search(text):
        return []
    issues = []
    if "What we already know" not in seen:
        issues.append("carries an interview coverage ledger but is MISSING 'What we already know' "
                      "— the evidence base the ledger reports coverage of (docs/specs/brief.md v4)")
    blank = [m.group(1).strip() for m in _ROW.finditer(text) if not m.group(2).strip()]
    if blank:
        issues.append("coverage ledger rows with NO status (a blank row reads as coverage while "
                      "proving nothing): " + ", ".join(blank[:6]))
    return issues


def lint(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    heads = re.findall(r"^##\s+(.+)$", text, re.M)
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
    issues += _ledger_issues(text, seen)
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
