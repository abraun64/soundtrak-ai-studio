#!/usr/bin/env python3
"""
Regression tests for weekly-digest.py — the escalation machinery that turns a persistent
diagnostic failure into a backlog ticket.

Stdlib + PyYAML only (no pytest — it isn't installed). Run directly:
    python .claude/skills/system-manager/test_weekly_digest.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this. Tests write only to a temp dir — the real system/ is never
touched (the module's SYSTEM_DIR global is redirected for the duration of each test).
"""
from __future__ import annotations
import importlib.util
import sys
import tempfile
from pathlib import Path

_WD = Path(__file__).resolve().parent / "weekly-digest.py"
_spec = importlib.util.spec_from_file_location("_weekly_digest", _WD)
_wd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wd)

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _seed(tmp: Path) -> list:
    """A system/ dir with one existing ticket, and the in-memory backlog the digest loads."""
    (tmp / "backlog.yaml").write_text(
        "items:\n  - id: SYS-140\n    title: \"Something else\"\n    status: todo\n",
        encoding="utf-8")
    _wd.SYSTEM_DIR = tmp
    return _wd.load_items(tmp / "backlog.yaml", "items")


def test_two_escalations_get_distinct_ids() -> None:
    """2026-08-11: smoke-test and drift-gate both escalated in one run, both computed their id
    from the same stale in-memory backlog, and both wrote a block claiming SYS-141. The
    collision had to be repaired by hand. The second escalation must see the first."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        backlog = _seed(tmp)
        a = _wd.escalate_to_ticket("smoke-test", 4, backlog, "2026-08-11")
        b = _wd.escalate_to_ticket("drift-gate", 2, backlog, "2026-08-11")
        check("two escalations in one run get distinct ids", a != b, f"both filed as {a}")
        import yaml
        written = yaml.safe_load((tmp / "backlog.yaml").read_text(encoding="utf-8"))["items"]
        ids = [i["id"] for i in written]
        check("backlog.yaml has no duplicate ids after a double escalation",
              len(ids) == len(set(ids)), f"ids: {ids}")
        check("backlog.yaml stays parseable", len(written) == 3, f"got {len(written)} items")


def test_same_label_is_deduped() -> None:
    """One open ticket per failing diagnostic — a weekly re-run must not stack duplicates."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        backlog = _seed(tmp)
        first = _wd.escalate_to_ticket("smoke-test", 4, backlog, "2026-08-11")
        again = _wd.escalate_to_ticket("smoke-test", 5, backlog, "2026-08-18")
        check("a second escalation for the same label is deduped",
              first is not None and again is None, f"first={first} again={again}")


def test_recovery_lookup() -> None:
    """SYS-141 — a diagnostic going green left its P1 ticket open with nothing saying so.
    open_escalation() is what the digest's recovery section reads; a DONE ticket must not
    resurface, and an open one must."""
    backlog = [
        {"id": "SYS-122", "title": "Persistent diagnostic failure: smoke-test", "status": "done"},
        {"id": "SYS-141", "title": "Persistent diagnostic failure: smoke-test", "status": "todo"},
        {"id": "SYS-142", "title": "Persistent diagnostic failure: drift-gate", "status": "done"},
    ]
    open_one = _wd.open_escalation(backlog, "smoke-test")
    check("an OPEN escalation is found for the recovery report",
          open_one is not None and open_one["id"] == "SYS-141", f"got {open_one}")
    check("a CLOSED escalation does not resurface",
          _wd.open_escalation(backlog, "drift-gate") is None)
    check("a label with no ticket returns None",
          _wd.open_escalation(backlog, "nav-audit") is None)


def test_diagnostic_output_decoding() -> None:
    """The diagnostics disagree on output encoding. Decoding everything as cp1252 put "â€”" in
    the digest the operator reads (2026-07-27); decoding everything as UTF-8 with replace fixed
    those and produced U+FFFD for the others, which then crashed `print(digest)` on a cp1252
    console (2026-09-06). Neither side is right — try UTF-8 first, fall back."""
    check("utf-8 output decodes cleanly",
          _wd._decode("RESULT: RED — 1 issue".encode("utf-8")) == "RESULT: RED — 1 issue")
    check("cp1252 output decodes cleanly",
          _wd._decode("RESULT: RED — 1 issue".encode("cp1252")) == "RESULT: RED — 1 issue")
    check("no replacement characters survive either way",
          "�" not in _wd._decode("done — ok".encode("cp1252"))
          and "�" not in _wd._decode("done — ok".encode("utf-8")))


def test_escalation_is_not_blocked_by_its_own_idea() -> None:
    """SYS-010 files an idea on failure #1 and escalates to a ticket on failure #2. The
    fingerprint suppression must not count that idea — it is the very thing being promoted.
    Observed live 2026-09-06: smoke-test and docs-audit sat RED with only an inbox row, because
    the idea filed on the first failure blocked the ticket on the second."""
    import tempfile

    idea = "\n".join([
        "items:",
        "  - id: IDEA-067",
        '    title: "Diagnostic failing: smoke-test"',
        '    fingerprint: "weekly-digest:diagnostic:smoke-test"',
        "",
    ])
    other = "\n".join([
        "items:",
        "  - id: SYS-140",
        '    title: "Something else"',
        "    status: todo",
        "",
    ])
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "ideas.yaml").write_text(idea, encoding="utf-8")
        (tmp / "backlog.yaml").write_text(other, encoding="utf-8")
        saved = _wd.SYSTEM_DIR
        _wd.SYSTEM_DIR = tmp
        try:
            backlog = _wd.load_items(tmp / "backlog.yaml", "items")
            tid = _wd.escalate_to_ticket("smoke-test", 2, backlog, "2026-09-06")
            check("a standing idea does not block its own escalation", tid is not None,
                  "escalate_to_ticket returned None")
            check("filing a NEW idea is still deduped against that standing idea",
                  "weekly-digest:diagnostic:smoke-test" in _wd.suppressed_fingerprints())
        finally:
            _wd.SYSTEM_DIR = saved


def test_drift_reports_before_it_accepts() -> None:
    """The safety property of the weekly drift step, and the only one that matters.

    Nothing ever moved drift findings from NEW into the baseline except a human remembering to
    type --write-baseline, so NEW accumulated forever and the gate sat permanently red - which is
    indistinguishable from broken (SYS-141). The digest now ratchets it weekly. The danger in that
    is obvious: auto-accepting silently would kill the guard outright, since everything would be
    accepted the moment it appeared.

    What makes it safe is ORDER. The gate is read and the findings captured BEFORE the baseline is
    written, so every accepted finding appears in the digest the operator reads. This asserts the
    read happens first: if the implementation ever ratchets before reporting, the recorded call
    order changes and this fails."""
    calls = []

    class FakeRun:
        def __init__(self, out):
            self.stdout = out
            self.stderr = b""
            self.returncode = 0

    real = _wd.subprocess.run

    def fake(args, **kw):
        calls.append("--write-baseline" if "--write-baseline" in args else "read")
        if "--write-baseline" in args:
            return FakeRun(b"baseline written")
        return FakeRun(b"drift gate: 87 total  86 known  3 NEW  0 resolved\n"
                       b"     - camp::plan::asset folder 99-probe has NO row\n"
                       b"     - camp::board::pending action in phase 1\n")

    _wd.subprocess.run = fake
    try:
        count, sample, ratcheted = _wd.drift_delta(Path(__file__))
    finally:
        _wd.subprocess.run = real

    check("the NEW count is read off the gate", count == 3, f"got {count}")
    check("the findings are captured for the digest", len(sample) == 2, f"got {sample}")
    check("the baseline was ratcheted", ratcheted is True)
    check("it READ before it accepted - nothing is swallowed unreported",
          calls == ["read", "--write-baseline"], f"call order was {calls}")


def test_no_drift_means_no_ratchet() -> None:
    """A quiet week must not touch the baseline at all - writing one on every run regardless
    would make the file churn and hide when acceptance actually happened."""
    class FakeRun:
        stdout = b"drift gate: 86 total  86 known  0 NEW  0 resolved\n"
        stderr = b""
        returncode = 0

    calls = []
    real = _wd.subprocess.run

    def fake(args, **kw):
        calls.append(args)
        return FakeRun()

    _wd.subprocess.run = fake
    try:
        count, sample, ratcheted = _wd.drift_delta(Path(__file__))
    finally:
        _wd.subprocess.run = real
    check("no new drift reports nothing", count == 0 and sample == [])
    check("and does not write a baseline", ratcheted is False and len(calls) == 1,
          f"{len(calls)} call(s)")


def main() -> int:
    print("weekly-digest escalation tests")
    test_diagnostic_output_decoding()
    test_escalation_is_not_blocked_by_its_own_idea()
    test_drift_reports_before_it_accepts()
    test_no_drift_means_no_ratchet()
    saved = _wd.SYSTEM_DIR
    try:
        test_two_escalations_get_distinct_ids()
        test_same_label_is_deduped()
        test_recovery_lookup()
    finally:
        _wd.SYSTEM_DIR = saved
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll weekly-digest tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
