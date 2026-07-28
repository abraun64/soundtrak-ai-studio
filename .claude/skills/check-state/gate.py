#!/usr/bin/env python3
"""
Drift gate (ratchet) — wraps check.py's drift detection with a baseline so the
system reports only NEW drift (a regression beyond the accepted backlog), while
the existing/known backlog stays grandfathered.

LOUD, NON-BLOCKING by design:
  - exit 1 when NEW drift is introduced (so smoke-test / the Stop hook surface it)
  - exit 0 when no new drift (even if the known backlog is non-empty)

It does NOT modify check.py — it imports check.py's check_* functions, so the
detection logic stays identical to the human-readable report. The only thing this
adds is "new vs known", which turns check.py's 34-line dump into one actionable
signal: did THIS change introduce drift?

Usage:
  python gate.py --all-campaigns                    # report new vs baseline
  python gate.py --campaign <slug>                  # one campaign
  python gate.py --all-campaigns --write-baseline   # accept current state as known
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # the existing checker — REUSED, never modified

# Windows cp1252 console can't print emoji — force UTF-8 + replace fallback.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = check.REPO_ROOT
BASELINE_PATH = REPO_ROOT / ".claude" / "state" / "drift-baseline.json"

# W4 dual-path: also discover business-rooted tenants' campaigns (additive; [] until one exists)
sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
import tenant_paths as _tp  # noqa: E402


def _asset_folders(campaign_dir: Path):
    assets_dir = campaign_dir / "assets"
    if not assets_dir.is_dir():
        return []
    return sorted(p for p in assets_dir.iterdir() if p.is_dir() and re.match(r"^\d+-", p.name))


def collect_issues(campaign_dir: Path) -> set[str]:
    """Stable issue keys for one campaign — mirrors check.report_campaign's
    collection, silently. Key shape: <campaign>::<layer>::<detail>."""
    slug = campaign_dir.name
    keys: set[str] = set()
    folders = _asset_folders(campaign_dir)
    if not folders:
        return keys
    results = []
    for af in folders:
        r = check.check_asset(af)
        results.append(r)
        if r["drift"]:
            keys.add(f"{slug}::status::{af.name}::{' · '.join(r['drift'])}")
    for line in check.check_dashboard_drift(campaign_dir, results):
        keys.add(f"{slug}::dashboard::{line.strip()}")
    for line in check.check_plan_roster_drift(campaign_dir, folders):
        keys.add(f"{slug}::plan::{line.strip()}")
    for line in check.check_campaign_yaml_drift(campaign_dir, folders):
        keys.add(f"{slug}::campaign_yaml::{line.strip()}")
    for line in check.check_ships_drift(campaign_dir, folders):
        keys.add(f"{slug}::ships::{line.strip()}")
    for line in check.check_board_currency(campaign_dir):
        keys.add(f"{slug}::board::{line.strip()}")
    return keys


def collect_all(campaigns) -> set[str]:
    out: set[str] = set()
    for c in campaigns:
        out |= collect_issues(c)
    return out


def load_baseline() -> set[str]:
    try:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        return set(data.get("issues", []))
    except (OSError, json.JSONDecodeError):
        return set()


def write_baseline(issues: set[str]) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps({"generated": date.today().isoformat(), "issues": sorted(issues)}, indent=2),
        encoding="utf-8",
    )


def _all_campaign_dirs():
    """Flat campaigns/<slug>/ + business-rooted <Tenant>/campaigns/<slug>/ (latter [] today)."""
    root = REPO_ROOT / "campaigns"
    flat = [p for p in root.iterdir() if p.is_dir() and (p / "assets").is_dir()] if root.is_dir() else []
    br = [c for c in _tp.business_rooted_campaign_dirs(REPO_ROOT) if (c / "assets").is_dir()]
    return sorted(flat + br, key=lambda p: p.name)


def resolve_campaigns(args):
    if args.all_campaigns:
        return _all_campaign_dirs()
    if args.campaign:
        match = [c for c in _all_campaign_dirs() if c.name == args.campaign]
        return match or [REPO_ROOT / "campaigns" / args.campaign]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", help="Campaign slug")
    ap.add_argument("--all-campaigns", action="store_true", help="Scan every campaign")
    ap.add_argument("--write-baseline", action="store_true", help="Accept current drift as the known baseline")
    args = ap.parse_args()

    campaigns = resolve_campaigns(args)
    if campaigns is None:
        ap.error("specify --campaign <slug> or --all-campaigns")

    current = collect_all(campaigns)

    scoped = {c.name for c in campaigns}

    if args.write_baseline:
        # Merge: keep other campaigns' baseline, replace only the in-scope portion —
        # so `--campaign X --write-baseline` can't wipe the rest of the baseline.
        kept = {k for k in load_baseline() if k.split("::", 1)[0] not in scoped}
        merged = kept | current
        write_baseline(merged)
        print(
            f"baseline written: {len(current)} issue(s) across {len(campaigns)} campaign(s); "
            f"{len(merged)} total known -> {BASELINE_PATH.relative_to(REPO_ROOT)}"
        )
        return 0

    # Compare only against the in-scope campaigns' slice of the baseline, so a
    # single-campaign run doesn't report other campaigns' backlog as "resolved".
    baseline = {k for k in load_baseline() if k.split("::", 1)[0] in scoped}
    new = sorted(current - baseline)
    resolved = sorted(baseline - current)

    print(
        f"drift gate: {len(current)} total · {len(current & baseline)} known (baselined) · "
        f"{len(new)} NEW · {len(resolved)} resolved"
    )
    if resolved:
        print(f"  {len(resolved)} known issue(s) resolved since baseline (run --write-baseline to ratchet down)")
    if new:
        print(f"  WARNING: {len(new)} NEW drift issue(s) introduced (not in baseline):")
        for k in new:
            print(f"     - {k}")
        print("  Fix it, or if intentional run: python .claude/skills/check-state/gate.py --all-campaigns --write-baseline")
        return 1
    print("  OK — no new drift.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
