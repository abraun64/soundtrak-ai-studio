#!/usr/bin/env python3
"""
Regression tests for brief_lint.py — the structure gate every Brief passes before an operator
sees it.

Stdlib only (no pytest — it isn't installed). Run directly:
    python .claude/skills/brief-lint/test_brief_lint.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this. The v4 checks are the ones with teeth: the exhaustive intake is
only worth anything if "we covered everything" is falsifiable, so these assert that a ledger with
holes in it FAILS rather than reading as coverage.
"""
from __future__ import annotations
import importlib.util
import sys
import tempfile
from pathlib import Path

_BL = Path(__file__).resolve().parent / "brief_lint.py"
_spec = importlib.util.spec_from_file_location("_brief_lint", _BL)
_bl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bl)

_FAILED: list[str] = []

# Every mandatory section, in canonical order — the minimum a brief needs to pass the order check.
_MANDATORY = [
    "Why this campaign", "Business objective", "The offer", "Audience",
    "Single-minded proposition", "Goal & KPI", "Brand context", "Mandatories",
    "Budget", "Timeline", "Approval record",
]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _brief(*, evidence: bool = False, ledger: str | None = None) -> list[str]:
    """Write a minimal well-formed brief (optionally v4) to a temp file and lint it."""
    parts = ["# Test — Brief v1", ""]
    for s in _MANDATORY:
        parts += [f"## {s}", "body", ""]
        if s == "Why this campaign" and evidence:
            parts += ["## What we already know", "body", ""]
        if s == "Approval record" and ledger is not None:
            parts += [ledger, ""]
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "brief.md"
        p.write_text("\n".join(parts), encoding="utf-8")
        return _bl.lint(p)


_GOOD_LEDGER = (
    "<details markdown=\"1\">\n"
    "<summary><strong>Interview coverage</strong> — 3 topics</summary>\n\n"
    "| Topic | Status | Note |\n|---|---|---|\n"
    "| A3 Baseline | answered | 4.1% avg engagement |\n"
    "| B2 Prior results | homework · load-bearing | LinkedIn export, by Fri |\n"
    "| G5 Tech setup | n/a | resolved at Phase 3 |\n"
    "</details>"
)
_HOLED_LEDGER = _GOOD_LEDGER.replace("| B2 Prior results | homework · load-bearing |",
                                     "| B2 Prior results |  |")


def test_pre_v4_brief_is_unaffected() -> None:
    """Briefs written before the exhaustive intake carry no ledger, so the v4 checks must not fire.
    The alternative — grandfathering by date — is fragile; self-identification is not."""
    check("a brief with no ledger passes unchanged", _brief() == [], f"{_brief()}")


def test_evidence_section_is_allowed_but_not_demanded() -> None:
    """'What we already know' is optional in the order check, so adding it can't break a brief and
    omitting it can't fail one — unless the brief claims v4 (below)."""
    check("the evidence section is accepted in canonical position",
          _brief(evidence=True) == [], f"{_brief(evidence=True)}")


def test_a_ledger_demands_the_evidence_section() -> None:
    """A ledger reports coverage OF the evidence base. Claiming coverage while the evidence
    section is absent is the shape of a brief that looks thorough and isn't."""
    issues = _brief(evidence=False, ledger=_GOOD_LEDGER)
    check("a ledger without 'What we already know' is flagged",
          any("What we already know" in i for i in issues), f"{issues}")
    check("a ledger WITH the evidence section is clean",
          _brief(evidence=True, ledger=_GOOD_LEDGER) == [],
          f"{_brief(evidence=True, ledger=_GOOD_LEDGER)}")


def test_blank_ledger_rows_fail() -> None:
    """The one that matters. A row with no status reads as covered at a glance while proving
    nothing — worse than having no ledger at all, because it buys false confidence."""
    issues = _brief(evidence=True, ledger=_HOLED_LEDGER)
    check("a ledger row with no status is flagged",
          any("NO status" in i for i in issues), f"{issues}")
    check("the flag names the offending topic",
          any("B2" in i for i in issues), f"{issues}")


def test_all_ledger_statuses_are_accepted() -> None:
    """answered / assumed / homework / inherited / n/a are all legitimate — the bar is that a
    status EXISTS, not that it is 'answered'. A brief may honestly proceed on assumptions."""
    every = _GOOD_LEDGER.replace(
        "| G5 Tech setup | n/a | resolved at Phase 3 |",
        "| G5 Tech setup | n/a | resolved at Phase 3 |\n"
        "| D4 Untested beliefs | assumed | no data; flagged for the CD |\n"
        "| F2 Claims | inherited | playbook §0 claim map |")
    check("assumed / inherited / n/a rows all pass",
          _brief(evidence=True, ledger=every) == [],
          f"{_brief(evidence=True, ledger=every)}")


def main() -> int:
    print("brief-lint regression tests")
    test_pre_v4_brief_is_unaffected()
    test_evidence_section_is_allowed_but_not_demanded()
    test_a_ledger_demands_the_evidence_section()
    test_blank_ledger_rows_fail()
    test_all_ledger_statuses_are_accepted()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll brief-lint tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
