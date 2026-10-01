#!/usr/bin/env python3
"""Regression tests for source_trace_check.py (SYS-173). Stdlib only. Run directly:
    python .claude/skills/content-subedit/test_source_trace_check.py
The system smoke-test runs this.

The check is must-record: it cannot judge whether a trace is true, only that it was done and
that nothing untraced survived. So the tests are about the two failures that matter — a report
that says "Rule 10: clear" with no table (the exact step that let eds 22-28 through), and an
untraced row left standing in the copy.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "source_trace_check.py"
_spec = importlib.util.spec_from_file_location("_stc", _P)
_stc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_stc)

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


GOOD = """RULE 9 — EDITORIAL TICS: 0
RULE 10 — SOURCE TRACE: 3 items · 2 untraced (cut/rewritten) · 0 kept
| # | Draft line | Type | Source | Outcome |
|---|---|---|---|---|
| 1 | "CRM fields pre-populated" | result | library notes: "default CRM fields pre-populated" | TRACED |
| 2 | "For years I thought you changed behaviour by explaining it" | feeling | none | UNTRACED → CUT |
| 3 | "at Netwealth ... adoption crawled" | role | notes give the rollout, not the employer or the struggle | OVERSTATED -> REWRITTEN |
"""


def main() -> int:
    print("source-trace check tests")
    ok, msg, c = _stc.check_text(GOOD)
    check("a full trace with every untraced row disposed passes", ok, msg)
    check("it counts rows and dispositions", c == {"rows": 3, "untraced_kept": 0, "disposed": 2}, str(c))

    ok, msg, _ = _stc.check_text("RULE 10 — FABRICATED SCENE: ✓ No violations.")
    check("'no violations' with no trace FAILS (asserted, not recorded)", not ok, msg)

    ok, msg, _ = _stc.check_text("RULE 1 — EM-DASHES: 0\nRULE 2 — BANNED WORDS: 0\n")
    check("a report with no Rule 10 block at all FAILS", not ok, msg)

    ok, msg, _ = _stc.check_text("RULE 10 — SOURCE TRACE\n\nI checked it against the brief.\n")
    check("a header with prose instead of a table FAILS", not ok, msg)

    kept = GOOD.replace("UNTRACED → CUT", "UNTRACED")
    ok, msg, c = _stc.check_text(kept)
    check("an UNTRACED row left in the copy FAILS", not ok and c.get("untraced_kept") == 1, msg)

    vague = GOOD.replace("| TRACED |", "| looks fine |")
    ok, msg, _ = _stc.check_text(vague)
    check("an outcome that is not one of the named values FAILS", not ok, msg)

    nocol = GOOD.replace("| Source | Outcome |", "| Notes | Result |")
    ok, msg, _ = _stc.check_text(nocol)
    check("a table without Source and Outcome columns FAILS", not ok, msg)

    arch = GOOD.replace("| 3 |", '| 4 | "You sign up on one screen; leaving takes three menus" | scene | none | ARCHETYPE |\n| 3 |')
    ok, msg, c = _stc.check_text(arch)
    check("a second-person archetypal scene is allowed", ok and c["untraced_kept"] == 0, msg)

    disguised = GOOD.replace("| 3 |", '| 4 | "I sat in a review where the room nodded along" | scene | none | ARCHETYPE |\n| 3 |')
    ok, msg, _ = _stc.check_text(disguised)
    check("a first-person memory relabelled ARCHETYPE FAILS", not ok, msg)

    ok, msg, c = _stc.check_text("RULE 10 — SOURCE TRACE: 0 items (no scene, feeling, role or author result)")
    check("an explicit zero is a valid record", ok and c["rows"] == 0, msg)

    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll source-trace check tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
