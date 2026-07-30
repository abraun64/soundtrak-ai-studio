#!/usr/bin/env python3
"""Phase-0 gate (Retro-5) - mechanical check that a tenant's baseline is established
BEFORE a campaign (Phase 1) may start.

Why this exists: the CM skill already *says* "no baseline -> run Phase 0 first", but
that's prose an agent is trusted to follow. This makes the check deterministic, which
matters most for the Seed's solo non-expert operator. CM runs it before Phase 1; the
install doctor surfaces it too.

Threshold (v1) - BLOCK unless ALL of:
  - tenant-brand/<tenant>.yaml exists and parses
  - its `brand_context` baseline entry is status: present AND the referenced file exists
  - its `integrations`  baseline entry is status: present AND the referenced file exists
WARN (non-blocking): compliance / segments / market / playbook not yet present.
(Per-asset compliance is enforced later by the Governance Manager at Phase 4b.)

Keys off the existing `baseline:` status convention (present | planned) from
docs/specs/phase-0-tenant-baseline.md - `present` already means "built + established".

Usage:
  python .claude/lib/phase0_gate.py --tenant acme-co
  python .claude/lib/phase0_gate.py --tenant <slug> --root /path/to/checkout
Exit 0 = campaigns may start; exit 1 = blocked (Phase 0 incomplete).
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[2]  # .claude/lib/ -> checkout root

REQUIRED = ("brand_context", "integrations")
RECOMMENDED = ("compliance", "segments", "market", "playbook")


def check_baseline(root: Path, tenant: str) -> dict:
    """Return {ok, tenant, blocking:[...], warnings:[...]}."""
    tb = root / "tenant-brand"
    yml = tb / f"{tenant}.yaml"
    if not yml.exists():
        return {"ok": False, "tenant": tenant, "warnings": [],
                "blocking": [f"no tenant baseline - tenant-brand/{tenant}.yaml missing. Run Phase 0 first."]}
    if yaml is None:
        return {"ok": False, "tenant": tenant, "warnings": [],
                "blocking": ["PyYAML not available - cannot read the tenant baseline."]}
    try:
        data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    except Exception as e:
        return {"ok": False, "tenant": tenant, "warnings": [],
                "blocking": [f"tenant-brand/{tenant}.yaml did not parse: {e}"]}

    entries = {e.get("key"): e for e in (data.get("baseline") or []) if isinstance(e, dict)}
    blocking: list[str] = []
    warnings: list[str] = []

    def present_and_exists(key: str) -> tuple[bool, str]:
        e = entries.get(key)
        if not e:
            return False, f"baseline entry '{key}' absent from {tenant}.yaml"
        if str(e.get("status", "")).lower() != "present":
            return False, f"'{key}' not established (status: {e.get('status', 'missing')})"
        href = e.get("href")
        if href and not (tb / href).resolve().exists():
            return False, f"'{key}' marked present but file missing: {href}"
        return True, ""

    for key in REQUIRED:
        ok, why = present_and_exists(key)
        if not ok:
            blocking.append(why)

    for key in RECOMMENDED:
        e = entries.get(key)
        if not e or str(e.get("status", "")).lower() != "present":
            warnings.append(f"{key} not yet established (recommended, non-blocking)")

    return {"ok": not blocking, "tenant": tenant, "blocking": blocking, "warnings": warnings}


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-0 baseline gate - may a campaign start?")
    ap.add_argument("--tenant", required=True, help="tenant slug (matches tenant-brand/<slug>.yaml)")
    ap.add_argument("--root", default=str(ROOT), help="checkout root (default: this checkout)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    r = check_baseline(Path(a.root).resolve(), a.tenant)
    if not a.quiet:
        print(f"[phase0-gate] {a.tenant}: " +
              ("PASS - campaigns may start" if r["ok"] else "BLOCKED - Phase 0 incomplete"))
        for b in r["blocking"]:
            print(f"  x {b}")
        for w in r["warnings"]:
            print(f"  ! {w}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
