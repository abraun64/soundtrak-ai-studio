#!/usr/bin/env python3
"""
State drift checker — walks every asset folder in a campaign (or all campaigns) and
reports inconsistencies between the layers that hold "what's this asset's status":

  Layer A: asset.yaml `status:` field            (gallery's primary check)
  Layer B: <NN>-<slug>.md **Status**: line       (gallery's MD fallback)
  Layer C: preview.md **Status**: line           (operator review surface)
  Layer D: dashboard md asset list table         (campaign overview)

Reports any disagreement between A/B/C, and flags dashboard rows that don't match
the asset's canonical state. Doesn't fix — just surfaces. Pair with status-propagator
for the fix.

Usage:
  python .claude/skills/check-state/check.py --campaign acme-launch-2026q2
  python .claude/skills/check-state/check.py --all-campaigns
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
import tenant_paths as _tp  # noqa: E402  — W4 dual-path: also find business-rooted tenants

sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "render-html"))
try:
    import plan_model  # noqa: E402 — shared v3 plan parser; Plan is the source of truth for channel/name
except Exception:  # pragma: no cover
    plan_model = None

# Windows-safe stdout: plan channel/name values carry em-dashes etc. — don't let the
# cp1252 console crash the report (mirrors build-gallery.py's reconfigure).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover
        pass

# Pull the same status detection logic the gallery uses, so drift reports are
# consistent with what the gallery actually surfaces.
STATUS_PATTERNS = [
    # Each greedy `.*` swapped for `[^\n]*` so patterns are line-bound — prevents
    # false positives where prose elsewhere in the doc trips the Status detector
    # (e.g. "Operator rejected v3.4" several paragraphs away from the **Status**: line).
    (re.compile(r"Status[^\n]*Archived|archived 20", re.I), "Archived"),
    (re.compile(r"Status[^\n]*(?:Declined|Killed|Rejected)", re.I), "Declined"),
    (re.compile(r"✅\s*Approved|\*\*Status\*\*:\s*✅|Status[^\n]*✅?\s*Approved|status:\s*['\"]?approved", re.I), "Approved"),
    (re.compile(
        r"Brand[- ]cleared|Pass-with-Required|Pass-with-Notes"
        r"|ready[\s_]for[\s_](?:brand|operator)"
        r"|ready\s+for\s+Brand\s+verdict"
        r"|awaiting\s+(?:operator|your)\s+(?:gate|approval|review)"
        r"|Brand[^\n]*Pass-with"
        r"|For\s+Human\s+Review",
        re.I), "For Human Review"),
    (re.compile(r"Draft|in flight|in progress|cycle [0-9]|Status[^\n]*Drafted|Status[^\n]*Draft", re.I), "In Production"),
]


def normalise_yaml_status(raw: str) -> str:
    r = raw.lower().strip().strip("'\"")
    if "approved" in r:
        return "Approved"
    if any(x in r for x in ["review", "human", "gate", "brand pass", "pass-with", "awaiting"]):
        return "For Human Review"
    if any(x in r for x in ["archived", "archive"]):
        return "Archived"
    if any(x in r for x in ["decline", "killed", "rejected"]):
        return "Declined"
    if any(x in r for x in ["draft", "production", "progress"]):
        return "In Production"
    return raw.strip() or "(empty)"


def scan_text_for_status(text: str) -> str:
    for pat, label in STATUS_PATTERNS:
        if pat.search(text):
            return label
    return "(unknown)"


def get_yaml_status(asset_dir: Path) -> str:
    yaml_path = asset_dir / "asset.yaml"
    if not yaml_path.exists():
        return "(no yaml)"
    text = yaml_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'^status:\s*["\']?([^"\'\n]+)["\']?\s*$', text, re.MULTILINE)
    if m:
        return normalise_yaml_status(m.group(1))
    return "(no status field)"


def get_md_status(md_path: Path, yaml_status: str | None = None) -> str:
    """Find the **Status**: line and parse the state word right after the emoji.
    Much more reliable than scanning the whole doc — prose elsewhere (e.g.
    'Operator rejected v3.4') can't trip the detector.

    If the MD contains the STATUS_AUTO marker, the file is yaml-derived (no
    hand-authored status to drift); return the yaml status itself so the
    drift check is a no-op."""
    if not md_path.exists():
        return "(missing)"
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    if "<!-- STATUS_AUTO -->" in text:
        # Status is yaml-derived; no drift possible by construction.
        return yaml_status or "(yaml-derived)"
    # Find the Status: line
    m = re.search(r'^\*\*Status\*\*:\s*(.+?)$', text, re.MULTILINE)
    if not m:
        return scan_text_for_status(text[:5000])  # fallback for old formats
    status_line = m.group(1)
    # Emoji-state mapping: look for the FIRST state-word that follows whitespace/emoji
    # within the first ~100 chars of the status line (where canonical writers put the state).
    head = status_line[:120]
    # Check in priority order — case-insensitive throughout
    if re.search(r'\bapproved\b', head, re.I):
        return "Approved"
    if re.search(r'\barchived\b', head, re.I):
        return "Archived"
    if re.search(r'\b(declined|killed|rejected)\b', head, re.I):
        return "Declined"
    if re.search(r'(For Human Review|Pass-with-Notes|Pass-with-Required|Brand[- ]cleared|awaiting|ready[\s_]for[\s_](?:brand|operator))', head, re.I):
        return "For Human Review"
    if re.search(r'\b(Draft|drafted|in[\s-]flight|in[\s-]production|in[\s-]progress)\b', head, re.I):
        return "In Production"
    return "(unknown)"


def check_asset(asset_dir: Path) -> dict:
    yaml = get_yaml_status(asset_dir)
    # Prefer <folder>.md as the asset record (semantic match to the folder slug);
    # fall back to any numeric-prefix .md only if no folder-named record exists.
    named_record = asset_dir / f"{asset_dir.name}.md"
    if named_record.exists():
        numeric_md = named_record
    else:
        numeric_md = next(asset_dir.glob("[0-9]*-*.md"), None)
    record = get_md_status(numeric_md, yaml) if numeric_md else "(no record)"
    preview = get_md_status(asset_dir / "preview.md", yaml)

    # Drift detection: yaml is canonical
    drift = []
    if record not in ("(missing)", "(no record)", "(unknown)") and record != yaml:
        drift.append(f"record={record}")
    if preview not in ("(missing)", "(unknown)") and preview != yaml:
        drift.append(f"preview={preview}")
    return {
        "asset_dir": asset_dir,
        "yaml": yaml,
        "record": record,
        "preview": preview,
        "drift": drift,
    }


# Layer I (SYS-036): copy.md is the operator's EDIT SURFACE — bare copy only. These are
# the high-confidence bloat signatures that must NOT appear there (they belong in the asset
# record, asset.md): a strategic thesis block, a "Current state" / version-history changelog,
# and per-section [vN: design notes] annotations. See docs/specs/asset.md §Editable copy file.
COPY_BLOAT_PATTERNS = [
    ("version-log", re.compile(r"(?im)^\s*\*?\*?Current state\*?\*?\s*:|Prior:\s*v\d|version[-\s]history")),
    ("thesis-block", re.compile(r"(?im)^\s*\*\*The thesis\*\*")),
    ("design-annotation", re.compile(r"\[v\d[.\d]*\s*:")),
]


def check_copy_bloat(asset_folders) -> list[str]:
    """Flag any copy.md carrying a banned non-copy section. One line per offending file."""
    issues = []
    for af in asset_folders:
        cp = af / "copy.md"
        if not cp.exists():
            continue
        try:
            text = cp.read_text(encoding="utf-8")
        except OSError:
            continue
        hits = [name for name, rx in COPY_BLOAT_PATTERNS if rx.search(text)]
        if hits:
            issues.append(f"  {af.name}/copy.md — banned section(s): {', '.join(hits)} → move to asset.md (copy.md is the edit surface)")
    return issues


_BOARD_DONE = ("done", "approved", "complete", "shipped", "✅")


def check_board_currency(campaign_dir: Path) -> list[str]:
    """Layer J (SYS-038) — board-currency / world-↔-data drift. Flags a pending
    operator_action whose phase the campaign has already moved PAST: the campaign
    advanced but the task wasn't reconciled (it shipped → mark it done, or it's
    genuinely overdue). This is the 'items don't drop off as the campaign progresses'
    class that a long/rabbit-hole session silently introduces. Pure data — reuses the
    render layer's phase helpers, honours SYS-031's active-later-phase exception."""
    issues: list[str] = []
    try:
        sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "render-html"))
        import operator_actions as oa  # noqa: PLC0415 — lazy: optional dependency
        cur = oa._current_phase_num(campaign_dir)
        if cur is None:
            return issues
        active_later = oa._active_later_phase_nums(campaign_dir)
        actions = oa.scan_campaign(campaign_dir)
    except Exception:  # noqa: BLE001 — never let the detector break the checker
        return issues
    for a in actions:
        if not isinstance(a, dict):
            continue
        status = str(a.get("status") or "pending").strip().lower()
        if any(d in status for d in _BOARD_DONE):
            continue
        pn = oa._phase_num(a.get("phase"))
        if pn is None or pn >= cur or pn in active_later:
            continue
        title = str(a.get("title") or a.get("id") or "(action)")[:55]
        issues.append(
            f"  {campaign_dir.name}: pending action in phase {pn} ('{title}') but the campaign "
            f"is at phase {cur} — reconcile (mark done if it shipped, else confirm still owed)"
        )
    return issues


def check_dashboard_drift(campaign_dir: Path, asset_results: list[dict]) -> list[str]:
    """Scan the dashboard md for stale references to approved/archived assets.
    Takes the campaign DIR (works for flat campaigns/<slug>/ AND business-rooted
    <Tenant>/campaigns/<slug>/) rather than reconstructing a flat path from the slug."""
    dashboard_path = campaign_dir / f"{campaign_dir.name}.md"
    if not dashboard_path.exists():
        return [f"(no dashboard md at {dashboard_path.name})"]
    text = dashboard_path.read_text(encoding="utf-8")
    issues = []
    approved_ids = []
    for r in asset_results:
        if r["yaml"] == "Approved":
            # asset_id is the numeric prefix on the folder name
            asset_id = r["asset_dir"].name.split("-")[0]
            approved_ids.append(asset_id)
    # Look for stale phrases tied to assets we know are approved
    stale_phrases = [
        r"Producer in flight",
        r"awaiting (operator )?approval",
        r"⏸ Queued",
        r"⏳ Wave \d+ Producer",
        r"Gate Asset #?\d+",
    ]
    # History table rows look like `| YYYY-MM-DD |` — skip them, they're historical
    # records of past state, not current claims about asset status.
    history_row = re.compile(r'^\|\s*\d{4}-\d{2}-\d{2}\s*\|')
    for asset_id in approved_ids:
        for phrase in stale_phrases:
            pat = re.compile(
                rf'(^.*#0?{int(asset_id)}.*?{phrase}.*$|^.*Asset #?0?{int(asset_id)}.*?{phrase}.*$)',
                re.MULTILINE | re.I,
            )
            for m in pat.finditer(text):
                line = m.group().strip()
                if history_row.match(line):
                    continue  # historical row, not active drift
                issues.append(f"  #{asset_id} (yaml=Approved) but dashboard line: {line[:140]}")
    return issues


def check_plan_roster_drift(campaign_dir: Path, asset_folders: list[Path]) -> list[str]:
    """Layer E (added 2026-06-09 after the Plan-roster miss): every numeric-prefix
    asset folder on disk must appear as a row `| <id> |` in plan.md's asset table.
    Operator-added assets that never get a Plan row are exactly how the Plan rots."""
    plan_path = campaign_dir / "plan.md"
    if not plan_path.exists():
        return []  # no plan = nothing to drift against (e.g. cadence-only campaigns)
    text = plan_path.read_text(encoding="utf-8")
    issues = []
    for af in asset_folders:
        m = re.match(r"^(\d+)", af.name)
        if not m:
            continue
        asset_id = int(m.group(1))
        # Match a table row starting `| 23 ` or `| 23|` (tolerate bold/whitespace)
        row_pat = re.compile(rf"^\|\s*\**{asset_id}\**\s*\|", re.MULTILINE)
        if not row_pat.search(text):
            issues.append(f"  asset folder {af.name} on disk has NO row in plan.md asset roster")
    return issues


def check_campaign_yaml_drift(campaign_dir: Path, asset_folders: list[Path]) -> list[str]:
    """Layer F (added 2026-06-09 after the campaign.yaml phase-rot miss):
    sanity-check campaign.yaml phase rows against reality.
      - any phase title claiming 'N assets' must match the count on disk
      - status_mode: derive_blocks_launch with zero blocks_launch declarations
        anywhere is an unwired input (renders a false '✅ complete')."""
    yaml_path = campaign_dir / "campaign.yaml"
    if not yaml_path.exists():
        return []
    text = yaml_path.read_text(encoding="utf-8")
    issues = []
    n_disk = len(asset_folders)
    for m in re.finditer(r'title:\s*"[^"]*?(\d+)\s+assets', text):
        claimed = int(m.group(1))
        if claimed != n_disk:
            # Plan roster may legitimately exceed disk (queued assets not yet
            # built get no folder) — only flag when DISK exceeds the claim,
            # i.e. assets exist that the yaml has never heard of.
            if n_disk > claimed:
                issues.append(
                    f"  campaign.yaml phase title claims '{claimed} assets' but {n_disk} asset folders exist on disk"
                )
    if "derive_blocks_launch" in text:
        blocks_declared = False
        for af in asset_folders:
            ay = af / "asset.yaml"
            if ay.exists() and "blocks_launch" in ay.read_text(encoding="utf-8"):
                blocks_declared = True
                break
        if not blocks_declared:
            issues.append(
                "  campaign.yaml uses status_mode: derive_blocks_launch but NO asset.yaml declares blocks_launch "
                "(unwired input — renders a false '✅ All launch blockers complete'; use explicit status)"
            )
    return issues


# --- Layer K (SYS-120): produced-but-unpublished deliverables ------------------
# A finished deliverable sitting in an asset folder but never DECLARED in asset.yaml
# (neither ship:true nor ship:false) is invisible to the gallery and every downstream
# surface. Every OTHER check here reconciles only what is DECLARED, so a file never
# declared at all slips every net (the 8-walkthrough-finals miss). Flag it so the
# operator declares ship:true (to tile it) or ship:false (to suppress it).
_FINAL_BINARY_EXTS = {".mp4", ".mov", ".webm", ".gif", ".pdf", ".pptx", ".docx", ".key", ".xlsx"}
_FINAL_WEB_EXTS = {".html", ".png", ".jpg", ".jpeg"}          # only flagged in DEDICATED output dirs
_FINAL_OUTPUT_DIRS = ("finals", "exports", "final", "out", "deliverables")
# Never a shippable final: render sources, build tools, retina/thumb/poster exports,
# preview scaffolds, underscore-prefixed intermediates, remotion/template render trees.
_NON_FINAL_RE = re.compile(
    r"(-render\.html$)|(^build-.*\.py$)|(@2x)|(thumb)|(poster)|(-preview\.)|(^_)|(remotion)|(template)|(scaffold)|(\.tmp$)",
    re.IGNORECASE,
)


def check_undeclared_finals(asset_folders) -> list[str]:
    """Layer K (SYS-120) — produced-but-unpublished. Scans each asset folder's OUTPUT
    locations for finished-deliverable files not accounted for in asset.yaml. Tuned for
    near-zero false positives: binaries (mp4/pdf/pptx/…) are flagged in the folder root,
    the images/ dir, and dedicated output dirs; web finals (html/png) ONLY in dedicated
    output dirs (finals/ etc.), because the root + images/ legitimately hold render
    sources and components. Render-pipeline sources, thumbs, posters, @2x, and
    _intermediates are skipped."""
    import yaml
    issues = []
    for af in asset_folders:
        ay = af / "asset.yaml"
        if not ay.exists():
            continue
        try:
            data = yaml.safe_load(ay.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        declared = set()
        fb = data.get("files")
        if isinstance(fb, dict):
            for k in fb:
                declared.add(str(k).replace("\\", "/").lstrip("./"))
        for key in ("copy_file", "production_file", "view_source", "template_source"):
            v = data.get(key)
            if isinstance(v, str) and v:
                declared.add(v.replace("\\", "/").lstrip("./"))
        scan = [(af, _FINAL_BINARY_EXTS)]                     # root: binaries only
        img = af / "images"
        if img.is_dir():
            scan.append((img, _FINAL_BINARY_EXTS))           # images/: binaries only (components live here)
        for sub in _FINAL_OUTPUT_DIRS:
            d = af / sub
            if d.is_dir():
                scan.append((d, _FINAL_BINARY_EXTS | _FINAL_WEB_EXTS))
        for scan_dir, exts in scan:
            for f in sorted(scan_dir.iterdir()):
                if not f.is_file() or f.suffix.lower() not in exts:
                    continue
                if _NON_FINAL_RE.search(f.name):
                    continue
                rel = str(f.relative_to(af)).replace("\\", "/")
                if rel in declared or f.name in declared:
                    continue
                issues.append(
                    f"  {af.name}/{rel} — produced but unpublished (not in asset.yaml): "
                    f"declare ship:true to tile it, or ship:false to suppress it"
                )
    return issues


def _plan_ships_index(plan_text: str):
    """Find the 0-based column index of the `Ships` column in the plan asset
    table header, or None if this plan predates the Ships column."""
    for line in plan_text.splitlines():
        s = line.strip()
        if s.startswith("|") and re.search(r"\|\s*#\s*\|\s*Asset\s*\|", s, re.I):
            cells = [c.strip().lower() for c in s.strip("|").split("|")]
            for i, c in enumerate(cells):
                if c == "ships":
                    return i
            return None
    return None


def _plan_ships_cell(plan_text: str, asset_id: int, ships_idx: int):
    for line in plan_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        first = re.sub(r"[*~]", "", cells[0]).strip()
        if first == str(asset_id) and len(cells) > ships_idx:
            return cells[ships_idx]
    return None


def check_ships_drift(campaign_dir: Path, asset_folders: list[Path]) -> list[str]:
    """Layer G (added 2026-06-15): the Plan `Ships` column is the gallery-tile
    contract (one Ships entry = one tile = one asset.yaml ship:true). Catch the
    three ways asset.yaml ship-flags drift from it — all three were live bugs:
      1. asset.html flagged ship:true — the asset RECORD is never a deliverable tile.
      2. an images/ component declared (type: Instance) without ship:false —
         defaults to a stray tile (the embedded-image-becomes-a-tile bug).
      3. Plan Ships is '—' (nothing ships) yet asset.yaml flags files to ship."""
    try:
        import yaml
    except ImportError:
        return []
    plan_path = campaign_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    ships_idx = _plan_ships_index(plan_text) if plan_text else None
    HIDING_ROLES = {"asset_record", "design_doc", "how_to_use", "doc_index", "render_pipeline", "catalog", "rationale"}
    # Only these extensions become gallery tiles — .md never tiles (it's a related doc).
    TILEABLE = {".html", ".png", ".mp4", ".pptx", ".key", ".pdf", ".docx", ".xlsx", ".csv"}
    SEPARATE_PRIMARY_EXTS = {".mp4", ".pptx", ".key", ".pdf", ".docx", ".xlsx"}
    issues = []
    for af in asset_folders:
        ay = af / "asset.yaml"
        if not ay.exists():
            continue
        try:
            data = yaml.safe_load(ay.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        files_block = data.get("files") or {}
        # Compute the tile-able set that WOULD show (replicate the gallery's ship logic)
        would_ship = []
        for fname, meta in files_block.items():
            meta = meta or {}
            if Path(fname).suffix.lower() not in TILEABLE:
                continue  # .md and friends never tile
            shipv = meta.get("ship")
            if shipv is True:
                would_ship.append(fname)
            elif shipv is None and meta.get("type") != "Foundation" \
                    and meta.get("role", "") not in HIDING_ROLES \
                    and fname.lower() != "asset.html":
                would_ship.append(fname)  # default-show
        # 1. asset.html ship:true AND there's a clearly-separate primary deliverable
        #    (a video/doc, an index.html/case-study.html, or a subfolder file). In that
        #    case asset.html is the RECORD, not the deliverable, and shouldn't tile.
        #    NOT flagged when asset.html is the sole/primary deliverable surface — emails,
        #    posts, etc. render their deliverable AS asset.html.
        ah = files_block.get("asset.html") or {}
        if ah.get("ship") is True:
            others = [f for f in would_ship if f.lower() != "asset.html"]
            has_separate_primary = any(
                Path(f).suffix.lower() in SEPARATE_PRIMARY_EXTS
                or Path(f).name.lower() in {"index.html", "case-study.html"}
                or "/" in f.replace("\\", "/")
                for f in others
            )
            if has_separate_primary:
                issues.append(f"  {af.name}: asset.html is ship:true but the deliverables are separate files ({', '.join(others[:3])}…) — asset.html is the record here; set ship:false")
        # 2. Subfolder component that defaults-to-show (ship not set). Deliverables
        #    that live in a subfolder (final/*.mp4) are explicitly ship:true; an
        #    UN-flagged tileable file in a subfolder (images/*, storyboards/*,
        #    drafts/*) is almost always an intermediate component that will tile as
        #    a stray. Explicit ship:true in a subfolder is fine (a real deliverable).
        for fname, meta in files_block.items():
            meta = meta or {}
            norm = fname.replace("\\", "/")
            if "/" in norm and Path(fname).suffix.lower() in TILEABLE \
                    and meta.get("ship") is None and meta.get("type") != "Foundation" \
                    and meta.get("role", "") not in HIDING_ROLES:
                issues.append(f"  {af.name}: {fname} is a subfolder component with no ship flag — defaults to a stray tile; set ship:false (or ship:true if it really is a deliverable)")
        # 3. Plan Ships '—' but files would ship
        m = re.match(r"^(\d+)", af.name)
        if m and ships_idx is not None:
            cell = _plan_ships_cell(plan_text, int(m.group(1)), ships_idx)
            if cell is not None and cell.strip() in ("—", "-", "–", "") and would_ship:
                issues.append(f"  {af.name}: plan Ships is '—' but asset.yaml would tile {len(would_ship)} file(s) — reconcile the contract")
    return issues


def check_close_report_drift(campaign_dir: Path) -> list[str]:
    """Layer H (added 2026-06-15): a CLOSED campaign MUST carry a results report.
    Campaign close = forensic-analyst results report + campaign-end retro +
    graduation + freeze (per docs/specs/campaign-report.md). The wrap gate sets
    `closed: true` only AFTER the report exists; this catches a campaign frozen
    without the readout. Closed signal: campaign.yaml `closed: true` / `status: closed`,
    or the dashboard md '**Status**: ... Closed/Wrapped/Archived'."""
    issues: list[str] = []
    closed = False
    yaml_path = campaign_dir / "campaign.yaml"
    if yaml_path.exists():
        try:
            ytext = yaml_path.read_text(encoding="utf-8")
            if re.search(r"^\s*closed:\s*true\b", ytext, re.M | re.I) or \
               re.search(r"^\s*status:\s*['\"]?closed", ytext, re.M | re.I):
                closed = True
        except Exception:
            pass
    if not closed:
        dash = campaign_dir / f"{campaign_dir.name}.md"
        if dash.exists():
            try:
                dtext = dash.read_text(encoding="utf-8")[:2000]
                if re.search(r"\*\*Status\*\*:\s*[^\n]*\b(closed|wrapped|archived)\b", dtext, re.I):
                    closed = True
            except Exception:
                pass
    if not closed:
        return issues  # not closed -> nothing to enforce
    report_dir = campaign_dir / "report"
    report_files = (list(report_dir.glob("*results*.md")) + list(report_dir.glob("*results*.html"))) if report_dir.is_dir() else []
    if not report_files:
        issues.append(
            "  campaign is CLOSED but has NO results report in report/ — a closed campaign must carry "
            "the forensic-analyst results readout. Run the close (report -> retro -> graduate) before "
            "freezing. Per docs/specs/campaign-report.md."
        )
    return issues


def check_channel_name_drift(campaign_dir: Path, asset_folders: list[Path]) -> list[str]:
    """Layer K (2026-07): for a v3 plan, each asset.yaml's `default_channel` + `asset_name`
    MUST equal its Plan row's Channel + name. The Plan is the source of truth for the asset
    catalog; an off-Plan channel is EXACTLY how an asset silently drops from the gallery (the
    render loop skips a channel it doesn't know). Legacy plans (no Type/Channel column —
    plan_model returns []) are not enforced. Per docs/specs/plan.md §'living source of truth'."""
    issues: list[str] = []
    plan_path = campaign_dir / "plan.md"
    if plan_model is None or not plan_path.exists():
        return issues
    try:
        rows = plan_model.parse_plan_markdown(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return issues
    if not rows:
        return issues  # legacy plan — channel/name not enforced against the Plan
    idx = plan_model.index_by_id(rows)

    def _val(text: str, key: str):
        m = re.search(rf"(?m)^\s*{key}:\s*(.+?)\s*$", text)
        if not m:
            return None
        v = m.group(1).strip()
        if v[:1] in ('"', "'"):                              # quoted -> quoted content
            end = v.find(v[0], 1)
            return v[1:end] if end > 0 else v[1:].strip("\"'")
        return re.split(r"\s+#", v, maxsplit=1)[0].strip()   # unquoted -> drop ' # comment'

    for af in asset_folders:
        m = re.match(r"^(\d+[a-z]?)", af.name)
        if not m:
            continue
        key = m.group(1)
        row = idx.get(key) or idx.get(key.lstrip("0") or "0")
        if not row:
            continue  # a missing plan row is Layer E's job, not this one's
        ay = af / "asset.yaml"
        if not ay.exists():
            continue
        try:
            text = ay.read_text(encoding="utf-8")
        except Exception:
            continue
        dc, an = _val(text, "default_channel"), _val(text, "asset_name")
        plan_ch, plan_nm = (row.get("channel") or "").strip(), (row.get("name") or "").strip()
        if dc and plan_ch and dc != plan_ch:
            issues.append(
                f"  {af.name}: asset.yaml default_channel='{dc}' != Plan Channel='{plan_ch}' — "
                f"the Plan is the source of truth; set default_channel to the Plan channel "
                f"(an off-Plan channel silently drops the asset from the gallery)")
        if an and plan_nm and an != plan_nm:
            issues.append(
                f"  {af.name}: asset.yaml asset_name='{an}' != Plan name='{plan_nm}' — "
                f"align the name to the Plan (name drift rots the catalog)")
    return issues


def report_campaign(campaign_dir: Path) -> int:
    """Print drift report for one campaign. Returns number of drift issues found."""
    assets_dir = campaign_dir / "assets"
    if not assets_dir.is_dir():
        print(f"  (no assets/ dir under {campaign_dir.name})")
        return 0
    asset_folders = sorted(
        [p for p in assets_dir.iterdir() if p.is_dir() and re.match(r'^\d+-', p.name)]
    )
    if not asset_folders:
        print(f"  (no numeric-prefix asset folders)")
        return 0

    issue_count = 0
    results = []
    print(f"\n=== {campaign_dir.name} — {len(asset_folders)} assets ===")
    print(f"{'asset':<35} {'yaml':<22} {'record':<22} {'preview':<22} {'drift?'}")
    print("-" * 130)
    for af in asset_folders:
        r = check_asset(af)
        results.append(r)
        drift_flag = "DRIFT: " + " · ".join(r["drift"]) if r["drift"] else "ok"
        if r["drift"]:
            issue_count += 1
        print(f"{af.name:<35} {r['yaml']:<22} {r['record']:<22} {r['preview']:<22} {drift_flag}")

    # Dashboard sweep
    print(f"\n--- dashboard cross-check ---")
    dash_issues = check_dashboard_drift(campaign_dir, results)
    if not dash_issues:
        print("  (no dashboard drift detected for approved assets)")
    else:
        for line in dash_issues[:30]:  # cap to 30 to avoid wall-of-text
            print(line)
            issue_count += 1
        if len(dash_issues) > 30:
            print(f"  ... and {len(dash_issues) - 30} more (truncated)")

    # Plan roster sweep (Layer E)
    print(f"\n--- plan roster cross-check ---")
    plan_issues = check_plan_roster_drift(campaign_dir, asset_folders)
    if not plan_issues:
        print("  (every asset folder on disk has a plan.md roster row)")
    else:
        for line in plan_issues:
            print(line)
            issue_count += 1

    # campaign.yaml sweep (Layer F)
    print(f"\n--- campaign.yaml cross-check ---")
    cy_issues = check_campaign_yaml_drift(campaign_dir, asset_folders)
    if not cy_issues:
        print("  (campaign.yaml phase rows consistent with disk)")
    else:
        for line in cy_issues:
            print(line)
            issue_count += 1

    # Ships ↔ ship:true contract sweep (Layer G)
    print(f"\n--- ships contract cross-check ---")
    ships_issues = check_ships_drift(campaign_dir, asset_folders)
    if not ships_issues:
        print("  (asset.yaml ship-flags consistent with the plan Ships contract)")
    else:
        for line in ships_issues:
            print(line)
            issue_count += 1

    # Channel + name ↔ Plan sweep (Layer K — the v3 one-vocabulary gate)
    print(f"\n--- plan channel/name cross-check ---")
    chan_issues = check_channel_name_drift(campaign_dir, asset_folders)
    if not chan_issues:
        print("  (asset.yaml default_channel + asset_name match the Plan, or legacy plan)")
    else:
        for line in chan_issues:
            print(line)
            issue_count += 1

    # Campaign-close report sweep (Layer H)
    print(f"\n--- campaign-close report cross-check ---")
    close_issues = check_close_report_drift(campaign_dir)
    if not close_issues:
        print("  (campaign not closed, or closed with a results report present)")
    else:
        for line in close_issues:
            print(line)
            issue_count += 1

    # copy.md bloat sweep (Layer I — SYS-036)
    print(f"\n--- copy.md bloat cross-check ---")
    bloat_issues = check_copy_bloat(asset_folders)
    if not bloat_issues:
        print("  (no copy.md carries a banned thesis / version-log / design-annotation section)")
    else:
        for line in bloat_issues:
            print(line)
            issue_count += 1

    # board-currency sweep (Layer J — SYS-038)
    print(f"\n--- board-currency cross-check ---")
    board_issues = check_board_currency(campaign_dir)
    if not board_issues:
        print("  (no pending action sits in a phase the campaign has already moved past)")
    else:
        for line in board_issues:
            print(line)
            issue_count += 1

    # produced-but-unpublished sweep (Layer K — SYS-120)
    print(f"\n--- produced-but-unpublished cross-check ---")
    final_issues = check_undeclared_finals(asset_folders)
    if not final_issues:
        print("  (no finished deliverable sits in an asset folder undeclared in asset.yaml)")
    else:
        for line in final_issues:
            print(line)
            issue_count += 1

    return issue_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--campaign", help="Campaign slug (e.g. acme-launch-2026q2)")
    parser.add_argument("--all-campaigns", action="store_true", help="Scan every campaign in campaigns/")
    args = parser.parse_args()

    campaigns_root = REPO_ROOT / "campaigns"
    flat = sorted([p for p in campaigns_root.iterdir() if p.is_dir() and (p / "assets").is_dir()]) if campaigns_root.is_dir() else []
    # W4 dual-path: also business-rooted <Tenant>/campaigns/<slug>/ ([] until one exists)
    all_dirs = sorted(flat + [c for c in _tp.business_rooted_campaign_dirs(REPO_ROOT) if (c / "assets").is_dir()], key=lambda p: p.name)
    if args.all_campaigns:
        campaigns = all_dirs
    elif args.campaign:
        match = [c for c in all_dirs if c.name == args.campaign]
        campaigns = match or [campaigns_root / args.campaign]
    else:
        parser.error("specify --campaign <slug> or --all-campaigns")

    total = 0
    for c in campaigns:
        total += report_campaign(c)

    print("\n" + "=" * 60)
    if total == 0:
        print(f"OK — no drift detected across {len(campaigns)} campaign(s).")
        return 0
    print(f"{total} drift issue(s) detected across {len(campaigns)} campaign(s).")
    print(f"Fix each with: python .claude/skills/status-propagator/propagate.py --campaign <slug> --asset <NN> --status <state>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
