"""
operator_actions — scan a campaign's assets for pending operator_actions in asset.yaml
and render a markdown table that the dashboard render-html injection replaces in place.

YAML schema per asset.yaml:

  operator_actions:
    - id: pick-printer                         # stable slug for propagator --task
      title: "Pick print partner"
      why: "Inkness Carlton recommended; Bambra Press premium alt"   # optional context
      time: "~10 min"                           # optional time estimate
      blocks_launch: true                       # optional; default false
      priority: P1                              # optional; default P1
      phase: 4                                  # optional; default 4
      where: "preview.md"                       # optional; relative path inside asset folder
      status: pending                           # pending | done
      completed: "2026-06-12"                   # optional ISO date when status=done

A pending action surfaces in the dashboard's auto-generated To Do block.
A done action is silently filtered out. To restore, set status: pending.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


AUTO_INJECT_MARKER = "<!-- OPERATOR_ACTIONS_AUTO -->"
ASSET_LIST_MARKER = "<!-- ASSET_LIST_AUTO -->"
STATUS_MARKER = "<!-- STATUS_AUTO -->"
COMPLIANCE_MARKER = "<!-- COMPLIANCE_AUTO -->"
RESONANCE_MARKER = "<!-- RESONANCE_AUTO -->"
PHASES_MARKER = "<!-- PHASES_AUTO -->"
COST_TOTAL_MARKER = "<!-- COST_TOTAL_AUTO -->"
HUMAN_TIME_TOTAL_MARKER = "<!-- HUMAN_TIME_TOTAL_AUTO -->"  # SYS-082
CAMPAIGN_DNA_MARKER = "<!-- CAMPAIGN_DNA_AUTO -->"  # SYS-089
PHASE_COST_RE = re.compile(r"<!-- PHASE_COST:(\d+) -->")
CROSS_TASKS_MARKER = "<!-- CROSS_CAMPAIGN_ACTIONS_AUTO -->"
CAMPAIGN_INDEX_MARKER = "<!-- CAMPAIGN_INDEX_AUTO -->"

STATUS_DISPLAY = {
    "approved": "✅ Approved",
    "for human review": "🟡 For Human Review",
    "in production": "🔄 In Production",
    "archived": "📦 Archived",
    "declined": "❌ Declined",
}

# Governance Manager verdicts (W1) — surfaced on asset previews via COMPLIANCE_MARKER.
COMPLIANCE_VERDICT_DISPLAY = {
    "clear": "✅ Clear",
    "clear-with-disclaimers": "✅ Clear (disclaimers applied)",
    "hold": "⏸️ Hold for operator",
    "blocked": "⛔ Blocked",
}
COMPLIANCE_VERDICT_CLASS = {
    "clear": "gov--clear",
    "clear-with-disclaimers": "gov--clear",
    "hold": "gov--hold",
    "blocked": "gov--blocked",
}

# Insights Manager advisory resonance read (Phase 4) — surfaced on external-touchpoint
# asset previews via RESONANCE_MARKER. ADVISORY, never a gate.
RESONANCE_READ_DISPLAY = {
    "on-insight": "🎯 On-insight",
    "mixed": "🟡 Mixed",
    "off-key": "🔁 Off-key",
    "n/a-by-design": "⚪ N/A by design",
}
RESONANCE_READ_CLASS = {
    "on-insight": "res--on",
    "mixed": "res--mixed",
    "off-key": "res--off",
    "n/a-by-design": "res--unknown",
}


def inject_asset_status_line(markdown_text: str, asset_dir: Path) -> str:
    """Replace STATUS_MARKER in a per-asset markdown file (preview.md or numeric-prefix
    asset record) with a single-line `**Status**: <display>` block derived from the
    asset's yaml. The yaml is the only place asset status is ever hand-authored;
    preview + asset record files reference it via the marker."""
    if STATUS_MARKER not in markdown_text:
        return markdown_text
    if yaml is None:
        return markdown_text.replace(STATUS_MARKER, "**Status**: (pyyaml unavailable)")
    yaml_path = asset_dir / "asset.yaml"
    if not yaml_path.exists():
        return markdown_text.replace(STATUS_MARKER, "**Status**: (no asset.yaml found)")
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        return markdown_text.replace(STATUS_MARKER, f"**Status**: (yaml parse error: {e})")
    if not isinstance(data, dict):
        return markdown_text.replace(STATUS_MARKER, "**Status**: (yaml top-level not a mapping)")
    raw = str(data.get("status") or "").lower().strip().strip("'\"")
    display = STATUS_DISPLAY.get(raw, raw or "(no status set)")
    line = (
        f"**Status**: {display} "
        "<small>(auto-derived from `asset.yaml` — to change: "
        "`python .claude/skills/status-propagator/propagate.py --campaign <slug> --asset <NN> --status <new-state>`)</small>"
    )
    return markdown_text.replace(STATUS_MARKER, line)


def inject_compliance_line(markdown_text: str, asset_dir: Path) -> str:
    """Replace COMPLIANCE_MARKER in a per-asset md (preview.md / asset record) with the
    Governance Manager verdict line, derived from the asset.yaml `compliance:` block
    (written by CM from the governance return at the Phase-4 gate, W1).

    NO-RETROFIT no-op: if there is no `compliance:` block (no governance ran), the
    marker is stripped to nothing — existing assets render exactly as before. The
    verdict is a red-flag-for-human-review, NOT legal/compliance advice."""
    if COMPLIANCE_MARKER not in markdown_text:
        return markdown_text
    if yaml is None:
        return markdown_text.replace(COMPLIANCE_MARKER, "")
    yaml_path = asset_dir / "asset.yaml"
    if not yaml_path.exists():
        return markdown_text.replace(COMPLIANCE_MARKER, "")
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return markdown_text.replace(COMPLIANCE_MARKER, "")
    comp = data.get("compliance") if isinstance(data, dict) else None
    if not isinstance(comp, dict) or not comp:
        return markdown_text.replace(COMPLIANCE_MARKER, "")  # no governance review → strip

    verdict = str(comp.get("verdict") or "").lower().strip().strip("'\"")
    display = COMPLIANCE_VERDICT_DISPLAY.get(verdict, verdict or "(no verdict)")
    cls = COMPLIANCE_VERDICT_CLASS.get(verdict, "gov--unknown")

    bits = [f'**🛡 Governance**: <span class="gov-verdict {cls}">{display}</span>']
    risk = str(comp.get("risk_tier") or "").strip()
    if risk:
        bits.append(f"{risk} risk")
    disclaimers = comp.get("disclaimers_applied") or []
    if not isinstance(disclaimers, list):
        disclaimers = [disclaimers]
    disclaimers = [str(d) for d in disclaimers if str(d).strip()]
    if disclaimers:
        bits.append(f"disclaimers: {', '.join(disclaimers)}")
    reviewed = str(comp.get("reviewed") or "").strip()
    if reviewed:
        bits.append(f"reviewed {reviewed}")
    counsel = str(comp.get("counsel_confirmed") or "no").strip()
    bits.append(f"counsel: {counsel}")

    notes = str(comp.get("notes") or "").strip()
    notes_md = f" — {notes}" if notes else ""
    line = (
        " · ".join(bits) + notes_md
        + " <small>(red-flag for human review — not legal/compliance advice; "
        "auto-derived from `asset.yaml` `compliance:`)</small>"
    )
    return markdown_text.replace(COMPLIANCE_MARKER, line)


def inject_resonance_line(markdown_text: str, asset_dir: Path) -> str:
    """Replace RESONANCE_MARKER in a per-asset md (preview.md / asset record) with the
    Insights Manager's advisory resonance read, derived from the asset.yaml `resonance:`
    block (written by CM from the Insights Manager Phase-4 return).

    NO-RETROFIT no-op: if there is no `resonance:` block (no read ran — internal/
    Foundation assets, or campaigns predating the Insights Manager), the marker is
    stripped to nothing — existing assets render exactly as before. The read is
    fidelity-to-the-insight, ADVISORY only — never a gate, never blocks an asset."""
    if RESONANCE_MARKER not in markdown_text:
        return markdown_text
    if yaml is None:
        return markdown_text.replace(RESONANCE_MARKER, "")
    yaml_path = asset_dir / "asset.yaml"
    if not yaml_path.exists():
        return markdown_text.replace(RESONANCE_MARKER, "")
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return markdown_text.replace(RESONANCE_MARKER, "")
    res = data.get("resonance") if isinstance(data, dict) else None
    if not isinstance(res, dict) or not res:
        return markdown_text.replace(RESONANCE_MARKER, "")  # no read → strip

    read = str(res.get("read") or "").lower().strip().strip("'\"")
    display = RESONANCE_READ_DISPLAY.get(read, read or "(no read)")
    cls = RESONANCE_READ_CLASS.get(read, "res--unknown")

    meta_bits = []
    segment = str(res.get("segment") or "").strip()
    if segment:
        meta_bits.append(f"segment: {segment}")
    insight_ref = str(res.get("insight_ref") or "").strip()
    if insight_ref and insight_ref != "-":
        meta_bits.append(f"anchor §{insight_ref}")
    reviewed = str(res.get("reviewed") or "").strip()
    if reviewed:
        meta_bits.append(f"read {reviewed}")
    meta = (" · " + " · ".join(meta_bits)) if meta_bits else ""

    why = str(res.get("why") or "").strip()
    fix = str(res.get("fix") or "").strip()

    # A titled "On Strategy" section (rendered wherever the marker sits — by
    # convention the marker lives at the BOTTOM of the asset record, so the read
    # reads as a closing section, not a top-of-page line). Advisory, never a gate.
    parts = [
        "",
        "---",
        "",
        "### 🧭 On Strategy — resonance read",
        "",
        f'<span class="resonance-read {cls}">{display}</span>{meta}',
    ]
    if why:
        parts += ["", why]
    if fix:
        parts += ["", f"**Fix:** {fix}"]
    parts += [
        "",
        "<small>(advisory — does this asset still carry its segment's insight? "
        "a read, not a verdict; never blocks. Auto-derived from `asset.yaml` `resonance:`)</small>",
        "",
    ]
    return markdown_text.replace(RESONANCE_MARKER, "\n".join(parts))


def _set_campaign_dir(campaign_dir: Path) -> None:
    """Cache the campaign root so _build_action_link can validate file existence."""
    global _LAST_CAMPAIGN_DIR
    _LAST_CAMPAIGN_DIR = campaign_dir


def _norm_gate_id(x) -> str:
    """Normalise an asset id / gate reference to a common form so a gate list matches the
    asset folders regardless of formatting: '02' / 'A2' / 2 / '2' -> '2'; '18' -> '18'."""
    s = re.sub(r"[^0-9a-z]", "", str(x).lower())
    if s[:1] == "a":
        s = s[1:]
    return s.lstrip("0") or s or ""


def scan_campaign(campaign_dir: Path) -> list[dict]:
    """Walk every asset.yaml under campaign_dir/assets/ and collect pending operator_actions.
    Each returned dict carries the action fields plus asset_id, asset_name, asset_dir for context."""
    if yaml is None:
        return []
    assets_dir = campaign_dir / "assets"
    out: list[dict] = []
    # SYS-112 prong B — collect the set of Approved asset ids so a campaign-level gate that
    # declares `gates: [ids]` can DERIVE its completion from asset states (done when all its
    # gated assets are Approved) instead of a hand-marked status that drifts.
    approved_ids: set[str] = set()
    # An early-phase campaign (no assets/ dir yet) still has campaign-level
    # operator_actions in campaign.yaml (e.g. "pick a concept") — skip the asset walk
    # but STILL read those below, so the operator's next action always surfaces.
    for asset_folder in (sorted(assets_dir.iterdir()) if assets_dir.is_dir() else []):
        if not asset_folder.is_dir():
            continue
        m = re.match(r"^(\d+)-", asset_folder.name)
        if not m:
            continue
        asset_id = m.group(1)
        yaml_path = asset_folder / "asset.yaml"
        if not yaml_path.exists():
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if str(data.get("status") or "").strip().strip("'\"").lower() == "approved":
            approved_ids.add(_norm_gate_id(asset_id))
        actions = data.get("operator_actions") or []
        if not isinstance(actions, list):
            continue
        asset_name = str(data.get("asset_name") or asset_folder.name)
        files = data.get("files") if isinstance(data.get("files"), dict) else {}
        # Asset-level context for richer task descriptions: a one-line "what this
        # asset is" from rationale/summary.
        asset_blurb = _first_sentence(str(data.get("rationale") or data.get("summary") or ""))
        default_channel = str(data.get("default_channel") or "")
        for raw in actions:
            if not isinstance(raw, dict):
                continue
            status = str(raw.get("status") or "pending").lower()
            if status == "done":
                continue
            where = str(raw.get("where") or "")
            # "What you'll do on the page" — pull the target file's review prompt
            # so the operator knows what the (often dense) linked page asks of them.
            review_hint = ""
            if where and isinstance(files.get(where), dict):
                review_hint = str(files[where].get("review") or "")
            out.append({
                "asset_id": asset_id,
                "asset_name": asset_name,
                "asset_folder": asset_folder.name,
                "asset_blurb": asset_blurb,
                "channel": default_channel,
                "id": str(raw.get("id") or ""),
                "title": str(raw.get("title") or "(untitled action)"),
                "why": str(raw.get("why") or ""),
                "review_hint": review_hint,
                "time": str(raw.get("time") or ""),
                "where": where,
                "priority": str(raw.get("priority") or "P1"),
                "phase": str(raw.get("phase") or "4"),
                "blocks_launch": bool(raw.get("blocks_launch") or False),
            })

    # Campaign-level operator_actions (from campaign.yaml) — to-dos not tied to a
    # single asset: strategy gates, launch-infra steps, cadence checkpoints. They
    # render as styled rows alongside asset actions, marked "Campaign-level".
    camp_yaml_path = campaign_dir / "campaign.yaml"
    if camp_yaml_path.exists():
        try:
            cdata = yaml.safe_load(camp_yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            cdata = {}
        camp_actions = (cdata.get("operator_actions") or []) if isinstance(cdata, dict) else []
        for raw in camp_actions:
            if not isinstance(raw, dict):
                continue
            # SYS-112 prong B — a gate that declares `gates: [asset_ids]` DERIVES its
            # completion from asset states: done (dropped) when all its gated assets are
            # Approved, pending (surfaced) otherwise — no hand-set status to drift. An
            # action WITHOUT `gates` keeps the stored-status behaviour (external blockers
            # like "send your ABN" can't be derived).
            gates = raw.get("gates")
            if isinstance(gates, list) and gates:
                gate_ids = {_norm_gate_id(g) for g in gates if _norm_gate_id(g)}
                if gate_ids and gate_ids <= approved_ids:
                    continue  # derived DONE
                # else fall through — derived PENDING, surface it
            elif str(raw.get("status") or "pending").lower() == "done":
                continue
            out.append({
                "asset_id": "",
                "asset_name": str(raw.get("scope_label") or "Campaign-level"),
                "asset_folder": "",
                "asset_blurb": "",
                "channel": str(raw.get("channel") or ""),
                "scope": "campaign",
                "id": str(raw.get("id") or ""),
                "title": str(raw.get("title") or "(untitled action)"),
                "why": str(raw.get("why") or ""),
                "review_hint": "",
                "time": str(raw.get("time") or ""),
                "where": str(raw.get("where") or ""),
                "priority": str(raw.get("priority") or "P1"),
                "phase": str(raw.get("phase") or ""),
                "blocks_launch": bool(raw.get("blocks_launch") or False),
            })
    return out


def _first_sentence(text: str, limit: int = 160) -> str:
    """First sentence (or clause) of a blurb, capped — for compact task context."""
    t = " ".join(str(text).split())
    if not t:
        return ""
    m = re.search(r"^(.+?[.!?])(\s|$)", t)
    s = m.group(1) if m else t
    return (s[: limit - 1].rstrip() + "…") if len(s) > limit else s


def _build_action_link(action: dict) -> str:
    """Build the [open](path.html) cell content for an action row.

    Tries in order:
      1. The explicit `where` field if present (swap .md→.html for the link)
      2. `preview.html` at the asset root if it exists
      3. `<asset_folder>.html` (the asset record) if it exists
      4. The gallery anchor for that asset id

    Validation: if the constructed path doesn't resolve to a real file, marks
    the link with a (missing) suffix so the operator sees the dead link instead
    of clicking through to a 404.
    """
    # Campaign-level action (from campaign.yaml) — `where` is relative to the
    # campaign dir directly (no assets/ prefix), and may be empty (no file target).
    if action.get("scope") == "campaign":
        where = str(action.get("where") or "")
        if not where:
            return "[—](#)"
        anchor = "#" + where.split("#", 1)[1] if "#" in where else ""
        base = where.split("#")[0]
        if not base:  # pure anchor on this page
            return f"[open]({where})"
        if _LAST_CAMPAIGN_DIR is None:
            return f"[open]({where})"
        # Prefer the rendered .html; fall back to the raw file (.md cookbooks, etc.).
        html_candidate = (base[:-3] + ".html") if base.endswith(".md") else base
        if (_LAST_CAMPAIGN_DIR / html_candidate).exists():
            return f"[open]({html_candidate}{anchor})"
        if (_LAST_CAMPAIGN_DIR / base).exists():
            return f"[open]({base}{anchor})"
        return f"[open]({html_candidate}{anchor}) <small>(file missing)</small>"

    candidates: list[tuple[str, str]] = []  # (relative href, label)
    if action.get("where"):
        href = f"assets/{action['asset_folder']}/{action['where']}"
        if href.endswith(".md"):
            href = href[:-3] + ".html"
        candidates.append((href, "open"))
    candidates.append((f"assets/{action['asset_folder']}/preview.html", "preview"))
    candidates.append((f"assets/{action['asset_folder']}/{action['asset_folder']}.html", "asset"))
    candidates.append((f"gallery.html#{action['asset_id']}", "gallery"))

    if _LAST_CAMPAIGN_DIR is None:
        href, label = candidates[0]
        return f"[{label}]({href})"
    for href, label in candidates:
        abs_path = _LAST_CAMPAIGN_DIR / href.split("#")[0]
        if abs_path.exists() or "#" in href:
            return f"[{label}]({href})"
    href, label = candidates[0]
    return f"[{label}]({href}) <small>(file missing)</small>"


# Module-level state — set by scan_campaign() so _build_action_link can
# resolve relative paths against the campaign root for existence-checks.
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
_LAST_CAMPAIGN_DIR: Path | None = None
REPO_ROOT_REL = Path(".")


# Priority tiers — (sort rank, pill class, label). Shared by the per-campaign
# dashboard To Do and the cross-campaign tasks queue so they read identically.
_PRIO = {
    "blocker": (0, "pill--blocked", "🔴 Blocker"),
    "action":  (1, "pill--review",  "🟡 Action"),
    "nice":    (2, "pill--queued",  "⚪ Nice-to-have"),
}


def _action_tier(a: dict) -> str:
    if a.get("blocks_launch"):
        return "blocker"
    return "action" if str(a.get("priority") or "P1").upper() in ("P0", "P1") else "nice"


def display_num(asset_id) -> str:
    """Normalise an asset id to the ONE plan/gallery numbering convention (SYS-099):
    strip an optional 'A' prefix + leading zeros, but keep a lone zero (A0 / 00 → 0).
    So the dashboard To Do + tasks queue show '#8', matching the plan (#8) and the
    gallery (#8 / #8.1) — not the zero-padded folder prefix '#08'. Non-numeric ids
    (a rare sub-lettered '8b') pass through unchanged; empty → ''."""
    s = re.sub(r"^[Aa]", "", str(asset_id or "")).strip()
    return str(int(s)) if s.isdigit() else s


def build_action_table(actions: list, campaign_dir: "Path", link_prefix: str = "") -> str:
    """The styled To Do table — priority pill · task + asset-context · why + page-hint ·
    time · descriptive link. ONE renderer shared by the dashboard (link_prefix="",
    links relative to the campaign dir) and the cross-campaign tasks queue
    (link_prefix=f"{slug}/", links relative to campaigns/)."""
    import html as _html
    _set_campaign_dir(campaign_dir)
    rows = sorted(actions, key=lambda a: (_PRIO[_action_tier(a)][0], int(a["asset_id"] or 99)))
    body = []
    for a in rows:
        _, pcls, plabel = _PRIO[_action_tier(a)]
        link_md = _build_action_link(a)
        m = re.search(r"\]\(([^)]+)\)", link_md)
        href = m.group(1) if m else "#"
        missing = "(file missing)" in link_md
        # Prefix relative hrefs for the cross-campaign (tasks) context; dashboards pass "".
        if link_prefix and href and not href.startswith(("#", "http", "/")):
            href = link_prefix + href
        title = _html.escape(a["title"])
        if a.get("scope") == "campaign":
            # Campaign-level (gates / deploy / config) → link to the action's own
            # surface: the cookbook / guide / trio named in `where`.
            asset_ctx = "Campaign-level"
            open_cell = (f'<a href="{_html.escape(href)}">Open ↗</a>' if href and href != "#" else "—")
            if missing:
                open_cell += ' <small>(missing)</small>'
        else:
            # Asset-level (reviews / approvals) → link to the GALLERY, the operator's
            # review-and-approve surface (thumbnails · zoom · decision panels) — not the
            # dense asset record. The "On the page" hint still describes what to check.
            asset_ctx = f'#{display_num(a["asset_id"])} · {_html.escape(a["asset_name"])}'
            if a.get("channel"):
                asset_ctx += f' · {_html.escape(a["channel"])}'
            gallery_href = (link_prefix + "gallery.html") if link_prefix else "gallery.html"
            open_cell = f'<a href="{_html.escape(gallery_href)}">Review in gallery ↗</a>'
        task_cell = f'<strong>{title}</strong><div class="task-asset">{asset_ctx}</div>'
        desc = _html.escape(a["why"])
        hint_src = a.get("review_hint") or a.get("asset_blurb") or ""
        hint = _first_sentence(hint_src, 180)
        if hint:
            lbl = "On the page" if a.get("review_hint") else "What it is"
            desc += f'<div class="task-hint"><span class="task-hint__label">{lbl}:</span> {_html.escape(hint)}</div>'
        time_txt = _html.escape(a["time"])
        body.append(
            f'<tr><td><span class="pill {pcls}">{plabel}</span></td>'
            f'<td>{task_cell}</td><td>{desc}</td><td>{time_txt}</td><td>{open_cell}</td></tr>'
        )
    return (
        '<table class="task-table"><thead><tr>'
        '<th>Priority</th><th>Task</th><th>Why</th><th>Time</th><th>Open</th>'
        '</tr></thead><tbody>' + "".join(body) + '</tbody></table>'
    )


# ── Phase 5/6 plan-gate collapse ──────────────────────────────────────────────
# When a campaign has a phase-5-rollout / phase-6-cadence plan doc, THAT doc is the
# execution checklist (human-first steps + checkboxes + data-driven status). So the
# task-LIST surfaces (cross-campaign tasks + dashboard To Do) must not re-itemise the
# same Phase 5/6 launch STEPS — that's the duplication. Instead they carry ONE row per
# phase: "Approve the Phase N plan" (while the plan is in Draft). Once approved, the
# steps are tracked in the doc + the dashboard phase row. Genuine standalone decisions
# tagged to the phase (e.g. a brand-recs verdict) are NOT steps, so they stay visible.
_PHASE_PLAN_DOCS = {"5": ("phase-5-rollout", "Execute & Launch"),
                    "6": ("phase-6-cadence", "Manage & Report")}


def _phase_plan_status(campaign_dir: "Path", stem: str):
    """'draft' | 'approved' | None (no doc) — read from the doc's **Plan status** line.
    Draft is the safe default whenever the doc exists but the line is missing/ambiguous:
    an unapproved plan must never auto-suppress its own approval gate."""
    if campaign_dir is None:
        return None
    md = campaign_dir / f"{stem}.md"
    if not md.exists():
        return None
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return "draft"
    m = re.search(r"\*\*Plan status\*\*\s*:?\s*(.+)", text)
    if not m:
        return "draft"
    line = m.group(1)
    # The header template lists both halves ("🟡 Draft … / ✅ Approved …") until the
    # operator trims to just the Approved line on sign-off — so Draft wins if present.
    if "🟡" in line or re.search(r"\bdraft\b", line, re.I):
        return "draft"
    if "✅" in line or re.search(r"\bapproved\b", line, re.I):
        return "approved"
    return "draft"


def _phase_num(phase) -> "int | None":
    """Leading integer of a phase id ('1b' -> 1, '4' -> 4, '' -> None) for ordering."""
    m = re.match(r"\s*(\d+)", str(phase if phase is not None else ""))
    return int(m.group(1)) if m else None


def _current_phase_num(campaign_dir: "Path") -> "int | None":
    """Numeric id of the campaign's CURRENT phase = the first phase that isn't done.
    None when there are no phases or all are done — the caller then does not filter."""
    phases = scan_campaign_yaml(campaign_dir).get("phases") or []
    for p in phases:
        if isinstance(p, dict) and not _phase_done(p, campaign_dir):
            return _phase_num(p.get("id"))
    return None


def _active_later_phase_nums(campaign_dir: "Path") -> set:
    """Phase numbers of LATER phases the campaign is explicitly running CONCURRENTLY —
    any phase whose status is marked active/running (🚀 or the word 'ACTIVE') even though
    an earlier phase isn't fully done. A campaign can legitimately straddle two phases
    (e.g. tail-end Phase-4 production while Phase-5 launch is already live); those phases'
    tasks are genuinely in play and must show in the To Do, not be filtered as 'future'.
    Operator rule 2026-06-30 (SYS-038 refinement of SYS-031)."""
    phases = scan_campaign_yaml(campaign_dir).get("phases") or []
    out = set()
    for p in phases:
        if not isinstance(p, dict):
            continue
        s = str(p.get("status") or "")
        if "🚀" in s or re.search(r"\bactive\b", s, re.I):
            n = _phase_num(p.get("id"))
            if n is not None:
                out.add(n)
    return out


def _drop_future_phase_actions(actions: list, campaign_dir: "Path") -> list:
    """The To Do shows only what the operator must do at the stage the campaign is up to:
    drop any action whose phase is LATER than the current phase (e.g. Phase 6 cadence
    steps while still in Phase 4). Earlier-phase actions still open are KEPT (genuinely
    overdue); actions with no phase are kept; actions in an explicitly-ACTIVE later phase
    are KEPT (the campaign is running that phase concurrently). Operator rule 2026-06-30."""
    cur = _current_phase_num(campaign_dir)
    if cur is None:
        return actions
    active = _active_later_phase_nums(campaign_dir)
    kept = []
    for a in (actions or []):
        pn = _phase_num(a.get("phase"))
        if pn is not None and pn > cur and pn not in active:
            continue
        kept.append(a)
    return kept


def collapse_phase_plan_actions(actions: list, campaign_dir: "Path") -> list:
    """For task-LIST surfaces only: drop each phase's blocks_launch step-actions when
    that phase's plan doc exists (they live in the doc), and prepend ONE pointer row
    per phase that links to the doc. Returns a new list; non-step actions are left
    untouched. The dashboard's blocker COUNT (derive_blocks_launch) re-scans
    asset.yaml independently and is unaffected.

    Pointer-row shape varies by plan status:
      - draft     → "Approve the Phase N plan" (always shown — gate the operator must clear)
      - approved  → "Phase N execution tasks — click here" (shown iff that phase still has
                    open work — i.e. the doc carries unfinished steps; auto-removed when
                    every step is done, by piggy-backing on whether we dropped any rows)
    """
    gates: list = []
    kept = list(actions or [])
    for phase, (stem, label) in _PHASE_PLAN_DOCS.items():
        status = _phase_plan_status(campaign_dir, stem)
        if status is None:
            continue  # no plan doc for this phase — leave its actions alone
        phase_actions = [a for a in kept
                         if str(a.get("phase") or "") == phase and bool(a.get("blocks_launch"))]
        has_open_work = bool(phase_actions) or _phase_doc_has_open_work(campaign_dir, stem, phase)
        kept = [a for a in kept if a not in phase_actions]
        if status == "draft":
            gates.append({
                "asset_id": "", "asset_name": "Plan sign-off", "asset_folder": "",
                "asset_blurb": "", "channel": "", "scope": "campaign",
                "id": f"approve-phase-{phase}-plan",
                "title": f"Approve the Phase {phase} plan — {label}",
                "why": ("Read the steps + the gap check, send anything missing back to "
                        "Phase 4, then approve. Execution begins only after you sign off."),
                "review_hint": "", "time": "~10 min",
                "where": f"{stem}.html",
                "priority": "P0",
                "phase": phase,
                "blocks_launch": True,
            })
        elif status == "approved" and has_open_work:
            verb = "Execute & Launch" if phase == "5" else "Manage & Report"
            gates.append({
                "asset_id": "", "asset_name": f"Phase {phase} plan", "asset_folder": "",
                "asset_blurb": "", "channel": "", "scope": "campaign",
                "id": f"phase-{phase}-execute",
                "title": f"Phase {phase}: {verb} tasks to be done — click here",
                "why": ("Plan approved — execution open. Walk the steps on the plan page; "
                        "the row auto-clears when every step is complete."),
                "review_hint": "", "time": "varies",
                "where": f"{stem}.html",
                "priority": "P1",
                "phase": phase,
                "blocks_launch": True,
            })
    return gates + kept


def _phase_doc_has_open_work(campaign_dir: "Path", stem: str, phase: str) -> bool:
    """Does the phase-N plan doc still carry unfinished launch/cadence work?

    Data-driven, not checkbox-driven (checkboxes live in localStorage and are unreadable
    server-side). For Phase 5: any blocks_launch operator_action still pending across all
    asset.yamls. For Phase 6: any cadence entry in campaign.yaml not marked done.
    Returns False when the phase is genuinely complete — that's what auto-clears the
    pointer row from the dashboard To Do."""
    if campaign_dir is None:
        return False
    if phase == "5":
        try:
            for a in scan_campaign(campaign_dir):
                if a.get("blocks_launch") and str(a.get("status") or "pending").lower() != "done":
                    return True
        except Exception:
            return True  # fail-open: leave the pointer visible rather than hide work
        return False
    if phase == "6":
        try:
            data = scan_campaign_yaml(campaign_dir)
            cadence = data.get("cadence") or []
            if not isinstance(cadence, list) or not cadence:
                return False  # no schedule yet → nothing to point at
            for c in cadence:
                if isinstance(c, dict) and str(c.get("status") or "pending").lower() != "done":
                    return True
        except Exception:
            return True
        return False
    return False


def _split_rec_pointers(actions: list):
    """(table_actions, rec_pointers). Actions whose `where` targets the tenant
    Brand-recs queue (`_recommendations-queue.md`) are asset-verdict recommendations —
    durable, no time pressure — so they render as a low-key footer under a group's
    table, never as blocking task rows."""
    table, recs = [], []
    for a in (actions or []):
        (recs if "_recommendations-queue" in str(a.get("where") or "") else table).append(a)
    return table, recs


def _rec_pointer_footer(recs: list, link_prefix: str = "") -> str:
    """One muted footer line linking to the tenant recs queue (prefers the rendered
    .html). Empty string when there are no recommendation pointers."""
    if not recs:
        return ""
    import html as _html
    where = str(recs[0].get("where") or "../../tenant-brand/_recommendations-queue.md")
    href = where[:-3] + ".html" if where.endswith(".md") else where
    if link_prefix and not href.startswith(("#", "http", "/")):
        href = link_prefix + href
    return (
        '<p class="task-pointer task-pointer--rec">📋 Items queued from asset verdicts — '
        '<strong>no time pressure</strong>. '
        f'<a href="{_html.escape(href)}">See the recommendations queue ↗</a></p>'
    )


def render_actions_table_md(actions: list[dict], campaign_dir: "Path") -> str:
    """Dashboard To Do (OPERATOR_ACTIONS_AUTO) — same styled table as tasks.html."""
    actions = _drop_future_phase_actions(actions, campaign_dir)
    actions = collapse_phase_plan_actions(actions, campaign_dir)
    actions, rec_ptrs = _split_rec_pointers(actions)
    rec_footer = _rec_pointer_footer(rec_ptrs, "")

    # SYS-104 (dashboard parity) — surface assets sitting in "For Human Review" ADDITIVELY,
    # so the campaign dashboard's To Do reflects per-asset review progress the same way the
    # cross-campaign tasks.html does. Without this, the dashboard showed only the coarse
    # wave-level operator_actions and hid the fact that N assets are waiting on the operator.
    # The dashboard is ON the campaign, so the gallery link is relative.
    awaiting = sum(1 for a in scan_assets(campaign_dir)
                   if "For Human Review" in str(a.get("status_display", "")))
    review_ptr = ""
    if awaiting > 0:
        review_ptr = (
            f'\n\n<p class="task-pointer" style="margin:8px 0 0;"><strong>{awaiting} asset'
            f'{"s" if awaiting != 1 else ""} awaiting your review</strong> — '
            f'<a href="gallery.html">open the gallery to review + approve ↗</a></p>'
        )

    foot = (
        "\n\n<small>🔴 Blocker = unblocks downstream work · 🟡 Action · ⚪ Nice-to-have. "
        "Auto-generated from `operator_actions:` in each asset.yaml. "
        "Mark done: `propagate.py --campaign <slug> --asset <NN> --task <id> --done`.</small>"
    )
    if not actions:
        head = ("_No pending operator actions._" if awaiting > 0
                else "_No pending operator actions. All clear._") if not rec_ptrs else ""
        return head + review_ptr + ("\n\n" + rec_footer if rec_footer else "") + foot
    return build_action_table(actions, campaign_dir, "") + review_ptr + rec_footer + foot


def scan_assets(campaign_dir: Path) -> list[dict]:
    """Walk every asset folder and return a record per asset for the auto-derived
    Full asset list. Honest truth: actual folder numbering + actual yaml status."""
    if yaml is None:
        return []
    assets_dir = campaign_dir / "assets"
    if not assets_dir.is_dir():
        return []
    out: list[dict] = []
    for asset_folder in sorted(assets_dir.iterdir()):
        if not asset_folder.is_dir():
            continue
        m = re.match(r"^(\d+)-(.+)$", asset_folder.name)
        if not m:
            continue
        asset_id = m.group(1)
        yaml_path = asset_folder / "asset.yaml"
        yaml_status_raw = ""
        asset_name = m.group(2).replace("-", " ").title()
        if yaml_path.exists():
            try:
                data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
                if isinstance(data, dict):
                    asset_name = str(data.get("asset_name") or asset_name)
                    yaml_status_raw = str(data.get("status") or "")
            except Exception:
                pass
        artifact_class = ""
        artifact_kind = ""
        if yaml_path.exists():
            try:
                if isinstance(data, dict):
                    # `artifact_class:` is canonical; accept legacy `audience:` if present.
                    artifact_class = str(data.get("artifact_class") or "").lower().strip()
                    if not artifact_class:
                        legacy = str(data.get("audience") or "").lower().strip()
                        if legacy in ("operator", "client-marketer"):
                            artifact_class = "operational"
                        elif legacy == "marketing":
                            artifact_class = "end-audience"
                    artifact_kind = str(data.get("artifact_kind") or "").lower().strip()
            except Exception:
                pass
        status_display = STATUS_DISPLAY.get(yaml_status_raw.lower().strip().strip("'\""), yaml_status_raw or "(no status set)")
        out.append({
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_folder": asset_folder.name,
            "status_display": status_display,
            "artifact_class": artifact_class or "end-audience",  # default for untagged
            "artifact_kind": artifact_kind,
        })
    return out


# Artifact-class taxonomy — identity-silent. Operational artifacts describe
# WHAT needs to happen; WHO executes (the operator solo, client team solo, or paired)
# is a runtime decision, not a document attribute.
ARTIFACT_CLASS_GROUPS = [
    ("end-audience", "🎯 End-audience — what the consumer sees",
     "Assets the marketing surfaces ship to the audience (signup pages, bookmarks, emails, banners, social tiles, outreach copy)."),
    ("operational", "🔧 Operational — how to ship, deploy, run",
     "Deploy cookbooks, ESP wiring guides, print-partner handoff specs, runbooks, checklists. Identity-silent: could be executed solo (the operator), solo (client team), or paired — the doc doesn't care."),
]


def render_asset_list_table_md(assets: list[dict]) -> str:
    if not assets:
        return "_(no asset folders found)_"
    buckets: dict[str, list[dict]] = {k: [] for k, _, _ in ARTIFACT_CLASS_GROUPS}
    for a in assets:
        key = a.get("artifact_class") or "end-audience"
        buckets.setdefault(key, []).append(a)

    sections: list[str] = []
    for key, label, blurb in ARTIFACT_CLASS_GROUPS:
        group = buckets.get(key) or []
        if not group:
            continue
        sections.append(f"#### {label}")
        sections.append(f"_{blurb}_")
        sections.append("")
        sections.append("| # | Asset | Kind | Status | Review |")
        sections.append("|---|---|---|---|---|")
        for a in group:
            kind = f"`{a['artifact_kind']}`" if a.get("artifact_kind") else "—"
            sections.append(f"| {a['asset_id']} | {a['asset_name']} | {kind} | {a['status_display']} | [in gallery ↗](gallery.html) |")
        sections.append("")

    known = {k for k, _, _ in ARTIFACT_CLASS_GROUPS}
    other = [k for k in buckets.keys() if k not in known and buckets[k]]
    for k in other:
        sections.append(f"#### ❓ Untaxonomised: `artifact_class: {k}`")
        sections.append(f"_(Asset declared an `artifact_class:` value not in the taxonomy. Consider migrating to end-audience | operational, or extending ARTIFACT_CLASS_GROUPS in `operator_actions.py`.)_")
        sections.append("")
        sections.append("| # | Asset | Kind | Status | Review |")
        sections.append("|---|---|---|---|---|")
        for a in buckets[k]:
            kind = f"`{a['artifact_kind']}`" if a.get("artifact_kind") else "—"
            sections.append(f"| {a['asset_id']} | {a['asset_name']} | {kind} | {a['status_display']} | [in gallery ↗](gallery.html) |")
        sections.append("")

    sections.append(
        "<small>Each asset is tagged by what it's for. "
        "Two kinds: **end-audience** = what the audience sees; **operational** = how to ship/deploy/run it. "
        "WHO executes operational artifacts (you solo, the client team solo, or paired) is a runtime decision — not encoded in the doc. "
        "Open any asset in the channel-grouped **[gallery](gallery.html)**.</small>"
    )
    return "\n".join(sections)


def scan_campaign_yaml(campaign_dir: Path) -> dict:
    """Read campaign.yaml from the campaign root if present. Returns {} if missing."""
    if yaml is None:
        return {}
    path = campaign_dir / "campaign.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _any_blocks_launch_declared(campaign_dir: Path) -> bool:
    """True if ANY operator_action in ANY asset.yaml declares blocks_launch: true,
    regardless of done/pending status. Distinguishes 'all blockers complete' from
    'the blocks_launch channel was never wired for this campaign'."""
    if yaml is None:
        return False
    assets_dir = campaign_dir / "assets"
    if not assets_dir.is_dir():
        return False
    for asset_folder in assets_dir.iterdir():
        yaml_path = asset_folder / "asset.yaml"
        if not asset_folder.is_dir() or not yaml_path.exists():
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        actions = data.get("operator_actions") if isinstance(data, dict) else None
        if not isinstance(actions, list):
            continue
        for raw in actions:
            if isinstance(raw, dict) and bool(raw.get("blocks_launch")):
                return True
    return False


def _derive_phase_status(phase: dict, campaign_dir: Path) -> str:
    """Compute the phase's status display string based on `status_mode`.

    Modes:
      - explicit          : return phase['status'] verbatim (no derivation)
      - derive_assets     : count Approved vs total assets, render summary
      - derive_blocks_launch : count pending operator_actions with blocks_launch:true
      - derive_cadence    : count cadence entries with status:done vs total
    """
    mode = str(phase.get("status_mode") or "explicit").lower()
    if mode == "explicit":
        return str(phase.get("status") or "(no status)")
    if mode == "derive_assets":
        assets = scan_assets(campaign_dir)
        if not assets:
            return "(no assets)"
        total = len(assets)
        approved = sum(1 for a in assets if "Approved" in a["status_display"])
        if approved == total:
            return f"✅ All {total} produced assets Approved"
        return f"🔄 {approved} of {total} produced assets Approved"
    if mode == "derive_blocks_launch":
        actions = scan_campaign(campaign_dir)
        blockers = [a for a in actions if a["blocks_launch"]]
        if blockers:
            return f"🔄 {len(blockers)} launch blocker(s) pending"
        # Zero pending blockers is ambiguous: either all launch work is done,
        # or no asset.yaml ever declared a blocks_launch action and the launch
        # tasks live only in the dashboard To Do markdown (unwired input).
        # Claiming "✅ complete" on an unwired input is a lie — caught live
        # 2026-06-09: D1-D5 deploy tasks open while this row said complete.
        if _any_blocks_launch_declared(campaign_dir):
            return "✅ All launch blockers complete"
        return "⚠ no blocks_launch actions declared in any asset.yaml — use status_mode: explicit, or declare operator_actions with blocks_launch: true"
    if mode == "derive_cadence":
        data = scan_campaign_yaml(campaign_dir)
        cadence = data.get("cadence") or []
        if not isinstance(cadence, list) or not cadence:
            return "⏳ Queued post-launch"
        total = len(cadence)
        done = sum(1 for c in cadence if isinstance(c, dict) and str(c.get("status") or "").lower() == "done")
        if done == 0:
            return f"⏳ {total} cadence checkpoint(s) queued"
        if done == total:
            return f"✅ All {total} cadence checkpoint(s) complete"
        return f"🔄 {done} of {total} cadence checkpoint(s) complete"
    return "(unknown status_mode)"


def scan_phase_artifacts(campaign_dir: Path, phase_id) -> list[dict]:
    """Auto-discover operational artifacts (files tagged with `phase:` in each
    asset.yaml) for a given phase id. Two ways an artifact can be tagged:

      (a) Asset-level: top-level `artifact_class: operational` + `phase: N` →
          asset's primary_doc file is auto-included for phase N.
      (b) Per-file: any entry inside `files:` block with `phase: N` →
          lets marketing assets (#15 banners) declare their operational sub-files
          (upload cookbooks) without changing the asset's primary class.
    """
    out: list[dict] = []
    if yaml is None:
        return out
    assets_dir = campaign_dir / "assets"
    if not assets_dir.is_dir():
        return out
    try:
        phase_int = int(phase_id)
    except (TypeError, ValueError):
        return out
    seen: set[str] = set()
    for asset_folder in sorted(assets_dir.iterdir()):
        if not asset_folder.is_dir():
            continue
        m = re.match(r"^(\d+)-", asset_folder.name)
        if not m:
            continue
        asset_id = m.group(1)
        yaml_path = asset_folder / "asset.yaml"
        if not yaml_path.exists():
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        files = data.get("files") if isinstance(data.get("files"), dict) else {}
        try:
            asset_phase_int = int(data.get("phase")) if data.get("phase") is not None else None
        except (TypeError, ValueError):
            asset_phase_int = None
        # (a) Asset-level operational + matching phase → primary_doc
        if data.get("artifact_class") == "operational" and asset_phase_int == phase_int:
            primary_path = None
            primary_title = None
            for fp, meta in files.items():
                if isinstance(meta, dict) and meta.get("role") == "primary_doc":
                    primary_path = fp
                    primary_title = meta.get("title")
                    break
            if not primary_path:
                for cand in ("cookbook.md", "runbook.md", "deploy.md"):
                    if cand in files:
                        primary_path = cand
                        primary_title = files[cand].get("title") if isinstance(files.get(cand), dict) else None
                        break
            if not primary_path and files:
                primary_path = next(iter(files.keys()))
            if primary_path:
                href = f"assets/{asset_folder.name}/{primary_path}".replace(".md", ".html")
                if href not in seen:
                    seen.add(href)
                    title = primary_title or data.get("asset_name") or asset_folder.name
                    out.append({"title": f"#{asset_id} {title}", "href": href})
        # (b) Per-file phase declarations
        for fp, meta in files.items():
            if not isinstance(meta, dict):
                continue
            try:
                file_phase_int = int(meta.get("phase")) if meta.get("phase") is not None else None
            except (TypeError, ValueError):
                file_phase_int = None
            if file_phase_int != phase_int:
                continue
            href = f"assets/{asset_folder.name}/{fp}".replace(".md", ".html")
            if href in seen:
                continue
            seen.add(href)
            title = meta.get("title") or fp
            out.append({"title": f"#{asset_id} {title}", "href": href})
    return out


_HT_RE = re.compile(r"~?\s*(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes)\b", re.I)


def human_time_total(markdown_text: str) -> str:
    """SYS-082 — sum the Human Time column of the phases table. Works whether the table
    is hand-authored in the md OR the PHASES_AUTO table already injected into
    markdown_text (this runs after PHASES injection). Reads the 5th cell of 7-column
    phase rows; skips the header/Foundation/Total rows. Parses '~25 min' / '~1.5 hr'.
    Returns '**—**' if there's nothing to sum, so the row degrades cleanly."""
    total_min, found = 0.0, False
    for line in markdown_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) != 7:
            continue
        ht = cells[4]
        if "Total (to date)" in cells[0] or ht.lower() == "human time":
            continue
        m = _HT_RE.search(ht)
        if m:
            found = True
            total_min += float(m.group(1)) * (60 if m.group(2).lower().startswith("h") else 1)
    if not found:
        return "**—**"
    if total_min >= 90:
        hrs = total_min / 60
        return f"**~{int(hrs)} hr**" if hrs.is_integer() else f"**~{hrs:.1f} hr**"
    return f"**~{int(round(total_min))} min**"


def _sum_ht_minutes(s: str) -> float:
    """Sum every '~N min' / '~N.N hr' token in a free-text time string → minutes.
    Handles compound strings ('~1h 30m') by summing all matches."""
    total = 0.0
    for m in _HT_RE.finditer(s or ""):
        total += float(m.group(1)) * (60 if m.group(2).lower().startswith("h") else 1)
    return total


def _fmt_ht_minutes(total_min: float) -> str:
    """Format a minute total the SAME way human_time_total does, so the derived
    per-phase cell is re-parseable by _HT_RE and folds cleanly into the total row."""
    if total_min >= 90:
        hrs = total_min / 60
        return f"~{int(hrs)} hr" if hrs.is_integer() else f"~{hrs:.1f} hr"
    return f"~{int(round(total_min))} min"


def derive_phase_human_time(phase_id, campaign_dir: Path):
    """Per-phase human-in-the-loop time, DERIVED from the operator-action `time:`
    estimates assigned to that phase (each action already carries `time:` + `phase:`).
    The human-time analogue of ledger.phase_cost_cell — so the Human Time cell can't
    read blank while the phase still has operator actions to do (the recurring
    'human time not calculated' gap). Returns a formatted string, or None when the
    phase has no timed actions to sum."""
    try:
        cy = scan_campaign_yaml(campaign_dir)
    except Exception:  # noqa: BLE001
        return None
    pid = str(phase_id).strip()
    total, found = 0.0, False
    for a in (cy.get("operator_actions") or []):
        if not isinstance(a, dict):
            continue
        if str(a.get("phase") or "").strip() != pid:
            continue
        mins = _sum_ht_minutes(str(a.get("time") or ""))
        if mins > 0:
            found = True
            total += mins
    return _fmt_ht_minutes(total) if found else None


_PHASE_HT_BLANK = {"", "—", "-", "–", "tbd", "n/a", "na", "none"}


def _phase_human_time_cell(ph: dict, campaign_dir: Path) -> str:
    """Resolve the Human Time cell for one phase row. A hand-set value wins; a blank
    ('—' / missing) or an explicit <!-- PHASE_HUMAN_TIME:N --> marker auto-derives
    from the phase's operator-action times so it can never surface blank while the
    phase still has timed work (mirrors the ai_cost PHASE_COST marker)."""
    raw = str(ph.get("human_time") or "").strip()
    wants_derive = raw.lower() in _PHASE_HT_BLANK or "PHASE_HUMAN_TIME" in raw
    if wants_derive:
        return derive_phase_human_time(ph.get("id"), campaign_dir) or "—"
    return raw


def render_campaign_dna(campaign_dir: Path) -> str:
    """SYS-089 — the shared compact Campaign DNA header injected at the top of every artifact
    surface (Brief / Insight Brief / Concept / Plan), so each one opens on a consistent "you are
    here" anchor instead of a different crammed metadata paragraph. Rendered from campaign.yaml
    (`dna:` block + status/name) so it can't drift. The FULL DNA table lives on the dashboard;
    this is the reviewer's compact version. Renders nothing if the yaml has no `dna:` block."""
    try:
        cy = scan_campaign_yaml(campaign_dir)
    except Exception:
        return ""
    dna = cy.get("dna") or {}
    if not dna:
        return ""
    name = str(cy.get("nickname") or cy.get("campaign_name") or cy.get("slug") or "").strip()
    rows = []
    for key, label in (("objective", "Objective"), ("audience", "Audience"),
                       ("kpi", "Primary KPI")):
        if dna.get(key):
            rows.append(f"| **{label}** | {dna[key]} |")
    status = str(cy.get("status") or "").strip()
    if status:
        rows.append(f"| **Status** | {status} |")
    if not rows:
        return ""
    head = f"**🧭 {name} — Campaign DNA**\n\n" if name else "**🧭 Campaign DNA**\n\n"
    return head + "| | |\n|---|---|\n" + "\n".join(rows)


def render_phases_table_md(phases: list[dict], campaign_dir: Path) -> str:
    if not phases:
        return "_(no phases defined in campaign.yaml)_"
    lines = [
        "| Phase | Description | Status | Window | Human Time | AI Cost | Artifacts |",
        "|---|---|---|---|---|---|---|",
    ]
    # SYS-049: a dedicated Phase 0 · Foundation row, linking to the tenant's baseline
    # surface (the brand tenant foundation this campaign inherits). Shown only when the
    # tenant is known and its Phase-0 page exists — never crash the table on a lookup.
    try:
        _cy = scan_campaign_yaml(campaign_dir)
        _tslug = str(_cy.get("tenant") or "").strip()
        _repo = campaign_dir.parent.parent
        if _tslug and (_repo / "tenant-brand" / f"{_tslug}-phase0.html").exists():
            lines.append(
                "| 0 | Foundation — brand tenant baseline (inherited) | Inherited | — | — | — | "
                f"[Brand foundation](../../tenant-brand/{_tslug}-phase0.html) |"
            )
    except Exception:  # noqa: BLE001
        pass
    # SYS-030: the Artifacts column shows ONE authoritative link per phase (the primary,
    # always listed first); any other / superseded docs drop to the collapsed archive below
    # so the gate is unambiguous about what to review.
    archive: list = []  # (phase_id, phase_title, [demoted rendered artifact strings])
    for ph in phases:
        artifacts_md = ""
        # 1. Declared artifacts (campaign.yaml phases[].artifacts)
        declared = list(ph.get("artifacts") or [])
        # 2. Auto-derived artifacts (asset.yaml entries tagged phase:N)
        auto = scan_phase_artifacts(campaign_dir, ph.get("id"))
        # Dedupe by href (prefer declared title if both reference same target)
        seen_hrefs = set()
        merged: list[dict] = []
        for art in declared:
            if isinstance(art, dict):
                h = str(art.get("href") or "")
                if h:
                    seen_hrefs.add(h)
                merged.append(art)
        for art in auto:
            if art["href"] not in seen_hrefs:
                seen_hrefs.add(art["href"])
                merged.append(art)
        rendered: list = []
        for art in merged:
            if not isinstance(art, dict):
                continue
            t = str(art.get("title") or "")
            h = str(art.get("href") or "")
            if not t:
                continue
            is_link = bool(h) and not h.startswith("#") and (campaign_dir / h.split("#")[0]).exists()
            if is_link:
                cell = f"[{t}]({h})"
                # BB2 (SYS-073): also surface the markdown Source when it exists — a subtle,
                # low-prominence link so the underlying doc is reachable without cluttering the row.
                base = h.split("#")[0]
                if base.endswith(".html") and (campaign_dir / (base[:-5] + ".md")).exists():
                    cell += f' <a class="src-link" href="{base[:-5] + ".md"}" title="Open the source document">src</a>'
                rendered.append(cell)
            else:
                rendered.append(t)
        # Only the PRIMARY (first) artifact stays in the column; the rest go to the archive.
        artifacts_md = rendered[0] if rendered else ""
        if len(rendered) > 1:
            archive.append((str(ph.get("id", "")), str(ph.get("title", "")), rendered[1:]))
        status = _derive_phase_status(ph, campaign_dir)
        human_time = _phase_human_time_cell(ph, campaign_dir)
        lines.append(
            f"| {ph.get('id','')} | {ph.get('title','')} | {status} | "
            f"{ph.get('window','—')} | {human_time} | {ph.get('ai_cost','—')} | {artifacts_md or '—'} |"
        )
    lines.append("")
    lines.append(
        "<small>This table keeps itself up to date as the campaign moves through its phases.</small>"
    )
    # SYS-030 archive — earlier / supporting / superseded docs, one collapsed click below the
    # gate (so the column above carries exactly one thing to review per phase).
    if archive:
        lines.append("")
        lines.append('<details markdown="1">')
        lines.append('<summary><strong>🗂 Earlier &amp; supporting documents (by phase)</strong></summary>')
        lines.append("")
        for pid, ptitle, items in archive:
            lines.append(f"- **Phase {pid} · {ptitle}** — " + " · ".join(items))
        lines.append("")
        lines.append("</details>")
    return "\n".join(lines)


def scan_all_campaigns(campaigns_root: Path) -> list[dict]:
    """Walk every campaign folder under campaigns_root. Returns one dict per campaign with:
       slug, name, campaign_dir, assets (list from scan_assets), actions (list from scan_campaign).
    Skips folders that don't look like a campaign (missing assets/ subdir)."""
    out: list[dict] = []
    if not campaigns_root.is_dir():
        return out
    for child in sorted(campaigns_root.iterdir()):
        if not child.is_dir():
            continue
        # A campaign is defined by its campaign.yaml. Recognise early-phase campaigns
        # (Phase 1-3) that have no assets/ dir yet, so they still surface on the index /
        # tenant home / tasks. (Was: require assets/, which hid pre-production campaigns.)
        if not ((child / "campaign.yaml").is_file() or (child / "assets").is_dir()):
            continue
        camp_yaml = scan_campaign_yaml(child)
        name = str(camp_yaml.get("campaign_name") or child.name)
        out.append({
            "slug": child.name,
            "name": name,
            "campaign_dir": child,
            "campaign_yaml": camp_yaml,
            "assets": scan_assets(child),
            "actions": scan_campaign(child),
        })
    return out


def _is_done_status(status_str) -> bool:
    """Loose completion check on a raw `status:` string. Used in places that only
    ever see hand-authored explicit status strings. Phase-level done-ness uses the
    structured _phase_done() helper instead — it asks the data, not the display."""
    s = str(status_str or "")
    return ("Approved" in s) or ("✅" in s) or ("Selected" in s) or ("Complete" in s)


def _phase_done(phase: dict, campaign_dir: Path | None) -> bool:
    """Authoritative boolean: is this phase complete? Asks the data, not display strings.

    explicit            → status string starts with ✅ / equals approved-or-done
    derive_assets       → every asset Approved (and at least one exists)
    derive_blocks_launch→ zero pending blockers AND at least one was declared
    derive_cadence      → every cadence checkpoint marked done (and at least one exists)
    """
    mode = str(phase.get("status_mode") or "explicit").lower()
    if mode == "explicit":
        s = str(phase.get("status") or "").strip()
        if not s:
            return False
        if "🔄" in s or "⏳" in s or "🟡" in s or "⚠" in s or "❌" in s:
            return False
        # "inherited" = the Phase-0 foundation (established at the tenant layer) — a
        # completed, non-pending state, so the current-stage pill skips past it.
        return s.startswith("✅") or s.lower() in ("approved", "done", "complete", "selected", "inherited")
    if campaign_dir is None:
        return False  # can't derive without disk context
    if mode == "derive_assets":
        assets = scan_assets(campaign_dir)
        return bool(assets) and all("Approved" in a["status_display"] for a in assets)
    if mode == "derive_blocks_launch":
        actions = scan_campaign(campaign_dir)
        blockers = [a for a in actions if a["blocks_launch"]]
        return not blockers and _any_blocks_launch_declared(campaign_dir)
    if mode == "derive_cadence":
        data = scan_campaign_yaml(campaign_dir)
        cadence = data.get("cadence") or []
        if not isinstance(cadence, list) or not cadence:
            return False
        return all(isinstance(c, dict) and str(c.get("status") or "").lower() == "done" for c in cadence)
    return False


def _phase_pill(phases: list, total_assets: int, campaign_dir: Path | None = None) -> tuple[str, str]:
    """Shared current-stage pill (cls, text) used by the index cards + tasks groups.
    Uses the structured _phase_done() boolean rather than parsing display strings."""
    if phases:
        current = next((p for p in phases if not _phase_done(p, campaign_dir)), None)
        if current is None:
            return ("pill--approved", "Complete")
        short = str(current.get("title") or "").split("(")[0].strip()
        pid = current.get("id", "?")
        return ("pill--active", f"Phase {pid} · {short}" if short else f"Phase {pid}")
    if total_assets == 0:
        return ("pill--pending", "Setup")
    return ("pill--review", "In progress")


def render_cross_campaign_actions_md(campaigns: list[dict]) -> str:
    """Cross-campaign To Do — grouped per campaign with phase context. Itemised
    from asset.yaml operator_actions where present; a pointer row otherwise so
    every active campaign with pending work still appears (completeness)."""
    if not campaigns:
        return ("> **👋 Welcome — let's get your first campaign going.**\n>\n"
                "> You don't have any campaigns yet. Three steps to begin:\n>\n"
                "> 1. **Set up your business once** — say **“set yourself up”** in chat (this captures your brand, voice and audience).\n"
                "> 2. **Start a campaign** — say **“start a campaign”** and answer a few quick questions.\n"
                "> 3. **Review & approve** — everything appears here as web pages; you approve each step.\n>\n"
                "> First time? The [Getting Started guide](../docs/guide/getting-started.html) walks you through it.")
    import html as _html

    blocks: list[str] = []
    total_open = 0
    itemised_campaigns = 0
    pointer_campaigns = 0
    for camp in campaigns:
        camp_yaml = camp["campaign_yaml"]
        if bool(camp_yaml.get("archived")) or str(camp_yaml.get("status") or "").lower() == "archived":
            continue
        slug = camp["slug"]
        phases = camp_yaml.get("phases") or []
        actions = _drop_future_phase_actions(camp["actions"], camp["campaign_dir"])
        actions = collapse_phase_plan_actions(actions, camp["campaign_dir"])
        actions, rec_ptrs = _split_rec_pointers(actions)
        assets = camp["assets"]
        total_assets = len(assets)
        approved = sum(1 for a in assets if "Approved" in a["status_display"])
        pending_assets = total_assets - approved
        # SYS-104 — assets sitting in "For Human Review" are waiting on the OPERATOR
        # specifically (distinct from "In Production", which is still the machine's turn).
        # This count must surface even when the campaign ALSO has coarse, wave-level
        # operator_actions, or per-asset review progress is invisible in the queue.
        awaiting_review = sum(1 for a in assets if "For Human Review" in a["status_display"])
        pill_cls, pill_txt = _phase_pill(phases, total_assets, camp["campaign_dir"])
        disp = _html.escape(str(camp_yaml.get("nickname") or camp["name"]))
        dash = f"{slug}/dashboard.html"

        # Skip campaigns with nothing for the operator (no actions, no recs, nothing pending).
        if not actions and not rec_ptrs and pending_assets <= 0:
            continue

        header = (
            '<summary class="task-group__head">'
            f'<span class="task-group__name">{disp}</span>'
            f'<span class="pill {pill_cls}">{_html.escape(pill_txt)}</span>'
            f'<a class="task-group__dash" href="{_html.escape(dash)}" '
            'onclick="event.stopPropagation()">Dashboard ↗</a>'
            '</summary>'
        )

        # Footer pointer to the tenant Brand-recs queue — sits at the BOTTOM of the
        # group, below the actionable rows (asset-verdict items, no time pressure).
        rec_footer = _rec_pointer_footer(rec_ptrs, f"{slug}/")

        # SYS-104 — a pointer to the assets currently in "For Human Review", so
        # per-asset review progress is visible whether or not the campaign also has
        # coarse operator_actions. Links to the gallery (the review + approve surface).
        review_pointer = ""
        if awaiting_review > 0:
            review_pointer = (
                f'<p class="task-pointer"><strong>{awaiting_review} asset'
                f'{"s" if awaiting_review != 1 else ""} awaiting your review</strong> — '
                f'<a href="{_html.escape(f"{slug}/gallery.html")}">open the gallery to review + approve ↗</a></p>'
            )

        if actions:
            total_open += len(actions)
            itemised_campaigns += 1
            table = build_action_table(actions, camp["campaign_dir"], f"{slug}/")
            # The review pointer is ADDITIVE here — the coarse wave gates above it no
            # longer hide the per-asset review count (the SYS-104 fix).
            blocks.append(f'<details class="task-group" open>{header}{table}{review_pointer}{rec_footer}</details>')
        elif awaiting_review > 0:
            pointer_campaigns += 1
            blocks.append(
                f'<details class="task-group" open>{header}{review_pointer}{rec_footer}</details>'
            )
        elif pending_assets > 0:
            # Pending work exists but no asset is operator-gated yet (all In Production) —
            # a softer pointer so the campaign still appears (completeness).
            pointer_campaigns += 1
            blocks.append(
                f'<details class="task-group" open>{header}'
                f'<p class="task-pointer">{pending_assets} asset'
                f'{"s" if pending_assets != 1 else ""} in production (none awaiting you yet). '
                f'<a href="{_html.escape(dash)}">Open the dashboard ↗</a></p>{rec_footer}</details>'
            )
        else:
            # Only recommendation-queue pointers remain — show just the footer.
            blocks.append(f'<details class="task-group" open>{header}{rec_footer}</details>')

    if not blocks:
        return "_All clear — no pending operator actions across any active campaign._"

    parts = []
    if total_open:
        parts.append(
            f'{total_open} decision{"s" if total_open != 1 else ""} itemised below'
            f' across {itemised_campaigns} campaign{"s" if itemised_campaigns != 1 else ""}'
        )
    if pointer_campaigns:
        parts.append(
            f'{pointer_campaigns} more campaign{"s" if pointer_campaigns != 1 else ""} '
            f'{"have" if pointer_campaigns != 1 else "has"} items on {"their" if pointer_campaigns != 1 else "its"} dashboard'
        )
    summary = f'<p class="task-summary">{" · ".join(parts)}.</p>' if parts else ""
    # SYS-012 — each campaign group is a collapsible <details open>; offer a collapse/
    # expand-all control when there's more than one group (focus on one without scrolling).
    toolbar = (
        '<div class="task-tools">'
        '<button type="button" id="taskToggleAll" class="task-toggle-all" '
        'data-state="open" onclick="taskToggleAll()">Collapse all</button>'
        '</div>'
        '<script>'
        'function taskToggleAll(){'
        'var b=document.getElementById("taskToggleAll"),'
        'open=b.getAttribute("data-state")!=="closed";'
        'document.querySelectorAll("details.task-group").forEach(function(d){d.open=!open});'
        'b.setAttribute("data-state",open?"closed":"open");'
        'b.textContent=open?"Expand all":"Collapse all";}'
        '</script>'
    ) if len(blocks) > 1 else ""
    footer = (
        "<small>🔴 Blocker = unblocks downstream work · 🟡 Action · ⚪ Nice-to-have. "
        "Items update automatically as work progresses. "
        "Phase 5/6 launch steps live in each campaign's plan doc (Execute &amp; Launch · Manage &amp; Report) — "
        "this list carries only the plan-approval gate. "
        "Mark done: `python .claude/skills/status-propagator/propagate.py --campaign <slug> --asset <NN> --task <id> --done`.</small>"
    )
    middle = (toolbar + "\n\n" + "\n".join(blocks)) if toolbar else "\n".join(blocks)
    return summary + "\n\n" + middle + "\n\n" + footer


def _tenant_meta(repo_root: Path, slug: str) -> dict | None:
    """Read tenant-brand/<slug>.yaml (tenant identity). None if absent/unparseable.
    Cheap + defensive — used by the index chip + dashboard breadcrumb cross-links."""
    if not slug:
        return None
    path = repo_root / "tenant-brand" / f"{slug}.yaml"
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        return None


def _tenant_link_for_index(camp_dir: Path, camp_yaml: dict):
    """(label, href) for the owning tenant's home, relative to campaigns/index.html.
    None unless campaign.yaml declares `tenant:` AND the tenant home exists
    (NO-RETROFIT safe — campaigns without the field are untouched)."""
    try:
        slug = str(camp_yaml.get("tenant") or "").strip()
        if not slug:
            return None
        repo_root = camp_dir.parent.parent  # campaigns/<slug> -> campaigns -> repo root
        if not (repo_root / "tenant-brand" / f"{slug}-home.html").exists():
            return None
        meta = _tenant_meta(repo_root, slug) or {}
        name = str(meta.get("nickname") or meta.get("name") or slug)
        return (f"🏢 {name}", f"../tenant-brand/{slug}-home.html")
    except (OSError, ValueError):
        return None


def _tenant_breadcrumb_md(campaign_dir: Path) -> str:
    """Breadcrumb UP from a campaign dashboard to its Tenant Home, derived from
    campaign.yaml `tenant:`. Empty string unless the field is set AND the tenant
    home exists — so existing campaigns without the field render unchanged."""
    try:
        slug = str(scan_campaign_yaml(campaign_dir).get("tenant") or "").strip()
        if not slug:
            return ""
        repo_root = campaign_dir.parent.parent
        if not (repo_root / "tenant-brand" / f"{slug}-home.html").exists():
            return ""
        meta = _tenant_meta(repo_root, slug) or {}
        name = str(meta.get("nickname") or meta.get("name") or slug)
        import html as _h
        return (f'<p class="tenant-breadcrumb">🏢 Tenant: '
                f'<a href="../../tenant-brand/{slug}-home.html">{_h.escape(name)}</a></p>')
    except (OSError, ValueError):
        return ""


def render_campaign_index_md(campaigns: list[dict]) -> str:
    """Resilient wrapper. One malformed campaign.yaml must NEVER blank the whole
    Active index — it did once (a bare-string `artifacts:` raised AttributeError, the
    cross-surface inject swallowed it, and the unprocessed marker rendered as nothing).
    On any failure, degrade to a minimal roster (name + dashboard link) and warn loudly,
    so the operator's most important surface is never silently empty."""
    if not campaigns:
        return ("> **👋 Welcome — let's get your first campaign going.**\n>\n"
                "> You don't have any campaigns yet. Three steps to begin:\n>\n"
                "> 1. **Set up your business once** — say **“set yourself up”** in chat (this captures your brand, voice and audience).\n"
                "> 2. **Start a campaign** — say **“start a campaign”** and answer a few quick questions.\n"
                "> 3. **Review & approve** — everything appears here as web pages; you approve each step.\n>\n"
                "> First time? The [Getting Started guide](../docs/guide/getting-started.html) walks you through it.")
    try:
        return _render_campaign_index_impl(campaigns)
    except Exception as e:  # noqa: BLE001 — degrade, never blank
        import html as _html
        import sys as _sys
        print(f"  WARN campaign index degraded ({type(e).__name__}: {e}); showing a basic "
              "roster — fix the offending campaign.yaml", file=_sys.stderr)
        rows = []
        for c in campaigns:
            c = c if isinstance(c, dict) else {}
            cy = c.get("campaign_yaml")
            cy = cy if isinstance(cy, dict) else {}
            name = _html.escape(str(cy.get("nickname") or c.get("name") or c.get("slug") or "campaign"))
            slug = _html.escape(str(c.get("slug") or ""))
            rows.append(f'<li><a href="{slug}/dashboard.html">{name}</a></li>')
        return ("> ⚠ **Some campaign data is malformed** — showing a basic roster. "
                "Check the render log for the campaign at fault.\n\n"
                "<ul>" + "".join(rows) + "</ul>")


def _render_campaign_index_impl(campaigns: list[dict]) -> str:
    """Render a roster of every campaign with derived summary stats:
       - Asset count (Approved / total)
       - Launch blockers pending
       - Cadence checkpoints pending
       - Surfaces row (dashboard, gallery)"""
    if not campaigns:
        return ("> **👋 Welcome — let's get your first campaign going.**\n>\n"
                "> You don't have any campaigns yet. Three steps to begin:\n>\n"
                "> 1. **Set up your business once** — say **“set yourself up”** in chat (this captures your brand, voice and audience).\n"
                "> 2. **Start a campaign** — say **“start a campaign”** and answer a few quick questions.\n"
                "> 3. **Review & approve** — everything appears here as web pages; you approve each step.\n>\n"
                "> First time? The [Getting Started guide](../docs/guide/getting-started.html) walks you through it.")
    import html as _html
    import posixpath
    import re as _re

    def _is_done(status_str: str) -> bool:
        s = str(status_str or "")
        return ("Approved" in s) or ("✅" in s) or ("Selected" in s)

    # Strategy GATES only — the three approved-phase outputs, in card order.
    # Brand context is NOT a gate (it's tenant context — surfaced separately as a
    # link under the pill). Operator Playbook is cross-campaign — not a card link.
    GATE_ORDER = ["Brief", "Concept", "Plan"]

    def _surface_label(href: str):
        """Map an artifact href to a label. Returns ("gate", name) for a strategy
        gate, ("context", name) for tenant context, or None to drop it."""
        h = href.lower()
        if "brief" in h:
            return ("gate", "Brief")
        if "concept" in h:
            return ("gate", "Concept")
        if "plan" in h:
            return ("gate", "Plan")
        if "tenant-brand" in h or "brand-context" in h:
            return ("context", "Brand context")
        return None  # Playbook / anchors / unknowns dropped

    active_cards: list[str] = []
    archived_rows: list[str] = []
    repo_root = next(iter(campaigns))["campaign_dir"].parent.parent  # campaigns/<slug> -> repo root (for tenant labels)
    for camp in campaigns:
        slug = camp["slug"]
        camp_dir = camp["campaign_dir"]
        assets = camp["assets"]
        actions = camp["actions"]
        camp_yaml = camp["campaign_yaml"]
        phases = camp_yaml.get("phases") or []
        cadence = camp_yaml.get("cadence") or []
        total_assets = len(assets)
        approved = sum(1 for a in assets if "Approved" in a["status_display"])
        blockers = sum(1 for a in actions if a["blocks_launch"])
        cadence_total = len(cadence) if isinstance(cadence, list) else 0
        cadence_done = sum(
            1 for c in cadence if isinstance(c, dict) and str(c.get("status") or "").lower() == "done"
        ) if isinstance(cadence, list) else 0

        # Display name: operator nickname wins; formal name shown as subtitle.
        nickname = camp_yaml.get("nickname")
        display_name = _html.escape(str(nickname or camp["name"]))
        formal_html = (
            f'<span class="camp-card__formal">{_html.escape(str(camp["name"]))}</span>'
            if nickname else ""
        )

        # ── Archived campaigns → compact row in a collapsed section, not the grid ──
        is_archived = bool(camp_yaml.get("archived")) or str(camp_yaml.get("status") or "").lower() == "archived"
        if is_archived:
            archived_rows.append(
                f'<li><a href="{slug}/dashboard.html">{display_name}</a>'
                + (f' <span class="camp-archived__formal">({_html.escape(str(camp["name"]))})</span>' if nickname else "")
                + "</li>"
            )
            continue

        # ── Top-right pill = current stage/phase (from campaign.yaml phases) ──
        # Use the shared helper so status_mode (derive_assets/blocks_launch/cadence)
        # is honored; the inline version that lived here only checked the static
        # `status` field and stuck on Phase 4 once derived phases existed.
        pill_cls, pill_txt = _phase_pill(phases, total_assets, camp_dir)

        # ── Gate links (approved phases only) + Brand context (separate) ──
        # (Tenant cross-link now lives in the per-tenant section header below, not a
        # per-card chip — campaigns are grouped under their tenant on the index.)
        gates: dict[str, str] = {}
        context_links: dict[str, str] = {}
        for p in phases:
            if not _phase_done(p, camp_dir):
                continue
            for art in (p.get("artifacts") or []):
                # Artifacts SHOULD be mappings ({title, href}); tolerate a bare string
                # (some campaign.yaml authored `artifacts: [brief.md]`) by treating it as
                # the href. Anything else is skipped — never crash the whole index on one
                # malformed entry.
                if isinstance(art, str):
                    art = {"href": art}
                elif not isinstance(art, dict):
                    continue
                href = str(art.get("href") or "")
                if not href or href.startswith("#"):
                    continue
                tagged = _surface_label(href)
                if not tagged:
                    continue
                kind, label = tagged
                resolved = posixpath.normpath(posixpath.join(slug, href))
                bucket = gates if kind == "gate" else context_links
                bucket.setdefault(label, resolved)

        # Fallback for campaigns without campaign.yaml phases: probe disk for the
        # canonical gate files so they still surface (e.g. acme-co).
        if not gates:
            probe = {
                "Brief": "brief.html",
                "Concept": "concepts/concept-trio.html",
                "Plan": "plan.html",
            }
            for label, rel in probe.items():
                if (camp_dir / rel).exists():
                    gates[label] = f"{slug}/{rel}"

        surfaces: list[tuple[str, str]] = [("📊 Dashboard", f"{slug}/dashboard.html")]
        for lbl in GATE_ORDER:
            if lbl in gates:
                surfaces.append((lbl, gates[lbl]))
        surfaces.append(("🖼 Gallery", f"{slug}/gallery.html"))
        # Phase 5 / Phase 6 rollout docs — existence-checked (only campaigns past
        # Phase 4 have them; built together at end of Phase 4).
        if (camp_dir / "phase-5-rollout.html").exists():
            surfaces.append(("🚀 Execute & Launch", f"{slug}/phase-5-rollout.html"))
        if (camp_dir / "phase-6-cadence.html").exists():
            surfaces.append(("🔄 Manage & Report", f"{slug}/phase-6-cadence.html"))
        surfaces_html = "".join(
            f'<a href="{_html.escape(href)}">{_html.escape(label)}</a>' for label, href in surfaces
        )

        # SYS-049: the "Brand" chip is now derived from the tenant (built in the tenant
        # block below) → the Phase-0 foundation page, so every card shows it consistently.
        # The artifact-derived context_links are no longer rendered here.
        context_html = ""

        # ── Stats line (asset progress demoted here; blockers/cadence) ──
        stats: list[str] = []
        if total_assets:
            stats.append(f"{approved}/{total_assets} assets approved")
        if blockers:
            stats.append(f"🚀 {blockers} launch blocker{'s' if blockers != 1 else ''}")
        if cadence_total:
            stats.append(f"⏳ {cadence_done}/{cadence_total} cadence")
        stats_html = (
            '<div class="camp-card__stats">'
            + "".join(f"<span>{_html.escape(s)}</span>" for s in stats)
            + "</div>"
        ) if stats else ""

        # Tenant label (eyebrow above the campaign name) — links to the tenant home
        # when it exists. The identity cue now that cards share one flat grid (Option A).
        _tslug = str(camp_yaml.get("tenant") or "").strip()
        tenant_eyebrow = ""
        if _tslug:
            _tm = _tenant_meta(repo_root, _tslug) or {}
            _tdisp = _html.escape(str(_tm.get("nickname") or _tm.get("name") or _tslug))
            if (repo_root / "tenant-brand" / f"{_tslug}-home.html").exists():
                tenant_eyebrow = f'<a class="camp-card__tenant" href="../tenant-brand/{_tslug}-home.html">🏢 {_tdisp}</a>'
            else:
                tenant_eyebrow = f'<span class="camp-card__tenant">🏢 {_tdisp}</span>'
            # SYS-049: "Brand" chip → the tenant's Phase-0 foundation page (the whole
            # baseline, not just the brand doc), shown next to the pill on every card.
            if (repo_root / "tenant-brand" / f"{_tslug}-phase0.html").exists():
                context_html = (
                    '<div class="camp-card__context">'
                    f'<a href="../tenant-brand/{_tslug}-phase0.html">Brand</a>'
                    '</div>'
                )

        active_cards.append(
            '<div class="camp-card">'
            '<div class="camp-card__head">'
            f'<div class="camp-card__headL">{tenant_eyebrow}<span class="camp-card__name">{display_name}</span>{formal_html}</div>'
            f'<div class="camp-card__headR"><span class="pill {pill_cls}">{_html.escape(pill_txt)}</span>{context_html}</div>'
            '</div>'
            f'{stats_html}'
            f'<div class="camp-card__surfaces">{surfaces_html}</div>'
            '</div>'
        )

    # One flat grid — all active campaigns flow side-by-side, half-width (Option A,
    # 2026-06-19). Tenant identity is the per-card eyebrow label; no per-tenant section
    # rows (those forced single-campaign tenants onto their own half-empty row).
    out_parts: list[str] = ['<div class="camp-grid">', *active_cards, "</div>", ""]
    out_parts.append(
        '<a class="index-tasks-cta" href="tasks.html">'
        '<span class="index-tasks-cta__icon">✅</span>'
        '<span class="index-tasks-cta__text"><span class="index-tasks-cta__label">View all tasks</span>'
        '<span class="index-tasks-cta__sub">every pending decision across all campaigns</span></span>'
        '<span class="index-tasks-cta__arrow">→</span></a>'
    )
    if archived_rows:
        out_parts.append("")
        out_parts.append(
            '<details class="camp-archived"><summary><strong>🗄 Archived campaigns ('
            + str(len(archived_rows)) + ")</strong></summary>\n<ul>"
            + "".join(archived_rows) + "</ul></details>"
        )
    out_parts.append("")
    out_parts.append(
        "<small>This list keeps itself up to date as your campaigns progress.</small>"
    )
    return "\n".join(out_parts)


def inject(markdown_text: str, campaign_dir: Path) -> str:
    """Replace AUTO_INJECT, ASSET_LIST, and PHASES markers with derived tables."""
    # Tenant breadcrumb (cross-link UP) — injected after the H1 on every dashboard
    # render. No marker / no md edit needed; empty (no-op) unless campaign.yaml
    # declares `tenant:` and the tenant home exists, so existing campaigns without
    # the field are untouched. Wrapped fail-safe: any error leaves the md as-is.
    try:
        _bc = _tenant_breadcrumb_md(campaign_dir)
        if _bc and "tenant-breadcrumb" not in markdown_text:
            _lines = markdown_text.split("\n")
            for _i, _ln in enumerate(_lines):
                if _ln.startswith("# "):
                    _lines.insert(_i + 1, "\n" + _bc)
                    break
            markdown_text = "\n".join(_lines)
    except Exception:
        pass
    if AUTO_INJECT_MARKER in markdown_text:
        _set_campaign_dir(campaign_dir)
        actions = scan_campaign(campaign_dir)
        markdown_text = markdown_text.replace(AUTO_INJECT_MARKER, render_actions_table_md(actions, campaign_dir))
    if ASSET_LIST_MARKER in markdown_text:
        assets = scan_assets(campaign_dir)
        markdown_text = markdown_text.replace(ASSET_LIST_MARKER, render_asset_list_table_md(assets))
    if PHASES_MARKER in markdown_text:
        campaign_data = scan_campaign_yaml(campaign_dir)
        phases = campaign_data.get("phases") or []
        markdown_text = markdown_text.replace(PHASES_MARKER, render_phases_table_md(phases, campaign_dir))
    if HUMAN_TIME_TOTAL_MARKER in markdown_text:
        # SYS-082 — Total-row human-time, summed live from campaign.yaml phases.
        markdown_text = markdown_text.replace(HUMAN_TIME_TOTAL_MARKER, human_time_total(markdown_text))
    if COST_TOTAL_MARKER in markdown_text:
        # Ledger-derived AI cost line — rendered fresh every build so it cannot
        # go stale (the hand-maintained total it replaces rotted twice).
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cost-ledger"))
            import ledger as _ledger  # type: ignore
            markdown_text = markdown_text.replace(COST_TOTAL_MARKER, _ledger.total_line(campaign_dir.name))
        except Exception as e:
            markdown_text = markdown_text.replace(
                COST_TOTAL_MARKER,
                f"<small>(cost ledger unavailable at render: {e})</small>")
    if PHASE_COST_RE.search(markdown_text):
        # Per-phase AI-cost cells (<!-- PHASE_COST:N -->) — same live-ledger
        # source as the total row, so a phase cell can't drift or read blank
        # while spend is still accruing (the "where's the $ per phase?" gap).
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cost-ledger"))
            import ledger as _ledger  # type: ignore
            markdown_text = PHASE_COST_RE.sub(
                lambda m: _ledger.phase_cost_cell(campaign_dir.name, m.group(1)), markdown_text)
        except Exception:  # noqa: BLE001
            markdown_text = PHASE_COST_RE.sub("—", markdown_text)
    return markdown_text


def inject_cross_surface(markdown_text: str, campaigns_root: Path) -> str:
    """Replace CROSS_TASKS_MARKER + CAMPAIGN_INDEX_MARKER in the cross-campaign
    md files (tasks.md, index.md). Operates one level above the per-campaign
    inject() function — scans every campaign folder rather than one."""
    if CROSS_TASKS_MARKER not in markdown_text and CAMPAIGN_INDEX_MARKER not in markdown_text:
        return markdown_text
    campaigns = scan_all_campaigns(campaigns_root)
    if CROSS_TASKS_MARKER in markdown_text:
        markdown_text = markdown_text.replace(CROSS_TASKS_MARKER, render_cross_campaign_actions_md(campaigns))
    if CAMPAIGN_INDEX_MARKER in markdown_text:
        markdown_text = markdown_text.replace(CAMPAIGN_INDEX_MARKER, render_campaign_index_md(campaigns))
    return markdown_text
