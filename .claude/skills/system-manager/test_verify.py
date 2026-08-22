#!/usr/bin/env python3
"""
Regression tests for verify.py — the SYS-138 verification level runner.

Stdlib + PyYAML only (no pytest — it isn't installed). Run directly:
    python .claude/skills/system-manager/test_verify.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this. `--audit` is the piece under test: it is the only thing
standing between "closed" and "closed without anyone checking", so it has to flag a bare
closure, stay quiet on a recorded one, and — importantly — not drown the signal in the 140
historical closures that predate the framework.
"""
from __future__ import annotations
import importlib.util
import sys
import tempfile
from pathlib import Path

_V = Path(__file__).resolve().parent / "verify.py"
_spec = importlib.util.spec_from_file_location("_verify", _V)
_vf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vf)

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _audit_with(items_yaml: str) -> int:
    """Run audit() against a synthetic backlog. Returns its exit code (0 clean, 1 findings)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "backlog.yaml").write_text("items:\n" + items_yaml, encoding="utf-8")
        saved = _vf.SYSTEM_DIR
        _vf.SYSTEM_DIR = tmp
        try:
            return _vf.audit()
        finally:
            _vf.SYSTEM_DIR = saved


def test_bare_closure_is_flagged() -> None:
    """The whole point: a ticket closed with nothing recorded must be visible."""
    code = _audit_with('  - id: SYS-200\n    title: "A thing"\n    status: done\n'
                       '    date: 2026-08-01\n'
                       '    resolution: "2026-08-25 — RESOLVED. Did the thing."\n')
    check("a closure with no `verified:` is flagged", code == 1)


def test_recorded_closure_is_clean() -> None:
    code = _audit_with('  - id: SYS-200\n    title: "A thing"\n    status: done\n'
                       '    date: 2026-08-01\n'
                       '    resolution: "2026-08-25 — RESOLVED. Did the thing."\n'
                       '    verified: "L1 — smoke test — RESULT: ALL GREEN"\n')
    check("a closure that records its verification is clean", code == 0)


def test_close_date_comes_from_the_resolution() -> None:
    """`date:` is when a ticket was RAISED, not closed. Auditing on it silently exempts every
    long-lived ticket — SYS-136 and SYS-141 were both raised before the framework and closed
    after it, and an audit keyed on `date:` missed both."""
    old_raise_new_close = ('  - id: SYS-136\n    title: "Raised long ago"\n    status: done\n'
                           '    date: 2026-08-03\n'
                           '    resolution: "2026-08-22 — RESOLVED. Fixed."\n')
    check("a ticket raised before the framework but closed after it is audited",
          _audit_with(old_raise_new_close) == 1)
    check("the close date is read from the resolution",
          _vf._closed_on({"date": "2026-08-03",
                          "resolution": "2026-08-22 — RESOLVED. Fixed."}) == "2026-08-22")
    check("it falls back to `date:` when there is no resolution",
          _vf._closed_on({"date": "2026-08-03"}) == "2026-08-03")


def test_historical_closures_are_not_audited() -> None:
    """140 tickets closed before the framework existed. Flagging them would be noise that
    trains the operator to ignore the report — the exact failure this area keeps producing."""
    code = _audit_with('  - id: SYS-001\n    title: "Ancient"\n    status: done\n'
                       '    date: 2026-06-01\n'
                       '    resolution: "2026-06-02 — RESOLVED. Long before the framework."\n')
    check("closures predating the framework are not flagged", code == 0)


def test_open_tickets_are_not_audited() -> None:
    """Verification is required at CLOSE. Nagging about open work would make the report useless."""
    code = _audit_with('  - id: SYS-201\n    title: "Still going"\n    status: in_progress\n'
                       '    date: 2026-08-25\n')
    check("an open ticket is not asked for verification yet", code == 0)


def test_unit_suites_are_discovered() -> None:
    """`--level 3` globs for test_*.py, so the glob is the registry. If discovery breaks, the
    runner reports a cheerful green having run nothing."""
    suites = {p.name for p in _vf.unit_suites()}
    check("the runner discovers this very test file", "test_verify.py" in suites,
          f"found: {sorted(suites)}")
    check("the runner discovers suites outside its own skill",
          "test_surface_freshness.py" in suites, f"found: {sorted(suites)}")


def main() -> int:
    print("verify.py regression tests")
    test_bare_closure_is_flagged()
    test_recorded_closure_is_clean()
    test_close_date_comes_from_the_resolution()
    test_historical_closures_are_not_audited()
    test_open_tickets_are_not_audited()
    test_unit_suites_are_discovered()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll verify.py tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
