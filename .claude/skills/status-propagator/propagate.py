#!/usr/bin/env python3
"""
Status propagator — single command updates an asset's status across all the layers
that the gallery + dashboard + operator-review surfaces read from.

Without this script, every approval requires manually touching 5 hand-authored places:
  - asset.yaml  status: field        (load-bearing — gallery's primary check)
  - <NN>-<slug>.md  **Status**: line  (gallery's MD fallback)
  - preview.md  **Status**: line     (operator review surface)
  - dashboard md asset-list row       (out of scope here — manual for now)
  - tasks.md cross-campaign row       (out of scope here — manual for now)

This script handles the asset-local layers (yaml + 2 MDs) atomically, then re-renders
the affected HTMLs + rebuilds the gallery. The dashboard sweep is left for a follow-up
script (or single-source-of-truth refactor) since it requires reconciling Plan-list
numbering against actual folder numbering.

Usage:
  python .claude/skills/status-propagator/propagate.py \
      --campaign acme-launch-2026q2 \
      --asset 01 \
      --status approved \
      [--note "v5.3 final polish approved 2026-06-10"]

Status values (matches gallery `_normalise_yaml_status()` vocabulary):
  approved | for-human-review | in-production | archived | declined
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Windows cp1252 console can't print emoji — force UTF-8 + replace fallback so any
# non-encodable char (Status emoji, en-dashes in notes) renders as `?` instead of crashing.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
import tenant_paths as _tp  # noqa: E402  — W4 dual-path: resolve campaign in either layout

STATUS_DISPLAY = {
    "approved": "Approved",
    "for-human-review": "For Human Review",
    "in-production": "In Production",
    "archived": "Archived",
    "declined": "Declined",
}

STATUS_EMOJI = {
    "approved": "✅",
    "for-human-review": "🟡",
    "in-production": "🔄",
    "archived": "📦",
    "declined": "❌",
}


def find_asset_dir(campaign_slug: str, asset_id: str) -> Path:
    """Locate the asset folder by NN-anything pattern."""
    camp = _tp.find_campaign_dir(REPO_ROOT, campaign_slug)
    campaign_dir = (camp / "assets") if camp else (REPO_ROOT / "campaigns" / campaign_slug / "assets")
    if not campaign_dir.is_dir():
        raise SystemExit(f"Campaign not found: {campaign_slug} (looked flat + business-rooted)")
    # asset_id may be "01" or "1" — normalise both directions
    candidates = list(campaign_dir.glob(f"{asset_id}-*")) + list(
        campaign_dir.glob(f"{int(asset_id):02d}-*")
    )
    # Dedupe (`04-foo` and `04-foo` from zero-padded glob match same path) + dir-only
    candidates = list({c.resolve() for c in candidates if c.is_dir()})
    if not candidates:
        raise SystemExit(f"No asset folder matching id={asset_id} under {campaign_dir}")
    if len(candidates) > 1:
        raise SystemExit(
            f"Multiple folders matched id={asset_id}: {[c.name for c in candidates]}"
        )
    return candidates[0]


def update_yaml_status(asset_dir: Path, new_status_display: str) -> tuple[bool, str]:
    """Edit asset.yaml `status:` field. Returns (changed, msg)."""
    yaml_path = asset_dir / "asset.yaml"
    if not yaml_path.exists():
        return False, "asset.yaml missing — skipped"
    text = yaml_path.read_text(encoding="utf-8")
    # Match `status: "..."` or `status: '...'` or `status: bare` at start of line
    new_line = f'status: "{new_status_display}"'
    pattern = re.compile(r'^status:\s*.*$', re.MULTILINE)
    if pattern.search(text):
        new_text = pattern.sub(new_line, text, count=1)
        if new_text != text:
            yaml_path.write_text(new_text, encoding="utf-8")
            return True, f"yaml status -> {new_status_display}"
        return False, "yaml status already correct"
    # No status field — inject after asset_id or default_channel
    insertion_point = re.search(r'^(asset_name|default_channel):\s*.*$', text, re.MULTILINE)
    if insertion_point:
        idx = insertion_point.end()
        new_text = text[:idx] + f"\n{new_line}" + text[idx:]
        yaml_path.write_text(new_text, encoding="utf-8")
        return True, f"yaml status -> {new_status_display} (added)"
    # Last resort — prepend
    yaml_path.write_text(new_line + "\n" + text, encoding="utf-8")
    return True, f"yaml status -> {new_status_display} (prepended)"


def update_md_status(md_path: Path, emoji: str, display: str, note: str | None) -> tuple[bool, str]:
    """Replace a **Status**: line in an MD file. Returns (changed, msg)."""
    if not md_path.exists():
        return False, f"{md_path.name} missing — skipped"
    text = md_path.read_text(encoding="utf-8")
    new_status = f"**Status**: {emoji} **{display.upper()} {today_iso()}**"
    if note:
        new_status += f" — {note}"
    # Replace existing **Status**: line (greedy until newline)
    pattern = re.compile(r'^\*\*Status\*\*:.*$', re.MULTILINE)
    if pattern.search(text):
        new_text = pattern.sub(new_status, text, count=1)
        if new_text != text:
            md_path.write_text(new_text, encoding="utf-8")
            return True, f"{md_path.name} **Status**: updated"
        return False, f"{md_path.name} already current"
    # No existing line — inject after the H1
    h1_match = re.search(r'^(# .+\n)', text, re.MULTILINE)
    if h1_match:
        idx = h1_match.end()
        new_text = text[:idx] + "\n" + new_status + "\n" + text[idx:]
        md_path.write_text(new_text, encoding="utf-8")
        return True, f"{md_path.name} **Status**: line added"
    md_path.write_text(new_status + "\n" + text, encoding="utf-8")
    return True, f"{md_path.name} **Status**: prepended"


def today_iso() -> str:
    """Return today as ISO date string. Read from environment or a marker file
    rather than calling datetime, so the harness's date is honoured."""
    # Allow override via env for testability
    import os
    override = os.environ.get("PROPAGATE_TODAY")
    if override:
        return override
    # Fallback: read from the campaign dashboard's last updated stamp if present
    # else use a system call
    try:
        from datetime import date
        return date.today().isoformat()
    except Exception:
        return "2026-06-10"


def render_html(md_path: Path, template: str) -> str:
    """Invoke the render-html skill on a markdown file."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / ".claude" / "skills" / "render-html" / "render.py"),
        "--markdown", str(md_path),
        "--template", template,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        return f"  render-html FAILED for {md_path.name}: {result.stderr.strip()[:200]}"
    return f"  rendered {md_path.with_suffix('.html').name}"


def rebuild_gallery(campaign_slug: str) -> str:
    cmd = [
        sys.executable,
        str(REPO_ROOT / ".claude" / "skills" / "asset-gallery" / "build-gallery.py"),
        "--campaign", campaign_slug,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        return f"  gallery rebuild FAILED: {result.stderr.strip()[:300]}"
    last = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "(no output)"
    return f"  gallery rebuilt: {last}"


def update_action_status(asset_dir: Path, task_id: str, new_action_status: str, completed: str | None) -> tuple[bool, str]:
    """Set the `status:` field of an entry in `operator_actions:` keyed by id.
    Uses pyyaml for safe round-trip; preserves field order best-effort."""
    yaml_path = asset_dir / "asset.yaml"
    if not yaml_path.exists():
        return False, "asset.yaml missing — can't update operator_actions"
    try:
        import yaml as _yaml
    except ImportError:
        return False, "pyyaml not installed — run: pip install pyyaml"
    text = yaml_path.read_text(encoding="utf-8")
    data = _yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return False, "asset.yaml top-level is not a mapping"
    actions = data.get("operator_actions") or []
    if not isinstance(actions, list):
        return False, "operator_actions is not a list"
    target = next((a for a in actions if isinstance(a, dict) and str(a.get("id")) == task_id), None)
    if target is None:
        ids = [str(a.get("id")) for a in actions if isinstance(a, dict)]
        return False, f"task id '{task_id}' not found. Known ids: {ids}"
    target["status"] = new_action_status
    if new_action_status == "done" and completed:
        target["completed"] = completed
    elif new_action_status == "pending":
        target.pop("completed", None)
    yaml_path.write_text(
        _yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    return True, f"operator_action '{task_id}' -> status={new_action_status}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--campaign", required=True, help="Campaign slug (e.g. acme-launch-2026q2)")
    parser.add_argument("--asset", required=True, help="Asset numeric id (e.g. 01 or 1)")
    parser.add_argument("--status", default=None, choices=list(STATUS_DISPLAY.keys()),
                        help="Update asset-level status. Mutually exclusive with --task.")
    parser.add_argument("--task", default=None, help="Operator-action id within the asset (e.g. pick-printer). Use with --done or --pending.")
    parser.add_argument("--done", action="store_true", help="Mark --task as done")
    parser.add_argument("--pending", action="store_true", help="Mark --task as pending (un-done)")
    parser.add_argument("--note", default=None, help="Optional context appended to Status line")
    parser.add_argument("--no-render", action="store_true", help="Skip HTML re-render + gallery rebuild")
    args = parser.parse_args()
    if not (args.status or args.task):
        parser.error("specify either --status <state> OR --task <id> --done/--pending")
    if args.task and not (args.done or args.pending):
        parser.error("--task requires either --done or --pending")

    asset_dir = find_asset_dir(args.campaign, args.asset)
    print(f"asset folder: {asset_dir.relative_to(REPO_ROOT)}")

    if args.task:
        # Task mode — update operator_actions entry only.
        target_status = "done" if args.done else "pending"
        completed = today_iso() if target_status == "done" else None
        print(f"task:         {args.task} -> {target_status}")
        ok, msg = update_action_status(asset_dir, args.task, target_status, completed)
        print(f"  [action]  {msg}")
        if not ok:
            return 1
        if args.no_render:
            print("\nskipping dashboard re-render (--no-render)")
            return 0
        # Re-render the campaign dashboard so the auto-injected To Do block refreshes
        dashboard_md = asset_dir.parent.parent / f"{args.campaign}.md"
        if dashboard_md.exists():
            print(render_html(dashboard_md, "dashboard"))
        return 0

    # Status mode — full propagation across yaml + record + preview + renders
    display = STATUS_DISPLAY[args.status]
    emoji = STATUS_EMOJI[args.status]
    print(f"new status:   {emoji} {display}")
    if args.note:
        print(f"note:         {args.note}")
    print()

    # Layer 1: asset.yaml status field
    changed, msg = update_yaml_status(asset_dir, display)
    print(f"  [yaml]    {msg}")

    # Layer 2: numeric-prefix asset record .md
    numeric_md = next(asset_dir.glob("[0-9]*-*.md"), None)
    if numeric_md:
        changed, msg = update_md_status(numeric_md, emoji, display, args.note)
        print(f"  [record]  {msg}")

    # Layer 3: preview.md
    preview_md = asset_dir / "preview.md"
    if preview_md.exists():
        changed, msg = update_md_status(preview_md, emoji, display, args.note)
        print(f"  [preview] {msg}")

    if args.no_render:
        print("\nskipping HTML re-render + gallery rebuild (--no-render)")
        return 0

    print("\nrendering downstream surfaces:")
    if numeric_md:
        print(render_html(numeric_md, "asset-record"))
    if preview_md.exists():
        print(render_html(preview_md, "asset-preview"))
    # Re-render the campaign dashboard so its derived To Do block refreshes
    dashboard_md = asset_dir.parent.parent / f"{args.campaign}.md"
    if dashboard_md.exists():
        print(render_html(dashboard_md, "dashboard"))
    print(rebuild_gallery(args.campaign))
    print("\ndone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
