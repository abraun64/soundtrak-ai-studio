#!/usr/bin/env python3
"""
Regression tests for operator_actions.py — the module that decides what the dashboard
and tasks queue tell the operator to do next.

Stdlib only (no pytest — it isn't installed). Run directly:
    python .claude/skills/render-html/test_operator_actions.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this, so a regression goes RED there before it can reach a
campaign surface. Each test names the live failure it guards.
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operator_actions as oa  # noqa: E402

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _campaign(tmp: Path, name: str, *, phase5: bool, rollout_doc: bool) -> Path:
    """Minimal on-disk campaign in the shape that triggered the SYS-136 hang: production
    derived from assets, Phase 5 derived from launch-blockers (the cycle's entry point)."""
    cd = tmp / name
    (cd / "assets" / "01-thing").mkdir(parents=True)
    phases = [
        "  - id: 1\n    title: Fact-Find\n    status_mode: explicit\n    status: \u2705 Approved\n",
        "  - id: 4\n    title: Production\n    status_mode: derive_assets\n",
    ]
    if phase5:
        phases.append("  - id: 5\n    title: Launch\n    status_mode: derive_blocks_launch\n")
    (cd / "campaign.yaml").write_text(
        f"slug: {name}\ntenant: test\nstatus: active\nphases:\n" + "".join(phases),
        encoding="utf-8")
    (cd / "assets" / "01-thing" / "asset.yaml").write_text(
        "id: A1\nname: Thing\nchannel: LinkedIn\nstatus: \u2705 Approved\nship: true\n",
        encoding="utf-8")
    if rollout_doc:
        (cd / "phase-5-rollout.md").write_text("# Phase 5\n\nStatus: Draft\n", encoding="utf-8")
    return cd


def test_no_reentrant_scan() -> None:
    """SYS-136: _phase5_gap_action -> _current_phase_num -> _phase_done(derive_blocks_launch)
    -> scan_campaign -> _phase5_gap_action re-entered ~200 levels deep, each level doing a full
    campaign disk scan, until the recursion limit tripped and an inner `except Exception`
    swallowed the RecursionError. It always "finished", so completion proves nothing — the
    assertion has to be on the NESTING DEPTH. Depth 2 is the fixed shape (the outer scan asks
    _phase_done, whose one nested scan is legitimate and hits the guard); depth 196 was the
    broken one. On a real campaign the blowup cost minutes: gamma-launch-2026q2's dashboard
    render exceeded the Stop hook's 60s budget, was killed, and the surface silently kept
    serving stale content (verified 2026-09-06; depth 196 before the fix, 2 after)."""
    depth = {"now": 0, "max": 0}
    inner = oa.scan_campaign

    def traced(cd):
        depth["now"] += 1
        depth["max"] = max(depth["max"], depth["now"])
        try:
            return inner(cd)
        finally:
            depth["now"] -= 1

    with tempfile.TemporaryDirectory() as td:
        cd = _campaign(Path(td), "cyc-2026q1", phase5=True, rollout_doc=False)
        oa.scan_campaign = traced          # _phase_done resolves the module global, so this
        try:                               # intercepts the INNER calls too
            actions = traced(cd)
        finally:
            oa.scan_campaign = inner
        check("scan_campaign does not recurse on a derive_blocks_launch + Phase-5 campaign",
              depth["max"] <= 2, f"max nesting depth was {depth['max']} (expected <= 2)")
        check("the Phase-5 gap To Do still fires in that shape",
              any(a.get("id") == "phase5-author" for a in actions),
              f"got ids: {[a.get('id') for a in actions]}")


def test_gap_suppressed_once_rollout_authored() -> None:
    """The gap catch must fire ONLY in the gap. Once phase-5-rollout.md exists its own
    approval gate owns the surface, so a second synthetic row would double-report."""
    with tempfile.TemporaryDirectory() as td:
        cd = _campaign(Path(td), "done-2026q1", phase5=True, rollout_doc=True)
        check("no gap To Do once phase-5-rollout.md exists",
              not any(a.get("id") == "phase5-author" for a in oa.scan_campaign(cd)))


def test_gap_absent_without_phase5() -> None:
    """A campaign with no Phase 5 isn't a launch-type campaign — nothing to advance into."""
    with tempfile.TemporaryDirectory() as td:
        cd = _campaign(Path(td), "nolaunch-2026q1", phase5=False, rollout_doc=False)
        check("no gap To Do on a campaign with no Phase 5",
              not any(a.get("id") == "phase5-author" for a in oa.scan_campaign(cd)))


def test_phase_cost_derives_when_blank() -> None:
    """SYS-151 — the AI-cost cell was read VERBATIM from campaign.yaml, so the live ledger
    derivation only fired when someone had typed the literal marker "<!-- PHASE_COST:N -->" into
    that field. Auto-costing was OPT-IN via a magic string: omit it and the cell rendered a dash,
    silently, while the ledger held correctly phased entries. Recurring operator complaint. Human
    time already worked the other way round, so one table had two cells behaving differently."""
    cell = "~$9.99 · ~1.2M tok"
    real = oa.ledger_phase_cost
    oa.ledger_phase_cost = lambda *_a, **_k: cell
    try:
        cd = Path("does-not-matter")
        for label, ph in (
            ("key absent", {"id": 4}),
            ("empty string", {"id": 4, "ai_cost": ""}),
            ("em dash", {"id": 4, "ai_cost": "—"}),
            ("tbd", {"id": 4, "ai_cost": "TBD"}),
            ("the old opt-in marker", {"id": 4, "ai_cost": "<!-- PHASE_COST:4 -->"}),
        ):
            got = oa._phase_ai_cost_cell(ph, cd)
            check(f"a blank ai_cost derives from the ledger ({label})", got == cell, f"got {got!r}")
        check("a deliberate prose value is left alone",
              oa._phase_ai_cost_cell({"id": 4, "ai_cost": "~$0 · operator-run"}, cd)
              == "~$0 · operator-run")
        oa.ledger_phase_cost = lambda *_a, **_k: ""
        check("a phase with nothing in the ledger still renders a dash",
              oa._phase_ai_cost_cell({"id": 9}, cd) == "—")
    finally:
        oa.ledger_phase_cost = real


def test_hand_typed_cost_warns() -> None:
    """The twin failure mode, and the worse one: ai_cost accepts free text, so authors hand-type
    figures. acme-workforce-report-2026 carried "~$1.33 - ~222k tok (CD trio, metered
    2026-06-18)" — frozen at its June value and LOOKING correct, which is worse than a blank.
    The campaign-manager skill already forbids a typed number; nothing enforced it."""
    warn = oa._phase_cost_warning({"id": 2,
                                   "ai_cost": "~$1.33 - ~222k tok (CD trio, metered 2026-06-18)"})
    check("a hand-typed cost figure warns", bool(warn) and "hand-typed" in warn, f"got {warn!r}")
    check("the warning names the phase", bool(warn) and "phase 2" in warn, f"got {warn!r}")
    for label, val in (("a marker", "<!-- PHASE_COST:2 -->"), ("prose", "operator-run"),
                       ("a blank", ""), ("a dash", "\u2014")):
        check(f"no warning for {label}", oa._phase_cost_warning({"id": 2, "ai_cost": val}) is None)


def main() -> int:
    print("operator_actions regression tests")
    test_no_reentrant_scan()
    test_gap_suppressed_once_rollout_authored()
    test_gap_absent_without_phase5()
    test_phase_cost_derives_when_blank()
    test_hand_typed_cost_warns()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll operator_actions tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
