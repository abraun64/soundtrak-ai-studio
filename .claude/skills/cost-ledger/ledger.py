#!/usr/bin/env python3
"""
Per-dispatch AI cost ledger — the metered answer to "the dashboard totals went stale".

Ledger file: .claude/state/cost-ledger.jsonl — append-only, one JSON object per line:
  {ts, campaign, phase, asset, agent, tokens, cost_usd, basis, note}
    basis: "metered"  — token count came from a real usage report (subagent return,
                        console billing, /cost output)
           "estimate" — operator/CM judgment call; reported separately, never
                        silently blended with metered numbers

Rates: blended $/Mtok (input+output combined). Default 6.0 — derived from the one
fully-metered baseline we have (Soundtrak strategy phases: 710k tok = $4.30 ≈ $6.06/M).
Override per-call with --rate or per-entry with --cost.

Usage:
  # CM appends after EVERY subagent return that reports usage (same turn, no exceptions)
  python .claude/skills/cost-ledger/ledger.py add --campaign <slug> --asset 23 \
      --agent producer --tokens 130659 --note "Phase 4 Remotion build"

  # Report (metered vs estimated split, per phase + per asset)
  python .claude/skills/cost-ledger/ledger.py report --campaign <slug>

  # Push aggregated numbers into campaign.yaml phase ai_cost fields
  python .claude/skills/cost-ledger/ledger.py write-yaml --campaign <slug>

The dashboard total line is injected at render time from this ledger via the
<!-- COST_TOTAL_AUTO --> marker (see render-html/operator_actions.py) — it can
no longer go stale because nobody hand-maintains it.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / ".claude" / "state" / "cost-ledger.jsonl"
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
import tenant_paths as _tp  # noqa: E402  — W4 dual-path: resolve campaign in either layout
DEFAULT_RATE_PER_MTOK = 6.0


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
    cost = args.cost if args.cost is not None else round(args.tokens / 1_000_000 * args.rate, 2)
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "campaign": args.campaign,
        "phase": args.phase,
        "asset": args.asset or "",
        "agent": args.agent,
        "tokens": args.tokens,
        "cost_usd": cost,
        "basis": args.basis,
        "note": args.note or "",
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"ledger += {args.campaign} / asset {args.asset or '-'} / {args.agent}: "
          f"{args.tokens:,} tok = ${cost:.2f} ({args.basis})")
    return 0


def summarise(entries: list[dict]) -> dict:
    s = {
        "metered_tokens": 0, "metered_cost": 0.0,
        "est_tokens": 0, "est_cost": 0.0,
        "by_phase": defaultdict(lambda: {"tokens": 0, "cost": 0.0}),
        "by_asset": defaultdict(lambda: {"tokens": 0, "cost": 0.0}),
        "n": len(entries),
    }
    for e in entries:
        tok = int(e.get("tokens") or 0)
        cost = float(e.get("cost_usd") or 0.0)
        if e.get("basis") == "estimate":
            s["est_tokens"] += tok
            s["est_cost"] += cost
        else:
            s["metered_tokens"] += tok
            s["metered_cost"] += cost
        s["by_phase"][str(e.get("phase") or "?")]["tokens"] += tok
        s["by_phase"][str(e.get("phase") or "?")]["cost"] += cost
        if e.get("asset"):
            s["by_asset"][str(e["asset"])]["tokens"] += tok
            s["by_asset"][str(e["asset"])]["cost"] += cost
    return s


def fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    return f"{n/1000:.0f}k"


def total_line(campaign: str) -> str:
    """The dashboard <small> line — rendered at HTML-build time via COST_TOTAL_AUTO."""
    entries = read_entries(campaign)
    if not entries:
        return ("<small>**AI cost to date**: no ledger entries yet — "
                "CM appends one per dispatch via cost-ledger skill.</small>")
    s = summarise(entries)
    total_cost = s["metered_cost"] + s["est_cost"]
    total_tok = s["metered_tokens"] + s["est_tokens"]
    parts = [f"${s['metered_cost']:.2f} · {fmt_tok(s['metered_tokens'])} tok metered"]
    if s["est_tokens"]:
        parts.append(f"${s['est_cost']:.2f} · {fmt_tok(s['est_tokens'])} tok estimated")
    stamp = datetime.now().strftime("%Y-%m-%d")
    return (f"<small>**AI cost to date (ledger, auto-rendered {stamp})**: "
            f"{' + '.join(parts)} = ~${total_cost:.2f} · ~{fmt_tok(total_tok)} tok "
            f"across {s['n']} ledger entries. Source: `.claude/state/cost-ledger.jsonl` — "
            f"run `ledger.py report --campaign {campaign}` for the per-asset split.</small>")


def phase_cost_cell(campaign: str, phase) -> str:
    """Short per-phase AI-cost cell for a dashboard phases table — rendered fresh
    at build time from the ledger via the <!-- PHASE_COST:N --> marker so it can
    never go stale (mirrors total_line for the total row). Answers "where was the
    spend, by phase?" directly in the table instead of a blank or 'metered per asset'."""
    ph = str(phase)
    ents = [e for e in read_entries(campaign) if str(e.get("phase") or "") == ph]
    if not ents:
        return "—"
    met_c = sum(float(e.get("cost_usd") or 0.0) for e in ents if e.get("basis") != "estimate")
    met_t = sum(int(e.get("tokens") or 0) for e in ents if e.get("basis") != "estimate")
    est_c = sum(float(e.get("cost_usd") or 0.0) for e in ents if e.get("basis") == "estimate")
    est_t = sum(int(e.get("tokens") or 0) for e in ents if e.get("basis") == "estimate")
    tot_c, tot_t = met_c + est_c, met_t + est_t
    if est_t and not met_t:
        return f"~${tot_c:.2f} est. · ~{fmt_tok(tot_t)} tok"
    if met_t and not est_t:
        return f"~${tot_c:.2f} · ~{fmt_tok(tot_t)} tok"
    return f"~${tot_c:.2f} · ~{fmt_tok(tot_t)} tok (${met_c:.2f} metered + ${est_c:.2f} est.)"


def cmd_report(args) -> int:
    entries = read_entries(args.campaign)
    if not entries:
        print(f"(no ledger entries for {args.campaign or 'any campaign'})")
        return 0
    s = summarise(entries)
    scope = args.campaign or "ALL CAMPAIGNS"
    print(f"\n=== cost ledger — {scope} — {s['n']} entries ===\n")
    print(f"METERED : ${s['metered_cost']:.2f}  ({s['metered_tokens']:,} tok)")
    print(f"ESTIMATE: ${s['est_cost']:.2f}  ({s['est_tokens']:,} tok)")
    print(f"TOTAL   : ${s['metered_cost'] + s['est_cost']:.2f}  ({s['metered_tokens'] + s['est_tokens']:,} tok)")
    print("\n-- by phase --")
    for ph in sorted(s["by_phase"]):
        v = s["by_phase"][ph]
        print(f"  phase {ph}: ${v['cost']:.2f} · {v['tokens']:,} tok")
    if s["by_asset"]:
        print("\n-- by asset --")
        for a in sorted(s["by_asset"], key=lambda x: (len(x), x)):
            v = s["by_asset"][a]
            print(f"  #{a}: ${v['cost']:.2f} · {v['tokens']:,} tok")
    print()
    return 0


def cmd_write_yaml(args) -> int:
    """Update campaign.yaml ai_cost per phase from ledger aggregates."""
    _camp = _tp.find_campaign_dir(ROOT, args.campaign)
    yaml_path = (_camp / "campaign.yaml") if _camp else (ROOT / "campaigns" / args.campaign / "campaign.yaml")
    if not yaml_path.exists():
        print(f"ERROR: {yaml_path} not found", file=sys.stderr)
        return 1
    entries = read_entries(args.campaign)
    if not entries:
        print("(no ledger entries — nothing to write)")
        return 0
    s = summarise(entries)
    text = yaml_path.read_text(encoding="utf-8")
    stamp = datetime.now().strftime("%Y-%m-%d")
    changed = []
    for ph, v in s["by_phase"].items():
        if not ph.isdigit():
            continue
        new_cost = f'ai_cost: "~${v["cost"]:.2f} · ~{fmt_tok(v["tokens"])} tok (ledger {stamp})"'
        # Replace the ai_cost line inside the matching `- id: <ph>` block
        pat = re.compile(
            rf'(- id: {ph}\n(?:.*\n)*?\s*)ai_cost: "[^"]*"', re.MULTILINE)
        new_text, n = pat.subn(rf'\g<1>{new_cost}', text, count=1)
        if n:
            text = new_text
            changed.append(ph)
    if changed:
        yaml_path.write_text(text, encoding="utf-8")
        print(f"campaign.yaml updated for phase(s) {', '.join(sorted(changed))} — re-render the dashboard to surface.")
    else:
        print("(no matching ai_cost lines found to update)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append one dispatch entry")
    a.add_argument("--campaign", required=True)
    a.add_argument("--phase", default="4")
    a.add_argument("--asset", default="")
    a.add_argument("--agent", required=True, help="producer / brand-manager / cd / research / main-loop / ...")
    a.add_argument("--tokens", type=int, required=True)
    a.add_argument("--cost", type=float, default=None, help="explicit $ (else tokens × rate)")
    a.add_argument("--rate", type=float, default=DEFAULT_RATE_PER_MTOK, help="blended $/Mtok (default 6.0)")
    a.add_argument("--basis", choices=["metered", "estimate"], default="metered")
    a.add_argument("--note", default="")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("report", help="aggregate report")
    r.add_argument("--campaign", default=None)
    r.set_defaults(func=cmd_report)

    w = sub.add_parser("write-yaml", help="push aggregates into campaign.yaml ai_cost fields")
    w.add_argument("--campaign", required=True)
    w.set_defaults(func=cmd_write_yaml)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
