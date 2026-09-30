#!/usr/bin/env python3
"""Plan structure lint (plan spec v4, finding J) — the deterministic checks on a campaign Plan.

Four things were being checked BY EYE on a long programme, and two were caught only by accident:
dates that fell outside their wave, wave windows that did not line up, gallery channels that had
diverged from the Plan's, and a duplicate row id (S17 used twice, which silently repoints every
dependency that names it). A guard only covers what it enumerates, so these are enumerated:

  dates in order · wave windows · gallery channels match · row numbers stable

Plus the v4 structural floor: a Plan must DECLARE its Setting (Launch / Ongoing /
Launch-then-ongoing) rather than leave the renderer to guess it from wording, and every `setup` row
must carry a `Check:` a person can run.

Tables are parsed BY HEADER NAME, never by column position — the asset list has fourteen columns
and they move between versions. A table whose header cannot be recognised is REPORTED, never
skipped silently: a lint that quietly checks nothing is the failure this file exists to prevent.

Usage:
  python plan_lint.py <plan.md> [<plan.md> ...] [--quiet]     # exit 1 if any issue
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
# A window is "<start> -> <end>" with any of the dashes/arrows a human might type.
_WINDOW_SEP = re.compile(r"\s*(?:→|->|–|—|to|until)\s*", re.I)
_BLANK = {"", "-", "—", "–", "tbd", "n/a", "na", "none", "...", "…"}


def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_rule(line: str) -> bool:
    """The |---|---| separator under a markdown table header."""
    return bool(re.fullmatch(r"\|?[\s:|-]+\|?", line.strip())) and "-" in line


def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Every pipe table as (header cells, data rows). Ignores tables inside fenced code."""
    out, in_fence = [], False
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if not in_fence and ln.strip().startswith("|") and i + 1 < len(lines) and _is_rule(lines[i + 1]):
            head = _cells(ln)
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            out.append((head, rows))
            i = j
            continue
        i += 1
    return out


def _norm(h: str) -> str:
    return re.sub(r"[^a-z ]", "", h.lower()).strip()


def _find(head: list[str], *names: str) -> int | None:
    """Index of the first column whose normalised header matches any name."""
    norm = [_norm(h) for h in head]
    for n in names:
        if n in norm:
            return norm.index(n)
    for n in names:                       # substring fallback ("target date" -> "target")
        for k, h in enumerate(norm):
            if n in h:
                return k
    return None


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return row[idx].strip()


def _blank(v: str) -> bool:
    return v.strip().lower().strip("*`") in _BLANK


def _parse_window(v: str) -> tuple[str | None, str | None]:
    found = _DATE.findall(v)
    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        return found[0], None
    return None, None


def find_tables(text: str):
    """(waves_table, asset_table) — either may be None."""
    waves = assets = None
    for head, rows in tables(text):
        norm = " ".join(_norm(h) for h in head)
        if waves is None and "wave" in norm and "window" in norm:
            waves = (head, rows)
        elif assets is None and "asset" in norm and ("type" in norm or "ships" in norm):
            assets = (head, rows)
    return waves, assets


def gallery_channels(plan_path: Path) -> set[str] | None:
    """Channels declared in the campaign's gallery-config.yaml, or None if there isn't one."""
    cfg = plan_path.parent / "gallery-config.yaml"
    if not cfg.exists():
        return None
    try:
        import yaml
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return None
    chans = data.get("channels")
    if isinstance(chans, dict):
        return {str(k).strip() for k in chans}
    if isinstance(chans, list):
        out = set()
        for c in chans:
            out.add(str(c.get("name", "")).strip() if isinstance(c, dict) else str(c).strip())
        return {c for c in out if c}
    return None


def lint(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []

    # ---- v4 floor: the Setting must be DECLARED, not inferred from wording -------------------
    m = re.search(r"^\s*\**Setting\**\s*:?\s*\**\s*(Launch-then-ongoing|Launch|Ongoing)\b",
                  text, re.M | re.I)
    is_v4 = bool(re.search(r"Plan v4|spec version.*v4", text, re.I)) or m is not None
    if not m:
        issues.append("no `Setting:` declared (Launch / Ongoing / Launch-then-ongoing) — the "
                      "renderer would have to guess it from wording, which is what misfiled the "
                      "ongoing work (plan spec v4)")

    waves, assets = find_tables(text)
    if assets is None:
        issues.append("no asset-list table found (needs a header with Asset plus Type or Ships) — "
                      "REPORTING rather than passing, because a lint that checks nothing is worse "
                      "than no lint")
        return issues

    ahead, arows = assets
    i_num = _find(ahead, "")
    if i_num is None:
        i_num = 0                                    # the `#` column normalises to empty
    i_type = _find(ahead, "type")
    i_chan = _find(ahead, "channel")
    i_wave = _find(ahead, "wave")
    i_date = _find(ahead, "target date", "target", "date")
    i_deps = _find(ahead, "depends on", "depends")
    i_note = _find(ahead, "notes", "note")

    # ---- row numbers never change: no duplicates ---------------------------------------------
    seen: dict[str, int] = {}
    for n, row in enumerate(arows, 1):
        rid = _cell(row, i_num).strip("*` ")
        if not rid or _blank(rid):
            continue
        if rid in seen:
            issues.append(f"DUPLICATE row id '{rid}' (rows {seen[rid]} and {n}) — an id is a "
                          "permanent identity that dependencies and the gallery point at; retire "
                          "a removed number, never reuse it")
        else:
            seen[rid] = n

    # ---- every setup row carries a runnable Check: --------------------------------------------
    for row in arows:
        if _cell(row, i_type).lower() != "setup":
            continue
        rid = _cell(row, i_num) or "?"
        if "check:" not in _cell(row, i_note).lower():
            issues.append(f"setup row '{rid}' has no `Check:` in Notes — without a test a person "
                          "can run, it gets marked done on hope")

    # ---- wave windows + date ordering ---------------------------------------------------------
    windows: dict[str, tuple[str | None, str | None]] = {}
    if waves is None:
        if is_v4:
            issues.append("no Waves table found (needs a header with Wave and Window) — the "
                          "rollout has no windows, so dates cannot be checked against it")
    else:
        whead, wrows = waves
        j_wave = _find(whead, "wave") or 0
        j_win = _find(whead, "window")
        order: list[str] = []
        for row in wrows:
            wid = _cell(row, j_wave).strip("*` ")
            if not wid or _blank(wid):
                continue
            order.append(wid)
            start, end = _parse_window(_cell(row, j_win))
            windows[wid] = (start, end)
            if start is None:
                issues.append(f"wave '{wid}' has no dated window — a wave without a window cannot "
                              "order anything")
        # windows must not start before the previous wave's
        prev_id = prev_start = None
        for wid in order:
            start = windows.get(wid, (None, None))[0]
            if start and prev_start and start < prev_start:
                issues.append(f"wave '{wid}' starts {start}, before wave '{prev_id}' "
                              f"({prev_start}) — waves run forwards")
            if start:
                prev_id, prev_start = wid, start

        # every wave needs a row that can START it
        wave_of = {}
        for row in arows:
            rid = _cell(row, i_num).strip("*` ")
            w = _cell(row, i_wave).strip("*` ")
            if rid and w:
                wave_of[rid] = w
        for wid in order:
            rows_here = [r for r in arows if _cell(r, i_wave).strip("*` ") == wid]
            if not rows_here:
                issues.append(f"wave '{wid}' has no rows")
                continue
            openers = []
            for r in rows_here:
                deps = _cell(r, i_deps)
                if _blank(deps):
                    openers.append(r)
                    continue
                dep_ids = [d.strip(" #*`") for d in re.split(r"[,;+]", deps) if d.strip()]
                if all(wave_of.get(d, wid) != wid for d in dep_ids if d):
                    openers.append(r)
            if not openers:
                issues.append(f"wave '{wid}' has no row that can start it — every row depends on "
                              "another row in the same wave, so the wave opens blocked")

    # ---- a row's target date must sit inside its wave's window --------------------------------
    for row in arows:
        rid = _cell(row, i_num).strip("*` ") or "?"
        wid = _cell(row, i_wave).strip("*` ")
        d = _DATE.search(_cell(row, i_date))
        if not (wid and d and wid in windows):
            continue
        start, end = windows[wid]
        if start and d.group(1) < start:
            issues.append(f"row '{rid}' is dated {d.group(1)} but wave '{wid}' opens {start}")
        if end and d.group(1) > end:
            issues.append(f"row '{rid}' is dated {d.group(1)} but wave '{wid}' closes {end}")

    # ---- the Plan's channels and the gallery's must match -------------------------------------
    gal = gallery_channels(path)
    if gal is not None and i_chan is not None:
        plan_ch = {_cell(r, i_chan) for r in arows}
        plan_ch = {c for c in plan_ch if c and not _blank(c)}
        for c in sorted(plan_ch - gal):
            issues.append(f"channel '{c}' is in the Plan but not gallery-config.yaml — the gallery "
                          "derives its channels from the Plan, so this one has nowhere to land")
        for c in sorted(gal - plan_ch):
            issues.append(f"channel '{c}' is in gallery-config.yaml but no Plan row uses it")

    return issues


def main() -> int:
    files = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    if not files:
        print("usage: plan_lint.py <plan.md> [<plan.md> ...] [--quiet]")
        return 2
    total = 0
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"not found: {p}", file=sys.stderr)
            return 2
        issues = lint(p)
        total += len(issues)
        if quiet:
            continue
        if not issues:
            print(f"OK   {p.name}: structure, waves, dates, ids and channels all check out.")
        else:
            print(f"FLAG {p.name}: {len(issues)} issue(s):")
            for i in issues:
                print(f"     - {i}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
