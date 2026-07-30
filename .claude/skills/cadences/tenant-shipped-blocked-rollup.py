#!/usr/bin/env python3
"""SYS-020 cadence (d) — weekly PER-TENANT SHIPPED / BLOCKED ROLLUP.

Read-only + SURFACES only. For each tenant, a short standup-style summary:

  - WHAT SHIPPED this period — assets whose status is 'Approved' AND whose
    asset.yaml mtime falls within the last PERIOD_DAYS (recently shipped).
  - WHAT'S BLOCKED — open (not-done) campaign-level operator_actions across the
    tenant's campaigns (the operator decisions holding things up).

It writes a digest. It files ONE deduped inbox idea only when a tenant has
blocked operator_actions older than the period (a decision that has sat too
long). It NEVER edits a campaign, an action, or an asset.

  python .claude/skills/cadences/tenant-shipped-blocked-rollup.py

Weekly schedule (see SKILL.md for the Register-ScheduledTask command). Worktree-
aware (resolves campaigns/ to the main checkout via repo_paths).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cadence_common as cc  # noqa: E402

PERIOD_DAYS = 7   # "this period" window for shipped assets


def _status_of(asset_yaml: Path) -> str:
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
    return s.startswith("approved") or s.startswith("✅ approved") or "approved" in s[:14]


def shipped_this_period(tenant: str, now: float) -> list[tuple[str, int, str]]:
    """(label, days-ago, status-snippet) for Approved assets touched within the window."""
    out = []
    for camp in cc.campaigns_for_tenant(tenant):
        for ay in camp.glob("assets/*/asset.yaml"):
            status = _status_of(ay)
            if _is_approved(status):
                age = int((now - ay.stat().st_mtime) / 86400)
                if age <= PERIOD_DAYS:
                    snippet = (status[:70] + "…") if len(status) > 70 else status
                    # SYS-099 — prefix the ONE plan/gallery number (#8, not the folder's
                    # zero-padded 08-…) so the cadence standup names assets consistently.
                    _m = re.match(r"^(\d+)", ay.parent.name)
                    _n = f"#{int(_m.group(1))} · " if _m else ""
                    out.append((f"{_n}{camp.name}/{ay.parent.name}", age, snippet))
    out.sort(key=lambda r: r[1])
    return out


def blocked_actions(tenant: str) -> list[tuple[str, str, str]]:
    """(campaign, action-title, priority) for OPEN campaign operator_actions.

    Parses operator_actions from campaign.yaml via yaml.safe_load; an action is
    'open' when its status is not done/complete/closed/cancelled/killed."""
    try:
        import yaml
    except ImportError:
        return []
    done_states = {"done", "complete", "completed", "closed", "cancelled", "canceled", "killed"}
    out = []
    for camp in cc.campaigns_for_tenant(tenant):
        cy = camp / "campaign.yaml"
        try:
            data = yaml.safe_load(cy.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        for act in (data.get("operator_actions") or []):
            if not isinstance(act, dict):
                continue
            status = str(act.get("status", "")).strip().lower()
            if status in done_states:
                continue
            title = str(act.get("title", act.get("id", "(untitled action)")))
            prio = str(act.get("priority", "")).strip()
            out.append((camp.name, title, prio))
    return out


def main() -> int:
    today = cc.today_str()
    now = datetime.now().timestamp()
    tenants = cc.discover_tenants()

    lines = [f"# Per-tenant shipped / blocked rollup — {today}", ""]
    lines.append(f"Read-only weekly standup. Per tenant: what was APPROVED in the last {PERIOD_DAYS} "
                 "days, and which operator decisions are still BLOCKING. Surfacing only — nothing "
                 "is shipped, statused, or edited.")

    total_blocked_old = 0
    for tenant in tenants:
        shipped = shipped_this_period(tenant, now)
        blocked = blocked_actions(tenant)
        lines += ["", f"## {tenant}"]
        lines.append(f"**Shipped (last {PERIOD_DAYS}d):** {len(shipped)}")
        if shipped:
            for label, age, snippet in shipped:
                lines.append(f"- ✅ `{label}` — {age}d ago ({snippet})")
        else:
            lines.append("- (nothing approved in window)")
        lines.append(f"**Blocked (open operator decisions):** {len(blocked)}")
        if blocked:
            for camp, title, prio in blocked:
                tag = f" [{prio}]" if prio else ""
                lines.append(f"- ⛔ `{camp}`{tag} — {title}")
            total_blocked_old += len(blocked)
        else:
            lines.append("- (no open operator actions)")

    if not tenants:
        lines += ["", "- (no tenants discovered from campaign.yaml files)"]

    # Surface-only escalation: a single deduped idea if real blockers exist.
    filed: list[str] = []
    if total_blocked_old:
        title = f"{total_blocked_old} open operator decision(s) blocking across tenants — review the rollup"
        filed = cc.file_new_ideas(
            [title], raised_by="tenant-shipped-blocked-rollup", today=today,
            summary=f"The weekly rollup found {total_blocked_old} open operator action(s) blocking "
                    "campaigns; clear or reassign them.",
            source="cadence (tenant-shipped-blocked-rollup)")

    if filed:
        lines += ["", "## Filed this run (deduped — triage to confirm)"]
        lines += [f"- {iid}: {title}" for iid in filed]
    else:
        lines += ["", "## Filed this run", "- None (no blockers, or an idea was already on file)."]

    lines += ["", "## Next",
              "Clear the blocked operator decisions (each links a campaign surface). Shipped items are "
              "for awareness. This cadence only summarises — it never advances a campaign."]

    out = cc.write_digest("tenant-shipped-blocked-rollup", "tenant-shipped-blocked-rollup", lines, today)
    print("\n".join(lines))
    print(f"\n[tenant-shipped-blocked-rollup] wrote {out}" +
          (f" · filed {len(filed)} idea(s)" if filed else " · filed 0 ideas"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
