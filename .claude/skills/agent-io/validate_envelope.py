#!/usr/bin/env python3
"""
Agent I/O contract validator (SYS-004) — validates a return envelope (and optionally
the dispatch it answers) per docs/specs/agent-io-contract.md §5.

ADDITIVE / NON-BREAKING (spec §6 Step 2-3): the agents still emit their existing prose
returns; this checks the structured `return:` envelope that now rides ALONGSIDE the prose.
Nothing here parses or retires prose — that's the spec's future gated Step 4.

What it checks (§5):
  1. dispatch_id present (and matches the dispatch's id, when a dispatch is given).
  2. status present and in {delivered, blocked, needs-rescope, refused}.
  3. On status: delivered — the per-agent required fields from the §4 table:
       - producer    -> artifacts (>=1 ship:true) + self_qa.copy + self_qa.visual
                        + self_qa.content_subedit (every copy asset)
       - governance  -> gate.verdict in {clear, clear-with-disclaimers, hold, block}
                        + gate.audit_ref
       - brand       -> gate.verdict in {pass, pass-with-notes, send-back, kill}
                        + gate.audit_ref
       - creative-director / insights / forensic -> artifacts
  4. On delivered with artifacts — every ship:true artifact path EXISTS on disk
     (resolved relative to --asset-dir, else the dispatch/return's own dir). This
     reuses the SYS-003 / gallery-qa ship-file-existence discipline.
  5. Gate agents: a verdict is always required on delivered (never inferred from prose).

A non-delivered status (blocked / needs-rescope / refused) only needs dispatch_id +
status + a `notes` explaining why — the delivered-state fields are not required.

Output: a GREEN/RED report naming the specific gaps. Exit 0 = valid, non-zero = invalid,
so CM / a smoke test / a hook can gate on it.

Usage:
  python validate_envelope.py --return <file.yaml> [--dispatch <file.yaml>] [--asset-dir <dir>]
  python validate_envelope.py --selftest        # built-in good + bad fixtures; no live data

The envelope file may be either a bare YAML mapping with a top-level `return:` / `dispatch:`
key (as the agents emit it) OR the inner mapping directly — both are accepted.
"""
from __future__ import annotations
import argparse
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("RED: pyyaml required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

# --- per-agent profiles (mirrors agent-io-contract.md §4 table) ---------------
# Agent aliases -> canonical key. Accepts the dispatch vocabulary (§3) AND the
# agent-dir / self-declared `agent:` names, so a return that says
# "agent: governance-manager" validates the same as "agent: governance".
AGENT_ALIASES = {
    "producer": "producer",
    "governance": "governance",
    "governance-manager": "governance",
    "brand": "brand",
    "brand-manager": "brand",
    "creative-director": "creative-director",
    "cd": "creative-director",
    "insights": "insights",
    "insights-manager": "insights",
    "forensic": "forensic",
    "marketing-forensic-analyst": "forensic",
}

GATE_AGENTS = {"governance", "brand"}
GOVERNANCE_VERDICTS = {"clear", "clear-with-disclaimers", "hold", "block"}
BRAND_VERDICTS = {"pass", "pass-with-notes", "send-back", "kill"}
ARTIFACT_AGENTS = {"producer", "creative-director", "insights", "forensic"}

VALID_STATUSES = {"delivered", "blocked", "needs-rescope", "refused"}


def canonical_agent(raw: str | None) -> str | None:
    if not raw:
        return None
    return AGENT_ALIASES.get(str(raw).strip().lower())


def load_envelope(path: Path, kind: str) -> dict:
    """Load a YAML file and return the inner mapping.

    `kind` is "return" or "dispatch". Accepts either a top-level wrapper
    ({return: {...}} / {dispatch: {...}}) or the bare inner mapping.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: not a YAML mapping")
    if kind in data and isinstance(data[kind], dict):
        return data[kind]
    return data


def _get(d: dict, *keys):
    """Nested get: _get(d, 'self_qa', 'copy') -> d['self_qa']['copy'] or None."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def validate(ret: dict, dispatch: dict | None, asset_dir: Path | None,
             base_dir: Path) -> list[str]:
    """Return a list of failure strings (empty == valid). base_dir is where
    ship:true paths resolve when no --asset-dir is given."""
    fails: list[str] = []

    # --- 1. dispatch_id ---------------------------------------------------
    dispatch_id = ret.get("dispatch_id")
    if not dispatch_id:
        fails.append("dispatch_id: missing (required — pairs the return with its dispatch)")
    elif dispatch is not None:
        d_id = dispatch.get("id")
        if d_id and d_id != dispatch_id:
            fails.append(
                f"dispatch_id: '{dispatch_id}' does not match dispatch.id '{d_id}'")

    # --- 2. status --------------------------------------------------------
    status = ret.get("status")
    if not status:
        fails.append("status: missing (required)")
    elif status not in VALID_STATUSES:
        fails.append(
            f"status: '{status}' not in {{{', '.join(sorted(VALID_STATUSES))}}}")

    agent = canonical_agent(ret.get("agent") or (dispatch or {}).get("agent"))
    if ret.get("agent") and agent is None:
        fails.append(f"agent: '{ret.get('agent')}' is not a recognised agent")

    # Non-delivered states only need a `notes` explaining why (§4 last line).
    if status in {"blocked", "needs-rescope", "refused"}:
        if not str(ret.get("notes") or "").strip():
            fails.append(f"status '{status}' requires a `notes` explaining why")
        return fails  # delivered-state fields are not required

    if status != "delivered":
        return fails  # nothing more to check on missing/invalid status

    # --- 3. per-agent required fields on `delivered` ----------------------
    if agent is None:
        fails.append("agent: missing/unknown — cannot apply per-agent required fields")
        return fails

    artifacts = ret.get("artifacts")

    if agent in GATE_AGENTS:
        verdict = _get(ret, "gate", "verdict")
        verdict_set = GOVERNANCE_VERDICTS if agent == "governance" else BRAND_VERDICTS
        if not verdict:
            fails.append(f"{agent}: gate.verdict missing (gate agents MUST return an explicit verdict)")
        elif str(verdict).strip().lower() not in verdict_set:
            fails.append(
                f"{agent}: gate.verdict '{verdict}' not in {{{', '.join(sorted(verdict_set))}}}")
        if not _get(ret, "gate", "audit_ref"):
            fails.append(f"{agent}: gate.audit_ref missing (path to the audit block required)")

    if agent in ARTIFACT_AGENTS:
        if not isinstance(artifacts, list) or not artifacts:
            fails.append(f"{agent}: artifacts missing or empty (>=1 required on delivered)")
        elif agent == "producer":
            shipped = [a for a in artifacts if isinstance(a, dict) and a.get("ship") is True]
            if not shipped:
                fails.append("producer: no artifact has ship: true (>=1 ship:true required)")
            # Producer self-QA required fields
            if _get(ret, "self_qa", "copy") is None:
                fails.append("producer: self_qa.copy missing")
            if _get(ret, "self_qa", "visual") is None:
                fails.append("producer: self_qa.visual missing")
            if _get(ret, "self_qa", "content_subedit") is None:
                fails.append("producer: self_qa.content_subedit missing (mandatory on every copy asset)")

    # --- 4. ship:true artifacts must exist on disk ------------------------
    if isinstance(artifacts, list):
        resolve_dir = asset_dir or base_dir
        for a in artifacts:
            if not isinstance(a, dict) or a.get("ship") is not True:
                continue
            rel = a.get("path")
            if not rel:
                fails.append("artifact with ship: true has no `path`")
                continue
            p = (resolve_dir / rel)
            if not p.exists():
                fails.append(
                    f"ship:true artifact does not exist on disk: '{rel}' "
                    f"(resolved under {resolve_dir})")

    return fails


def report(label: str, fails: list[str]) -> int:
    print(f"=== AGENT I/O ENVELOPE VALIDATION — {label} ===")
    if not fails:
        print("RESULT: GREEN — envelope satisfies the agent-io contract (§5).")
        return 0
    print(f"RESULT: RED — {len(fails)} gap(s):")
    for f in fails:
        print(f"  x {f}")
    return 1


# --- selftest ----------------------------------------------------------------
def _selftest() -> int:
    """Run built-in good + bad fixtures against the validator. No live data — every
    ship:true path is created in a temp dir so the existence check has something real
    to resolve. Returns 0 only if every fixture's expected verdict is met."""
    print("=== AGENT I/O VALIDATOR SELFTEST ===\n")
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        # create the files the GOOD producer fixture claims to ship
        (base / "wk0-anchor-post.md").write_text("# asset", encoding="utf-8")
        (base / "wk0-anchor-post.png").write_bytes(b"\x89PNG")
        (base / "audit.md").write_text("# audit", encoding="utf-8")

        good_dispatch = {"id": "soundtrak-c1/wk0-anchor-post/producer/1", "agent": "producer"}

        fixtures: list[tuple[str, dict, dict | None, bool]] = [
            # (name, return-envelope, dispatch-or-None, expect_valid)
            ("GOOD producer (delivered, ship file exists, full self_qa)", {
                "dispatch_id": "soundtrak-c1/wk0-anchor-post/producer/1",
                "agent": "producer", "status": "delivered",
                "artifacts": [
                    {"path": "wk0-anchor-post.md", "type": "Instance", "ship": True, "role": "primary_doc"},
                    {"path": "wk0-anchor-post.png", "type": "Instance", "ship": True},
                ],
                "self_qa": {
                    "copy": {"ran": True, "pass": True},
                    "visual": {"ran": True, "pass": True},
                    "content_subedit": {"ran": True, "violations": 0},
                },
            }, good_dispatch, True),

            ("GOOD governance (delivered, verdict + audit_ref)", {
                "dispatch_id": "soundtrak-c1/wk0-anchor-post/governance/1",
                "agent": "governance-manager", "status": "delivered",
                "gate": {"verdict": "clear-with-disclaimers", "audit_ref": "asset.yaml#compliance"},
            }, None, True),

            ("GOOD brand (delivered, verdict + audit_ref)", {
                "dispatch_id": "soundtrak-c1/wk0-anchor-post/brand/1",
                "agent": "brand", "status": "delivered",
                "gate": {"verdict": "pass-with-notes", "audit_ref": "asset.md#brand-verdict"},
            }, None, True),

            ("GOOD insights (delivered, artifacts)", {
                "dispatch_id": "soundtrak-c1/insights/1",
                "agent": "insights", "status": "delivered",
                "artifacts": [{"path": "audit.md", "type": "Foundation", "ship": False}],
            }, None, True),

            ("GOOD blocked (notes given, no delivered fields)", {
                "dispatch_id": "soundtrak-c1/wk0/producer/2",
                "agent": "producer", "status": "blocked",
                "notes": "self-QA failed 3 cycles on L2 voice; rescope recommended",
            }, None, True),

            # --- BAD fixtures ---
            ("BAD missing dispatch_id", {
                "agent": "producer", "status": "delivered",
                "artifacts": [{"path": "wk0-anchor-post.md", "ship": True}],
                "self_qa": {"copy": {}, "visual": {}, "content_subedit": {}},
            }, None, False),

            ("BAD invalid status", {
                "dispatch_id": "x/1", "agent": "producer", "status": "done",
            }, None, False),

            ("BAD producer missing content_subedit", {
                "dispatch_id": "x/2", "agent": "producer", "status": "delivered",
                "artifacts": [{"path": "wk0-anchor-post.md", "ship": True}],
                "self_qa": {"copy": {}, "visual": {}},
            }, None, False),

            ("BAD producer ship:true file does not exist", {
                "dispatch_id": "x/3", "agent": "producer", "status": "delivered",
                "artifacts": [{"path": "ghost-file-that-isnt-there.md", "ship": True}],
                "self_qa": {"copy": {}, "visual": {}, "content_subedit": {}},
            }, None, False),

            ("BAD governance missing verdict", {
                "dispatch_id": "x/4", "agent": "governance", "status": "delivered",
                "gate": {"audit_ref": "asset.yaml#compliance"},
            }, None, False),

            ("BAD brand verdict not in set", {
                "dispatch_id": "x/5", "agent": "brand", "status": "delivered",
                "gate": {"verdict": "approved", "audit_ref": "x"},
            }, None, False),

            ("BAD dispatch_id mismatch vs dispatch", {
                "dispatch_id": "wrong/id", "agent": "producer", "status": "delivered",
                "artifacts": [{"path": "wk0-anchor-post.md", "ship": True}],
                "self_qa": {"copy": {}, "visual": {}, "content_subedit": {}},
            }, good_dispatch, False),

            ("BAD blocked without notes", {
                "dispatch_id": "x/6", "agent": "producer", "status": "blocked",
            }, None, False),
        ]

        all_ok = True
        for name, ret, disp, expect_valid in fixtures:
            fails = validate(ret, disp, None, base)
            is_valid = not fails
            ok = (is_valid == expect_valid)
            all_ok &= ok
            verdict = "GREEN" if is_valid else "RED"
            want = "GREEN" if expect_valid else "RED"
            mark = "ok " if ok else "FAIL"
            print(f"  [{mark}] {name}")
            print(f"         got {verdict}, expected {want}"
                  + (f" :: {fails[0]}" if fails else ""))
        print()
        if all_ok:
            print(f"RESULT: GREEN — all {len(fixtures)} fixtures behaved as expected.")
            return 0
        print("RESULT: RED — one or more fixtures did not match expectation.")
        return 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="Validate an agent-io return envelope (SYS-004).")
    p.add_argument("--return", dest="return_file", help="path to the return envelope YAML")
    p.add_argument("--dispatch", dest="dispatch_file", default=None,
                   help="optional matching dispatch envelope YAML")
    p.add_argument("--asset-dir", dest="asset_dir", default=None,
                   help="dir to resolve ship:true artifact paths against "
                        "(default: the return file's own dir)")
    p.add_argument("--selftest", action="store_true",
                   help="run built-in good + bad fixtures (no live data) and exit")
    args = p.parse_args()

    if args.selftest:
        return _selftest()

    if not args.return_file:
        p.error("--return is required (or use --selftest)")

    return_path = Path(args.return_file).resolve()
    if not return_path.exists():
        print(f"RED: return file not found: {return_path}", file=sys.stderr)
        return 2
    try:
        ret = load_envelope(return_path, "return")
    except Exception as e:  # noqa: BLE001
        print(f"RED: cannot load return envelope: {e}", file=sys.stderr)
        return 2

    dispatch = None
    if args.dispatch_file:
        dp = Path(args.dispatch_file).resolve()
        if not dp.exists():
            print(f"RED: dispatch file not found: {dp}", file=sys.stderr)
            return 2
        try:
            dispatch = load_envelope(dp, "dispatch")
        except Exception as e:  # noqa: BLE001
            print(f"RED: cannot load dispatch envelope: {e}", file=sys.stderr)
            return 2

    asset_dir = Path(args.asset_dir).resolve() if args.asset_dir else None
    base_dir = return_path.parent
    fails = validate(ret, dispatch, asset_dir, base_dir)
    return report(return_path.name, fails)


if __name__ == "__main__":
    sys.exit(main())
