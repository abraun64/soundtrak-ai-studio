#!/usr/bin/env python3
"""
next_in_calendar.py - resolve the target learning for a Debrief cycle.

Design principle (backlog L8 - two inputs, derive the rest): the operator supplies
EITHER a target learning id ("L4") OR nothing ("next in the calendar"). This script
resolves that into a single row the engine will produce. It reads two files and does
zero authoring - it just picks the row.

Reads:
  - the editorial calendar (assets/14-editorial-calendar/14-editorial-calendar.md)
    -> the running order + per-row Status column (Flagship / Banked / Queued / Placeholder)
  - the editorial backlog (assets/00-editorial-backlog/editorial-backlog.md)
    -> the full spine (started / ended / changed / learning) for the chosen learning id

Usage:
  python next_in_calendar.py                 # -> next unwritten calendar row
  python next_in_calendar.py --learning L4   # -> the row/backlog entry for L4
  python next_in_calendar.py --list          # -> print the running order + status

"Unwritten" = a calendar row whose Status is NOT one of the DONE markers
(Banked / Published / Shipped). The first such row, top to bottom, is next.

Output: a JSON object on stdout with the resolved learning id, working title,
the four-field spine, source tag, and provenance. The skill reads this and drafts
from it. It NEVER writes anything.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Force UTF-8 stdout so the JSON (which carries em-dashes / non-ASCII from the backlog
# data) survives redirection on Windows, where the default console encoding is cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Resolve the campaign root ROBUSTLY, so the script works whether it runs from its
# original home (campaigns/<slug>/assets/02-production-engine/scripts/) OR from an
# installed skill (.claude/skills/debrief-weekly-engine/scripts/). A location-relative
# parents[N] breaks the moment the script is installed elsewhere, so instead we search:
#   1) upward from this file for a dir that already holds assets/14-editorial-calendar
#      (the in-place layout), then
#   2) any repo root (up from __file__ or cwd) that holds campaigns/<slug>/ (the installed
#      layout — the engine is single-campaign, so the slug is a fixed anchor).
CAMPAIGN_SLUG = "soundtrak-ai-buildlog-2026q3"
_CAL_REL = Path("assets") / "14-editorial-calendar" / "14-editorial-calendar.md"

def _find_campaign_root() -> Path | None:
    here = Path(__file__).resolve()
    # 1) in-place: a parent that directly contains assets/14-editorial-calendar
    for p in here.parents:
        if (p / _CAL_REL).exists():
            return p
    # 2) installed: a repo root (from __file__ parents or cwd) that holds campaigns/<slug>
    bases = list(here.parents) + [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
    for base in bases:
        cand = base / "campaigns" / CAMPAIGN_SLUG
        if (cand / _CAL_REL).exists():
            return cand
    return None

CAMPAIGN_ROOT = _find_campaign_root()
if CAMPAIGN_ROOT is None:
    sys.exit(
        "ERROR: could not locate the Debrief campaign data "
        f"(campaigns/{CAMPAIGN_SLUG}/assets/14-editorial-calendar/). Run from inside the "
        "repo, or set the working directory to the repo root."
    )
CALENDAR = CAMPAIGN_ROOT / "assets" / "14-editorial-calendar" / "14-editorial-calendar.md"
BACKLOG = CAMPAIGN_ROOT / "assets" / "00-editorial-backlog" / "editorial-backlog.md"

# Status values that mean "already produced - skip it" when scanning for the next row.
DONE_MARKERS = ("banked", "published", "shipped", "live")


def read(path: Path) -> str:
    if not path.exists():
        sys.exit(f"ERROR: expected file not found: {path}")
    return path.read_text(encoding="utf-8")


def parse_calendar_rows(md: str):
    """Return the ordered list of calendar rows as dicts.

    Each data row looks like:
    | **1** ... | 1 | Tue 28 Jul | **A dozen agents became seven** | ... | 🌱 L1 | Flagship. ... |
    We key off the Source column (contains an L<N> id) and the Status column (last cell).
    """
    rows = []
    for line in md.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # header + separator rows: skip
        joined = " ".join(cells).lower()
        if not cells or "prov. date" in joined or set("".join(cells)) <= set("-: "):
            continue
        # find an L<N> id anywhere in the row (Source column)
        m = re.search(r"\bL(\d+)\b", line)
        if not m:
            continue
        learning_id = f"L{m.group(1)}"
        # number column: first cell, strip markdown emphasis + emoji
        num = re.sub(r"[^\d]", "", cells[0])
        # working title: the cell wrapped in **...** that is not the number cell
        title = None
        for c in cells[1:]:
            tm = re.search(r"\*\*(.+?)\*\*", c)
            if tm:
                title = tm.group(1).strip()
                break
        status = cells[-1]
        rows.append(
            {
                "row_number": num or None,
                "learning_id": learning_id,
                "working_title": title,
                "status": status,
            }
        )
    return rows


def parse_backlog_entry(md: str, learning_id: str):
    """Pull the four-field spine for a learning id from the backlog.

    Backlog entries look like:
    ### L4 - I started saving to OneDrive. ...
    - **Where we started**: ...
    - **Where we ended**: ...
    - **What changed**: ...
    - **The learning**: ...
    """
    # isolate the block for this id: from '### L4' up to the next '### L' or end
    pattern = re.compile(
        rf"^###\s+{re.escape(learning_id)}\b.*?(?=^###\s+L\d+\b|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(md)
    if not m:
        return None
    block = m.group(0)

    # heading line -> title after the separator dash (em-dash / en-dash / hyphen), any spacing.
    # Explicit alternation, not a character class, so the separator matches whatever the
    # backlog heading uses without depending on which dash glyph is present.
    heading = block.splitlines()[0]
    htitle = re.sub(rf"^###\s+{re.escape(learning_id)}\s*(?:—|–|-)\s*", "", heading).strip()
    # drop trailing status emoji/markers like "🆕 NEW" / "🅿️ archived draft ..."
    htitle = re.split(r"\s+🆕|\s+🅿️|\s+🔭|\s+🏦", htitle)[0].strip()

    def field(label):
        fm = re.search(
            rf"\*\*{label}\*\*\s*:?\s*(.+?)(?=\n\s*-\s*\*\*|\n###|\Z)",
            block,
            re.DOTALL,
        )
        return re.sub(r"\s+", " ", fm.group(1)).strip() if fm else None

    return {
        "learning_id": learning_id,
        "backlog_title": htitle,
        "started": field("Where we started"),
        "ended": field("Where we ended"),
        "changed": field("What changed"),
        "learning": field("The learning"),
    }


def resolve(learning_id=None, do_list=False):
    cal_md = read(CALENDAR)
    backlog_md = read(BACKLOG)
    rows = parse_calendar_rows(cal_md)

    if do_list:
        return {"running_order": rows}

    chosen = None
    if learning_id:
        learning_id = learning_id.upper()
        chosen = next((r for r in rows if r["learning_id"] == learning_id), None)
        if not chosen:
            # not on the calendar (e.g. a board learning promoted ad hoc) - still allow it
            chosen = {"row_number": None, "learning_id": learning_id,
                      "working_title": None, "status": "off-calendar (operator pick)"}
    else:
        # next unwritten row: first whose status has no DONE marker
        for r in rows:
            st = (r["status"] or "").lower()
            if not any(marker in st for marker in DONE_MARKERS):
                chosen = r
                break
        if not chosen:
            sys.exit("No unwritten calendar rows remain - every row is banked/published. "
                     "Add a row to the calendar or pass --learning to force one.")

    spine = parse_backlog_entry(backlog_md, chosen["learning_id"])
    result = {
        "resolved_from": "operator learning id" if learning_id else "next in calendar",
        "row_number": chosen.get("row_number"),
        "learning_id": chosen["learning_id"],
        "working_title": chosen.get("working_title") or (spine or {}).get("backlog_title"),
        "calendar_status": chosen.get("status"),
        "spine": spine,
        "spine_found": spine is not None,
        "notes": None if spine else (
            f"{chosen['learning_id']} is not a full backlog entry (likely a placeholder "
            f"slot 7-12 to source from the AI Learnings board). The skill must expand it "
            f"to a full spine and hold it to the two-test bar before drafting."
        ),
    }
    return result


def main():
    ap = argparse.ArgumentParser(description="Resolve the target learning for a Debrief cycle.")
    ap.add_argument("--learning", help="force a specific learning id, e.g. L4 (else: next in calendar)")
    ap.add_argument("--list", action="store_true", help="print the running order + status")
    args = ap.parse_args()
    print(json.dumps(resolve(args.learning, args.list), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
