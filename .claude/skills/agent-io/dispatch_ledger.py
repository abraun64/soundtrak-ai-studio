#!/usr/bin/env python3
"""
Dispatch ledger (SYS-004) — the auditable record of every dispatch↔return pair.

Mirrors the cost-ledger pattern: append-only, one JSON object per line in
.claude/state/dispatch-ledger.jsonl. CM appends one entry per agent return (SAME turn),
after running validate_envelope.py, so the orchestration boundary is auditable — which
agent was dispatched for which asset, what status came back, and whether the structured
envelope validated GREEN or RED.

ADDITIVE / NON-BREAKING (agent-io-contract.md §6 Steps 2-3): this records the handoff; it
does not replace prose-parsing (that's the future gated Step 4).

Each entry: {ts, campaign, asset, agent, dispatch_id, status, verdict, note}
  status  — the return envelope's status: delivered | blocked | needs-rescope | refused | (missing)
  verdict — the validator's result for this return: "ok" (GREEN) | "RED" | "no-envelope"

Usage:
  # CM appends after EVERY return (same turn as validate_envelope)
  python .claude/skills/agent-io/dispatch_ledger.py add \
      --campaign <slug> --asset <NN> --agent producer \
      --dispatch-id <id> --status delivered --verdict ok --note "wk0 anchor post"

  # Report — pairs per campaign, with the RED / no-envelope tally surfaced
  python .claude/skills/agent-io/dispatch_ledger.py report --campaign <slug>
  python .claude/skills/agent-io/dispatch_ledger.py report            # all campaigns
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / ".claude" / "state" / "dispatch-ledger.jsonl"

VALID_STATUSES = {"delivered", "blocked", "needs-rescope", "refused", "missing"}
VALID_VERDICTS = {"ok", "RED", "no-envelope"}


def read_entries(campaign: str | None = None) -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if campaign and e.get("campaign") != campaign:
            continue
        out.append(e)
    return out


def cmd_add(args) -> int:
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "campaign": args.campaign,
        "asset": args.asset or "",
        "agent": args.agent,
        "dispatch_id": args.dispatch_id or "",
        "status": args.status,
        "verdict": args.verdict,
        "note": args.note or "",
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"dispatch-ledger += {args.campaign} / asset {args.asset or '-'} / {args.agent}: "
          f"status={args.status} verdict={args.verdict} (id={args.dispatch_id or '-'})")
    return 0


def cmd_report(args) -> int:
    entries = read_entries(args.campaign)
    scope = args.campaign or "ALL CAMPAIGNS"
    if not entries:
        print(f"(no dispatch-ledger entries for {scope})")
        return 0
    by_agent: dict[str, int] = defaultdict(int)
    by_status: dict[str, int] = defaultdict(int)
    red = no_env = 0
    for e in entries:
        by_agent[e.get("agent") or "?"] += 1
        by_status[e.get("status") or "?"] += 1
        if e.get("verdict") == "RED":
            red += 1
        elif e.get("verdict") == "no-envelope":
            no_env += 1
    print(f"\n=== dispatch ledger — {scope} — {len(entries)} pair(s) ===\n")
    print("-- by agent --")
    for a in sorted(by_agent):
        print(f"  {a}: {by_agent[a]}")
    print("\n-- by return status --")
    for s in sorted(by_status):
        print(f"  {s}: {by_status[s]}")
    print(f"\nvalidator: {red} RED · {no_env} no-envelope (prose-only) · "
          f"{len(entries) - red - no_env} GREEN")
    print(f"\nSource: {LEDGER}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append one dispatch↔return pair")
    a.add_argument("--campaign", required=True)
    a.add_argument("--asset", default="")
    a.add_argument("--agent", required=True)
    a.add_argument("--dispatch-id", default="")
    a.add_argument("--status", choices=sorted(VALID_STATUSES), default="delivered")
    a.add_argument("--verdict", choices=sorted(VALID_VERDICTS), default="ok",
                   help="validator result: ok (GREEN) / RED / no-envelope (prose-only)")
    a.add_argument("--note", default="")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("report", help="aggregate report")
    r.add_argument("--campaign", default=None)
    r.set_defaults(func=cmd_report)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
