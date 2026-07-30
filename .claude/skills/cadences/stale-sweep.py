#!/usr/bin/env python3
"""SYS-020 cadence (c) — STALE-ASSET / STALE-SURFACE SWEEP.

Read-only + SURFACES only. Two sweeps across all campaigns:

  1. STALE ASSETS — any asset.yaml whose status is a 'For Human Review' variant
     and whose file mtime is older than REVIEW_STALE_DAYS (parked awaiting the
     operator too long).
  2. STALE SURFACES — any rendered .html that is older than its source .md /
     .yaml (a surface that no longer reflects its data), for the operator
     surfaces a cadence can safely compare: dashboard, gallery, index, tasks,
     brief, plan, and per-asset previews.

It writes a digest listing both, and files ONE deduped inbox idea per category
when the category is non-empty. It NEVER re-renders, re-statuses, or edits
anything — surfacing is the whole job (re-rendering is CM's job, on a state
change, not a timer's).

  python .claude/skills/cadences/stale-sweep.py

Recommended weekly schedule (see SKILL.md). Worktree-aware (resolves campaigns/
to the main checkout via repo_paths).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cadence_common as cc  # noqa: E402

REVIEW_STALE_DAYS = 10   # asset parked in 'For Human Review' longer than this → flag
SURFACE_SKEW_DAYS = 1    # html older than its source by more than this (in days) → flag

REVIEW_STATES = ("for human review", "for-human-review", "for review", "for-review")


def _status_of(asset_yaml: Path) -> str:
    try:
        for line in asset_yaml.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^status:\s*["\']?(.*)$', line)
            if m:
                return m.group(1).strip().strip('"\'')
    except Exception:  # noqa: BLE001
        pass
    return ""


def sweep_stale_assets(now: float) -> list[tuple[str, int, str]]:
    """(label, days-parked, status) for assets parked in review past threshold."""
    out = []
    for ay in sorted(cc.CAMPAIGNS_DIR.glob("*/assets/*/asset.yaml")):
        status = _status_of(ay)
        if status.strip().lower() in REVIEW_STATES:
            age = int((now - ay.stat().st_mtime) / 86400)
            if age >= REVIEW_STALE_DAYS:
                label = f"{ay.parent.parent.parent.name}/{ay.parent.name}"
                out.append((label, age, status))
    out.sort(key=lambda r: -r[1])
    return out


# render-html stamps every output with the breadcrumb + (when present) library-nav
# chrome; bespoke Producer HTML (slides, mockups, case studies, storyboards) carries
# neither. This is the reliable "was this auto-rendered by our pipeline?" signal.
_PIPELINE_SIG = ('class="crumb', 'library-nav')


def _is_pipeline_output(html: Path) -> bool:
    """True if the .html was produced by the render-html pipeline (so re-rendering
    it from its source is safe + meaningful). Read-only; False on any read error."""
    try:
        text = html.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return False
    return any(s in text for s in _PIPELINE_SIG)


def sweep_stale_surfaces(now: float) -> list[tuple[str, int]]:
    """(html-path-relative, days-html-is-behind-source) for AUTO-RENDERED operator
    surfaces whose HTML is older than the source the render pipeline actually
    rebuilds them from.

    SCOPE (SYS-040): only flag surfaces the system actually re-renders on a state
    change. Two discriminators, both required for the per-asset case:
      - the .html carries the render-html PIPELINE SIGNATURE (every render.py output
        ships the breadcrumb / library-nav chrome), so it is template-rendered, AND
      - it has a SAME-STEM .md newer than it (the source the pipeline rebuilds from);
    plus gallery.html (build-gallery.py, from gallery-config.yaml).
    This EXCLUDES bespoke one-off artifacts a Producer hand-builds (mockups, slides,
    og-cards, storyboards, print specs, case studies). Those produced the original
    false-positive flood two ways: (1) no same-stem source, but a sibling asset.yaml
    mtime bump made every hand-built .html in the folder look 'stale'; (2) a bespoke
    .html that merely shares a stem with a notes .md. Neither is auto-rendered, so a
    timer flagging them is noise the operator can't action by 're-rendering'."""
    flagged = []
    for html in sorted(cc.CAMPAIGNS_DIR.glob("**/*.html")):
        is_gallery = html.name == "gallery.html"
        if not is_gallery and not _is_pipeline_output(html):
            continue  # bespoke / hand-built artifact (not template-rendered) — skip
        sources = []
        same_md = html.with_suffix(".md")
        if same_md.exists():
            sources.append(same_md)
        if is_gallery:
            gc = html.parent / "gallery-config.yaml"
            if gc.exists():
                sources.append(gc)
        if not sources:
            continue
        newest_src = max(p.stat().st_mtime for p in sources)
        skew_days = (newest_src - html.stat().st_mtime) / 86400
        if skew_days > SURFACE_SKEW_DAYS:
            rel = html.relative_to(cc.CAMPAIGNS_DIR)
            flagged.append((str(rel).replace("\\", "/"), int(skew_days)))
    flagged.sort(key=lambda r: -r[1])
    return flagged


def main() -> int:
    today = cc.today_str()
    now = datetime.now().timestamp()

    stale_assets = sweep_stale_assets(now)
    stale_surfaces = sweep_stale_surfaces(now)

    lines = [f"# Stale-asset / stale-surface sweep — {today}", ""]
    lines.append("Read-only sweep. Surfaces (1) assets parked in 'For Human Review' too long and "
                 "(2) rendered HTML older than its source data. Nothing is re-rendered or re-statused "
                 "— re-rendering is CM's job on a state change, not a timer's.")

    lines += ["", f"## Assets parked in review > {REVIEW_STALE_DAYS} days ({len(stale_assets)})"]
    if stale_assets:
        for label, age, status in stale_assets:
            lines.append(f"- ⚠️ **{label}** — {age}d in review (`{status}`)")
    else:
        lines.append("- None over threshold.")

    lines += ["", f"## Surfaces older than their source data > {SURFACE_SKEW_DAYS}d "
                  f"({len(stale_surfaces)})"]
    if stale_surfaces:
        for rel, skew in stale_surfaces[:40]:
            lines.append(f"- ⚠️ `{rel}` — HTML ~{skew}d behind its source")
        if len(stale_surfaces) > 40:
            lines.append(f"- … and {len(stale_surfaces) - 40} more (see full sweep by re-running).")
    else:
        lines.append("- None over threshold.")

    # Surface-only escalation: one deduped idea per non-empty category.
    filed: list[str] = []
    if stale_assets:
        title = f"{len(stale_assets)} asset(s) parked in 'For Human Review' over {REVIEW_STALE_DAYS} days"
        filed += cc.file_new_ideas(
            [title], raised_by="stale-sweep", today=today,
            summary=f"The stale sweep found {len(stale_assets)} asset(s) awaiting the operator past "
                    f"the {REVIEW_STALE_DAYS}-day threshold; review or nudge.",
            source="cadence (stale-sweep)")
    if stale_surfaces:
        title = f"{len(stale_surfaces)} rendered surface(s) older than their source data"
        filed += cc.file_new_ideas(
            [title], raised_by="stale-sweep", today=today,
            summary=f"The stale sweep found {len(stale_surfaces)} HTML surface(s) behind their source "
                    f"markdown/yaml; CM should re-render on the next state change.",
            source="cadence (stale-sweep)")

    if filed:
        lines += ["", "## Filed this run (deduped — triage to confirm)"]
        lines += [f"- {iid}" for iid in filed]
    else:
        lines += ["", "## Filed this run", "- None (nothing over threshold, or ideas already on file)."]

    lines += ["", "## Next",
              "Triage parked assets (approve / send back / kill) and let CM re-render any stale surface "
              "on its next state-changing turn. This cadence only surfaces — it takes no action."]

    out = cc.write_digest("stale-sweep", "stale-sweep", lines, today)
    print("\n".join(lines))
    print(f"\n[stale-sweep] wrote {out}" +
          (f" · filed {len(filed)} idea(s)" if filed else " · filed 0 ideas"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
