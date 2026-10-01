#!/usr/bin/env python3
"""SYS-173 — Rule 10 source-trace check. MUST-RECORD, not must-judge.

WHY THIS EXISTS. Rule 10 (fabricated scene, interiority and role) is the single most-cut AI tell
in the operator's edits, and it cannot be linted: it is semantic, so a new draft invents a new scene in
new words and no regex or count can see it. The catch is a read against the source. But "I read
it and it's fine" is exactly the step that let eds 22-28 through, so the read has to PRODUCE a
table that names every scene, feeling, role claim and author result and says where each came
from (content-subedit references/voice-rules.md, Rule 10 verification protocol).

This script cannot tell whether a trace is TRUE. It checks that the trace was DONE and that
nothing untraced survived into the copy:
  1. a "RULE 10 — SOURCE TRACE" block exists;
  2. it is either an explicit zero ("0 items") or a table with an Outcome column;
  3. every row is TRACED, ARCHETYPE (a plainly-not-the-author scene: no first person in the
     line), or names what happened to it (UNTRACED/OVERSTATED -> CUT/REWRITTEN).
A row left UNTRACED or OVERSTATED with no disposition means invented material is still in the
draft: that fails, because Rule 10's limit is zero.

Same shape as the verification framework's `verified:` rule (must-record): absence is the
failure it exists to catch, because absence is indistinguishable from "nobody looked".

Usage:
  python source_trace_check.py <report.md> [...]      exit 0 = recorded + clean; 1 = not
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

_HEADER = re.compile(r"RULE\s*10\b[^\n]*SOURCE[\s-]*TRACE", re.I)
_ZERO = re.compile(r"SOURCE[\s-]*TRACE\s*[:\-—]\s*0\s+items?\b", re.I)
_DISPOSED = re.compile(r"(?:->|→)\s*(?:CUT|REWRITTEN)\b", re.I)
_BAD = re.compile(r"\b(?:UNTRACED|OVERSTATED)\b", re.I)
_OK = re.compile(r"\bTRACED\b", re.I)
# An archetypal scene is allowed (operator ruling 2026-07-30: "archetypal scenes OK, fabricated
# personal events not") but only when it is plainly not the author: no first person in the line.
# Otherwise ARCHETYPE becomes the label that lets an invented memory through.
_ARCHETYPE = re.compile(r"\bARCHETYPE\b", re.I)
_FIRST_PERSON = re.compile(r"\b(?:I|I'm|I've|I'd|me|my|mine|we|we're|we've|us|our|ours)\b")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def check_text(text: str) -> tuple[bool, str, dict]:
    """Returns (ok, message, counts)."""
    m = _HEADER.search(text)
    if not m:
        return False, "no 'RULE 10 — SOURCE TRACE' block: the trace was not recorded", {}
    block = text[m.start():]
    head_line = block.splitlines()[0]
    if _ZERO.search(head_line):
        return True, "recorded: 0 items (no scene, feeling, role or author result)", \
            {"rows": 0, "untraced_kept": 0, "disposed": 0}

    lines = block.splitlines()[1:]
    # the first markdown table after the header (skip blank lines / one-line notes)
    i = 0
    while i < len(lines) and not lines[i].lstrip().startswith("|"):
        if i > 6:
            break
        i += 1
    table = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        table.append(lines[i])
        i += 1
    if len(table) < 2:
        return False, ("RULE 10 header found but no trace table under it (and no explicit "
                       "'SOURCE TRACE: 0 items'): the trace was asserted, not recorded"), {}
    cols = [c.lower() for c in _cells(table[0])]
    out_col = next((k for k, c in enumerate(cols) if "outcome" in c or "verdict" in c), None)
    src_col = next((k for k, c in enumerate(cols) if "source" in c), None)
    if out_col is None or src_col is None:
        return False, f"trace table needs Source and Outcome columns, got {cols}", {}

    rows = [r for r in table[1:] if not re.fullmatch(r"\|?[\s:|-]+\|?", r.strip())]
    kept, disposed, bad_rows = 0, 0, []
    for r in rows:
        cells = _cells(r)
        outcome = cells[out_col] if out_col < len(cells) else ""
        if _ARCHETYPE.search(outcome) and not _BAD.search(outcome):
            quote = " ".join(c for k, c in enumerate(cells) if k not in (out_col, src_col))
            if _FIRST_PERSON.search(quote.replace("’", "'")):
                kept += 1
                bad_rows.append(r.strip()[:120] + "   <- ARCHETYPE but written in the first person")
            continue
        if _BAD.search(outcome):
            if _DISPOSED.search(outcome):
                disposed += 1
            else:
                kept += 1
                bad_rows.append(r.strip()[:120])
        elif not _OK.search(outcome):
            kept += 1
            bad_rows.append(r.strip()[:120] + "   <- outcome is not TRACED / ARCHETYPE / UNTRACED -> CUT|REWRITTEN")
    counts = {"rows": len(rows), "untraced_kept": kept, "disposed": disposed}
    if not rows:
        return False, "trace table has no rows (write 'SOURCE TRACE: 0 items' if there are none)", counts
    if kept:
        return False, (f"{kept} untraced/overstated item(s) still in the copy (Rule 10 limit is "
                       "zero):\n      " + "\n      ".join(bad_rows)), counts
    return True, f"recorded: {len(rows)} item(s), {disposed} cut or rewritten, 0 kept", counts


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[-1])
        return 2
    worst = 0
    for a in argv:
        p = Path(a)
        if not p.exists():
            print(f"FAIL {a}: not found")
            worst = 1
            continue
        ok, msg, _ = check_text(p.read_text(encoding="utf-8", errors="replace"))
        print(f"{'OK  ' if ok else 'FAIL'} {p.name}: {msg}")
        worst = max(worst, 0 if ok else 1)
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
