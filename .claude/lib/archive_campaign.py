#!/usr/bin/env python3
"""SYS-039 — archive / unarchive a campaign (one-step operator action).

Archiving is a pure SURFACE move. It sets `archived: true` (+ an `archived_date`)
in the campaign's campaign.yaml, so `render_campaign_index_md` routes the campaign
out of the Active grid into the collapsed "Archived campaigns" block on
campaigns/index.html, and `render_cross_campaign_actions_md` drops it from the
tasks queue. NOTHING is deleted: the campaign folder stays on disk (OneDrive) and
in the campaigns git repo. Unarchive clears the flag and the campaign returns to
Active. (The render support already exists — this is the missing operator action.)

  python .claude/lib/archive_campaign.py --campaign <slug>
  python .claude/lib/archive_campaign.py --campaign <slug> --unarchive

Re-renders the All-Campaigns index, the cross-campaign tasks queue, and the
campaign's own dashboard so the surfaces reflect the change immediately. The
canonical boolean is `archived: true` — `status:` is left free for the live state.
Worktree-aware: campaigns/ resolves to the MAIN checkout via repo_paths.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
except Exception:  # noqa: BLE001
    DATA = ROOT
CAMPAIGNS = DATA / "campaigns"
RENDER = ROOT / ".claude" / "skills" / "render-html" / "render.py"


def set_archived_flag(text: str, archive: bool, today: str) -> str:
    """Set/clear the top-level `archived:` (+ `archived_date`) in campaign.yaml
    text. Text-edit so comments + key order are preserved; the caller validates
    the result parses and rolls back otherwise."""
    val = "true" if archive else "false"
    if re.search(r"(?m)^archived:\s*.*$", text):
        text = re.sub(r"(?m)^archived:\s*.*$", f"archived: {val}", text, count=1)
    else:
        text = text.rstrip() + f"\narchived: {val}\n"
    if archive:
        if re.search(r"(?m)^archived_date:\s*.*$", text):
            text = re.sub(r"(?m)^archived_date:\s*.*$", f"archived_date: {today}", text, count=1)
        else:
            text = text.rstrip() + f"\narchived_date: {today}\n"
    else:
        text = re.sub(r"(?m)^archived_date:\s*.*\n?", "", text)
    return text


def _render(md: Path, template: str) -> None:
    """Best-effort re-render of one surface (failure is surfaced but non-fatal)."""
    if not md.exists():
        return
    r = subprocess.run([sys.executable, str(RENDER), "--markdown", str(md), "--template", template],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.stderr.write(f"  WARN: re-render of {md.name} exited {r.returncode}: "
                         f"{(r.stderr or '').strip()[-160:]}\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Archive / unarchive a campaign (surface move only; nothing is deleted).")
    ap.add_argument("--campaign", required=True, help="campaign slug (folder name under campaigns/)")
    ap.add_argument("--unarchive", action="store_true",
                    help="clear the archived flag (return the campaign to Active)")
    args = ap.parse_args()

    archive = not args.unarchive
    cdir = CAMPAIGNS / args.campaign
    cy = cdir / "campaign.yaml"
    if not cy.exists():
        print(f"ERROR: campaign.yaml not found for '{args.campaign}': {cy}", file=sys.stderr)
        return 1

    today = datetime.now().strftime("%Y-%m-%d")
    original = cy.read_text(encoding="utf-8")
    updated = set_archived_flag(original, archive, today)

    # Never leave campaign.yaml unparseable — validate, roll back on any error.
    try:
        import yaml
        yaml.safe_load(updated)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: edit would break campaign.yaml ({e}); aborted, file untouched.", file=sys.stderr)
        return 1
    if updated != original:
        cy.write_text(updated, encoding="utf-8")

    # Re-render the surfaces the flag affects: index, tasks, the campaign dashboard.
    _render(CAMPAIGNS / "index.md", "index")
    _render(CAMPAIGNS / "tasks.md", "tasks")
    dash = cdir / f"{args.campaign}.md"
    if not dash.exists():
        dash = cdir / "dashboard.md"
    _render(dash, "dashboard")

    state = "ARCHIVED" if archive else "UNARCHIVED (returned to Active)"
    print(f"{state}: {args.campaign}")
    print(f"  campaign.yaml: archived = {str(archive).lower()}"
          + (f"  ·  archived_date = {today}" if archive else ""))
    print(f"  re-rendered: campaigns/index.html · tasks.html · {dash.with_suffix('.html').name}")
    print("  nothing deleted — the campaign folder stays on disk and in the campaigns repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
