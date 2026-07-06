"""plan_model.py — the canonical parser for a Phase-3 v3 Plan asset list.

ONE source of truth for a campaign's plan model, consumed by BOTH the plan
renderer (render.py) and the asset gallery (build-gallery.py), so the two
operator surfaces can never disagree about a campaign's channels, names,
descriptions, dependency waves, or Launch/Ongoing split.

A v3 plan asset table has a header row containing '#', 'asset' (or 'item') and
'type'. `parse_plan_markdown()` returns one dict per row with a computed `wave`
(dependency tier) and `stage` (Launch / Ongoing). LEGACY plans (no `type`
column) return [] — callers fall back to their pre-v3 behaviour, so nothing
regresses.
"""
from __future__ import annotations
import re

# A row's Phase text classifies it Ongoing (the recurring engine) vs Launch
# (one-time stand-up). Kept here as the single definition both surfaces share.
STAGE_KW = ("ongoing", "cadence", "phase 6", "phase-6", "recurring",
            "weekly", "steady-state", "steady state")

STAGES = ("Launch", "Ongoing")

_CELL_DASH = ("", "—", "-", "–")


def classify_stage(phase_text: str) -> str:
    return "Ongoing" if any(k in (phase_text or "").lower() for k in STAGE_KW) else "Launch"


def parse_deps(text: str) -> list:
    """Row-id references (#N, Nb, S1, X2) out of a Depends cell."""
    return re.findall(r"#?\b([0-9]{1,3}[a-z]?|[STX][0-9]+)\b", text or "")


def compute_waves(rows: list) -> None:
    """Assign each row['wave'] = its dependency tier + 1 (topological over the
    'deps' ids). Wave 1 = nothing to wait on. A dependency cycle is broken
    defensively (the offending node is treated as a root)."""
    byid = {r["id"]: r for r in rows if r.get("id")}
    memo = {}

    def tier(rid, stack):
        if rid in memo:
            return memo[rid]
        if rid in stack:                       # cycle -> treat as a root
            memo[rid] = 0
            return 0
        r = byid.get(rid)
        if not r or not r.get("deps"):
            memo[rid] = 0
            return 0
        t = 0
        for d in r["deps"]:
            if d in byid and d != rid:
                t = max(t, tier(d, stack | {rid}) + 1)
        memo[rid] = t
        return t

    for r in rows:
        r["wave"] = (tier(r["id"], set()) + 1) if r.get("id") else None


def _split_row(line: str) -> list:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator(cells: list) -> bool:
    return all(c == "" or re.fullmatch(r":?-{2,}:?", c) for c in cells)


def parse_plan_markdown(md_text: str) -> list:
    """Parse the v3 asset table out of a plan.md string. Returns a list of row
    dicts (with `wave` + `stage`), or [] if the plan has no v3 asset table."""
    lines = md_text.splitlines()
    cols = None
    start = None
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.lower() for c in _split_row(line)]
        if "#" in cells and ("asset" in cells or "item" in cells) and "type" in cells:
            cols = {c: j for j, c in enumerate(cells)}
            start = i + 1
            break
    if cols is None:
        return []

    def col(cells, *names):
        for n in names:
            if n in cols and cols[n] < len(cells):
                return cells[cols[n]]
        return ""

    rows, seq = [], 0
    for line in lines[start:]:
        if not line.strip().startswith("|"):
            break                              # table ended
        cells = _split_row(line)
        if _is_separator(cells) or not any(cells):
            continue
        rid = col(cells, "#").lstrip("#").strip().strip("*")
        typ = col(cells, "type").lower()
        is_setup = typ.startswith("setup") or typ.startswith("task") or typ == "s"
        if rid in _CELL_DASH:
            seq += 1
            rid = f"S{seq}"
        phase = col(cells, "phase")
        rows.append({
            "id": rid,
            "is_setup": is_setup,
            "type": "setup" if is_setup else "asset",
            "name": col(cells, "asset", "item").replace("~~", "").strip(),
            "desc": col(cells, "description", "desc"),
            "channel": col(cells, "channel") or "Other",
            "ships": col(cells, "ships"),
            "review": col(cells, "review shape"),
            "form": col(cells, "form"),
            "copy_file": col(cells, "copy file"),
            "owner": col(cells, "owner agent", "owner"),
            "phase": phase,
            "target": col(cells, "target date", "target"),
            "deps": parse_deps(col(cells, "depends on", "depends", "deps")),
            "deps_text": col(cells, "depends on", "depends", "deps"),
            "notes": col(cells, "notes"),
            "stage": classify_stage(phase),
        })
    compute_waves(rows)
    return rows


def channels_in_order(rows: list) -> list:
    """Distinct channels in first-appearance (plan) order, Launch stage first."""
    seen, out = set(), []
    for stage in STAGES:
        for r in rows:
            ch = r.get("channel") or "Other"
            if r["stage"] == stage and ch not in seen:
                seen.add(ch)
                out.append(ch)
    return out


def index_by_id(rows: list) -> dict:
    """Map normalised numeric-or-token id -> row, for joining to gallery tiles.
    Keys include both the raw id ('09b', 'S1') and its leading-integer form
    ('9') so a tile folder like '09b-…' or '01-…' resolves either way."""
    out = {}
    for r in rows:
        rid = r["id"]
        out[rid] = r
        m = re.match(r"0*(\d+)", rid)
        if m:
            out.setdefault(m.group(1), r)
    return out
