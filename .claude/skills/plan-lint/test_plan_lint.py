#!/usr/bin/env python3
"""
Regression tests for plan_lint.py — the deterministic checks on a campaign Plan.

Stdlib + PyYAML only (no pytest — it isn't installed). Run directly:
    python .claude/skills/plan-lint/test_plan_lint.py
Exit 0 = all pass; exit 1 = one or more failed.

The system smoke-test runs this. Each check below exists because the thing it catches was found BY
EYE on a long programme, and two of them were found only by accident. The tests assert both
directions: the check fires on the real failure, AND a well-formed plan passes — a lint that flags
good input gets ignored exactly like one that never fires.
"""
from __future__ import annotations
import importlib.util
import sys
import tempfile
from pathlib import Path

_PL = Path(__file__).resolve().parent / "plan_lint.py"
_spec = importlib.util.spec_from_file_location("_plan_lint", _PL)
_pl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pl)

_FAILED: list[str] = []

GOOD = """# Test — Plan v4

**Setting: Launch-then-ongoing** — stands up, then becomes a weekly engine.

## Waves

| Wave | Window | What it is for | Channels starting | Test and learn | Rows |
|---|---|---|---|---|---|
| 1 | 2026-10-01 -> 2026-10-31 | Stand up the basics | Brand foundation | - | 1, S1 |
| 2 | 2026-11-01 -> 2026-11-30 | Open the mailing channel | Email | Subject-line test | 2, S2 |

## Asset list

| # | Asset | Description | Type | Channel | Wave | Ships | Owner | Target date | Depends on | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Visual identity kit | The logo and templates | asset | Brand foundation | 1 | Logo (SVG) | Producer | 2026-10-10 | - | - |
| S1 | Create the account | Stand up the account | setup | Brand foundation | 1 | - | Operator | 2026-10-05 | - | Check: the address resolves |
| 2 | Welcome email | The first email a subscriber gets | asset | Email | 2 | Email (HTML) | Producer | 2026-11-15 | #1 | - |
| S2 | Create the mailing list | The list it sends to | setup | Email | 2 | - | Operator | 2026-11-02 | - | Check: a test arrives |
"""


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _lint(text: str, gallery: str | None = None) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "plan.md"
        p.write_text(text, encoding="utf-8")
        if gallery is not None:
            (Path(td) / "gallery-config.yaml").write_text(gallery, encoding="utf-8")
        return _pl.lint(p)


def test_a_well_formed_plan_passes() -> None:
    """The half people forget. A lint that flags good input trains everyone to skip it."""
    issues = _lint(GOOD)
    check("a well-formed v4 plan passes clean", not issues, f"{issues}")


def test_setting_must_be_declared() -> None:
    """The renderer used to classify Launch vs Ongoing by reading words in a column, which filed
    January builds — part of the ongoing engine — into a group of their own because nothing in
    their wording said 'ongoing'."""
    issues = _lint(GOOD.replace(
        "**Setting: Launch-then-ongoing** — stands up, then becomes a weekly engine.", ""))
    check("a plan with no declared Setting is flagged",
          any("Setting" in i for i in issues), f"{issues}")
    for value in ("Launch", "Ongoing", "Launch-then-ongoing"):
        txt = GOOD.replace("**Setting: Launch-then-ongoing** — stands up, then becomes a weekly engine.",
                           f"**Setting: {value}**")
        check(f"'{value}' is accepted as a Setting",
              not any("Setting" in i for i in _lint(txt)))


def test_row_ids_are_permanent() -> None:
    """A row id is an identity that dependencies, the gallery and the operator's own notes point
    at. S17 was used twice on the real programme; every dependency naming it silently repointed."""
    issues = _lint(GOOD.replace("| S2 | Create the mailing list", "| S1 | Create the mailing list"))
    check("a duplicate row id is flagged", any("DUPLICATE" in i for i in issues), f"{issues}")
    check("the flag names the offending id", any("'S1'" in i for i in issues), f"{issues}")


def test_setup_rows_need_a_runnable_check() -> None:
    """Without a test a person can run, a setup row gets marked done on hope — which is how the
    programme shipped with no mailing lists and no form routing."""
    issues = _lint(GOOD.replace("Check: a test arrives", "configured correctly"))
    check("a setup row with no Check: is flagged",
          any("no `Check:`" in i for i in issues), f"{issues}")
    check("an asset row is NOT asked for a Check:",
          not any("row '1'" in i and "Check:" in i for i in issues), f"{issues}")


def test_waves_run_forwards() -> None:
    issues = _lint(GOOD.replace("| 2 | 2026-11-01 -> 2026-11-30 |", "| 2 | 2026-09-01 -> 2026-09-30 |"))
    check("a wave starting before the previous one is flagged",
          any("run forwards" in i for i in issues), f"{issues}")


def test_a_wave_needs_a_window() -> None:
    issues = _lint(GOOD.replace("| 2 | 2026-11-01 -> 2026-11-30 |", "| 2 | TBD |"))
    check("a wave with no dated window is flagged",
          any("no dated window" in i for i in issues), f"{issues}")


def test_a_wave_needs_a_row_that_starts_it() -> None:
    """Every row in the wave depending on another row in the SAME wave means the wave opens
    blocked — nothing in it can be produced on day one."""
    blocked = GOOD.replace(
        "| S2 | Create the mailing list | The list it sends to | setup | Email | 2 | - | Operator | 2026-11-02 | - | Check: a test arrives |",
        "| S2 | Create the mailing list | The list it sends to | setup | Email | 2 | - | Operator | 2026-11-02 | #2 | Check: a test arrives |")
    blocked = blocked.replace("| 2 | Welcome email | The first email a subscriber gets | asset | Email | 2 | Email (HTML) | Producer | 2026-11-15 | #1 |",
                              "| 2 | Welcome email | The first email a subscriber gets | asset | Email | 2 | Email (HTML) | Producer | 2026-11-15 | S2 |")
    issues = _lint(blocked)
    check("a wave where everything depends on a sibling is flagged",
          any("no row that can start it" in i for i in issues), f"{issues}")


def test_dates_sit_inside_their_wave() -> None:
    issues = _lint(GOOD.replace("| Producer | 2026-11-15 |", "| Producer | 2026-12-25 |"))
    check("a row dated after its wave closes is flagged",
          any("closes" in i for i in issues), f"{issues}")
    issues = _lint(GOOD.replace("| Producer | 2026-10-10 |", "| Producer | 2026-09-01 |"))
    check("a row dated before its wave opens is flagged",
          any("opens" in i for i in issues), f"{issues}")


def test_gallery_channels_must_match() -> None:
    """The gallery derives its channels from the Plan, so a divergence means a row has nowhere to
    land — checked in BOTH directions."""
    gal = 'channels:\n  "Brand foundation":\n    blurb: x\n  "Measurement":\n    blurb: y\n'
    issues = _lint(GOOD, gallery=gal)
    check("a Plan channel missing from the gallery config is flagged",
          any("in the Plan but not gallery-config" in i for i in issues), f"{issues}")
    check("a gallery channel no Plan row uses is flagged",
          any("no Plan row uses it" in i for i in issues), f"{issues}")
    matching = 'channels:\n  "Brand foundation":\n    blurb: x\n  "Email":\n    blurb: y\n'
    check("matching channels pass", not _lint(GOOD, gallery=matching),
          f"{_lint(GOOD, gallery=matching)}")


def test_an_unreadable_plan_is_reported_not_skipped() -> None:
    """A lint that quietly checks nothing is the exact failure this file exists to prevent."""
    issues = _lint("# Plan v4\n\n**Setting: Launch**\n\nNo tables here at all.\n")
    check("a plan with no asset table is REPORTED", bool(issues), "silently passed")
    check("and says so plainly", any("no asset-list table" in i for i in issues), f"{issues}")


def main() -> int:
    print("plan-lint regression tests")
    test_a_well_formed_plan_passes()
    test_setting_must_be_declared()
    test_row_ids_are_permanent()
    test_setup_rows_need_a_runnable_check()
    test_waves_run_forwards()
    test_a_wave_needs_a_window()
    test_a_wave_needs_a_row_that_starts_it()
    test_dates_sit_inside_their_wave()
    test_gallery_channels_must_match()
    test_an_unreadable_plan_is_reported_not_skipped()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll plan-lint tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
