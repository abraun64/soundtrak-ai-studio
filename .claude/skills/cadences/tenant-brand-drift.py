#!/usr/bin/env python3
"""SYS-020 cadence (b) — monthly TENANT BRAND-DRIFT CHECK.

Read-only + SURFACES only. For each tenant it compares the tenant playbook's
last-modified time against the newest SHIPPED asset for that tenant, and flags
tenants whose playbook is stale relative to what's actually shipping — i.e. the
brand guidance may no longer reflect the work going out the door. It writes a
digest and, for each genuinely-drifted tenant, files ONE deduped inbox idea. It
NEVER edits a playbook, an asset, or a campaign.

  python .claude/skills/cadences/tenant-brand-drift.py

Monthly schedule (see SKILL.md for the Register-ScheduledTask command). Worktree-
aware (resolves tenant-brand/ + campaigns/ to the main checkout via repo_paths).

"Shipped asset" = an asset.yaml whose status starts with 'Approved' (the canonical
ship state), using the asset.yaml file mtime as the ship-time proxy. Drift = the
newest such asset is more than DRIFT_GAP_DAYS newer than the playbook.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cadence_common as cc  # noqa: E402

DRIFT_GAP_DAYS = 30   # playbook older than newest shipped asset by more than this → flag


def _status_of(asset_yaml: Path) -> str:
    """Top-level `status:` value of an asset.yaml (read-only, defensive)."""
    try:
        for line in asset_yaml.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^status:\s*["\']?(.*)$', line)
            if m:
                return m.group(1).strip().strip('"\'')
    except Exception:  # noqa: BLE001
        pass
    return ""


def _is_approved(status: str) -> bool:
    s = status.strip().lower()
    # canonical ship state is 'Approved' (often with a trailing note, or a ✅ prefix)
    return s.startswith("approved") or s.startswith("✅ approved") or "approved" in s[:14]


def newest_shipped_asset(tenant: str) -> tuple[float | None, str]:
    """(mtime, label) of the newest Approved asset across the tenant's campaigns."""
    newest_mtime: float | None = None
    newest_label = ""
    for camp in cc.campaigns_for_tenant(tenant):
        for ay in camp.glob("assets/*/asset.yaml"):
            if _is_approved(_status_of(ay)):
                mt = ay.stat().st_mtime
                if newest_mtime is None or mt > newest_mtime:
                    newest_mtime = mt
                    newest_label = f"{camp.name}/{ay.parent.name}"
    return newest_mtime, newest_label


def main() -> int:
    today = cc.today_str()
    now = datetime.now().timestamp()
    tenants = cc.discover_tenants()

    lines = [f"# Tenant brand-drift check — {today}", ""]
    lines.append("Read-only monthly check. Flags tenants whose PLAYBOOK is stale relative to "
                 "the newest SHIPPED (Approved) asset — the brand guidance may have fallen "
                 "behind the work. Nothing is edited; findings are surfaced only.")
    lines += ["", f"Threshold: playbook flagged if it is more than **{DRIFT_GAP_DAYS} days** "
                  f"older than the newest shipped asset.", "", "## Per tenant"]

    drifted: list[tuple[str, int, str]] = []
    for tenant in tenants:
        playbook = cc.TENANT_BRAND_DIR / f"{tenant}-playbook.md"
        if not playbook.exists():
            lines.append(f"- **{tenant}** — no playbook at `{playbook.name}` (skipped)")
            continue
        pb_mtime = playbook.stat().st_mtime
        pb_age = int((now - pb_mtime) / 86400)
        asset_mtime, asset_label = newest_shipped_asset(tenant)
        if asset_mtime is None:
            lines.append(f"- **{tenant}** — playbook {pb_age}d old · no shipped (Approved) asset found · OK")
            continue
        gap = int((asset_mtime - pb_mtime) / 86400)   # positive = asset newer than playbook
        asset_age = int((now - asset_mtime) / 86400)
        if gap > DRIFT_GAP_DAYS:
            drifted.append((tenant, gap, asset_label))
            lines.append(f"- ⚠️ **{tenant}** — playbook {pb_age}d old; newest shipped asset "
                         f"`{asset_label}` is {asset_age}d old → **playbook lags by {gap}d** (DRIFT)")
        else:
            lines.append(f"- **{tenant}** — playbook {pb_age}d old; newest shipped `{asset_label}` "
                         f"{asset_age}d old → lag {gap}d · OK")

    if not tenants:
        lines.append("- (no tenants discovered from campaign.yaml files)")

    # Surface-only escalation: one deduped idea per drifted tenant.
    filed: list[str] = []
    for tenant, gap, asset_label in drifted:
        title = f"Tenant '{tenant}' playbook may be stale — lags newest shipped asset by {gap} days"
        filed += cc.file_new_ideas(
            [title], raised_by="tenant-brand-drift", today=today,
            summary=f"The monthly brand-drift check found {tenant}'s playbook {gap}d behind its "
                    f"newest shipped asset ({asset_label}); review whether brand guidance still matches.",
            source="cadence (tenant-brand-drift)")

    if filed:
        lines += ["", "## Filed this run (deduped — triage to confirm)"]
        lines += [f"- {iid}" for iid in filed]
    else:
        lines += ["", "## Filed this run", "- None (no new drift, or ideas already on file)."]

    lines += ["", "## Next",
              "For each flagged tenant, open the playbook and the recent shipped assets side by side; "
              "if the guidance has fallen behind, graduate the learnings UP into the playbook (the "
              "normal wrap path). This cadence only surfaces the gap — it never edits the playbook."]

    out = cc.write_digest("tenant-brand-drift", "tenant-brand-drift", lines, today)
    print("\n".join(lines))
    print(f"\n[tenant-brand-drift] wrote {out}" +
          (f" · filed {len(filed)} idea(s)" if filed else " · filed 0 ideas"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
