#!/usr/bin/env python3
"""SYS-020 cadence (a) — weekly COMPETITOR / LIBRARY SCAN.

Read-only + SURFACES only. It does NOT fetch, generate, or commit anything into
the library — it SURFACES a prompt/checklist of what the operator should pull in
(new exemplars + the System1 Ad-of-the-Week) as DRAFT library entries, reports
the library's current size + freshness from tenant/library/INDEX.md, and — only
if the library has not grown in N days — files ONE deduped inbox idea so a
stalled library surfaces even if nobody is looking.

  python .claude/skills/cadences/competitor-library-scan.py

Weekly schedule (see SKILL.md for the Register-ScheduledTask command). Worktree-
aware (resolves tenant/library + system/ to the main checkout via repo_paths).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cadence_common as cc  # noqa: E402

STALE_AFTER_DAYS = 14   # if the library hasn't grown in this long, file an idea

# A short, stable checklist the operator works through with /library-add. This is
# SURFACED guidance — the cadence never acts on it.
SCAN_CHECKLIST = [
    ("System1 Ad of the Week", "Sweep the latest System1 Ad-of-the-Week pick(s) since the last scan; "
     "add the standout as a DRAFT entry via `/library-add <url>` (archive-sweep mode)."),
    ("Competitor / category exemplars", "Pull any new campaign you noticed from a tenant's competitor set or "
     "adjacent category (a launch, a brand refresh, a standout always-on play)."),
    ("Award / craft sources", "Check Cannes / D&AD / Effie / The Drum / Ads of the World for a fresh winner "
     "worth a craft reference."),
    ("Operator-spotted", "Anything you saved this week (a LinkedIn post, a landing page, an email) that "
     "belongs as a Smart/Wild exemplar."),
]


def library_count_and_last_added() -> tuple[int, str, int | None]:
    """Read tenant/library/INDEX.md → (entry-count, headline-count-text, days-since-newest-entry-file).

    Count comes from the '**N entries**' headline if present, else the number of
    table rows under the Entries section. Freshness = mtime of the newest file in
    entries/ (read-only stat — no INDEX date column to rely on)."""
    index = cc.LIBRARY_DIR / "INDEX.md"
    headline = "(INDEX.md not found)"
    count = 0
    if index.exists():
        text = index.read_text(encoding="utf-8")
        m = re.search(r"\*\*([0-9]+)\s+entries\*\*", text)
        if m:
            count = int(m.group(1))
            headline = f"{count} entries (per INDEX headline)"
        else:
            # fall back to counting entry rows (lines linking into entries/)
            count = len(re.findall(r"\]\(entries/[^)]+\)", text))
            headline = f"{count} entries (counted from INDEX table)"

    days_since: int | None = None
    entries_dir = cc.LIBRARY_DIR / "entries"
    if entries_dir.is_dir():
        files = [p for p in entries_dir.glob("*.md")]
        if files:
            newest = max(p.stat().st_mtime for p in files)
            days_since = int((datetime.now().timestamp() - newest) / 86400)
    return count, headline, days_since


def main() -> int:
    today = cc.today_str()
    count, headline, days_since = library_count_and_last_added()

    lines = [f"# Competitor / library scan — {today}", ""]
    lines.append("Read-only weekly prompt. Nothing here is fetched or committed automatically — "
                 "it SURFACES what to add as DRAFT library entries. Add via `/library-add <url>`.")
    lines += ["", "## Library status"]
    lines.append(f"- Current size: **{headline}**")
    if days_since is None:
        lines.append("- Last added: unknown (no entry files found to stat)")
    else:
        lines.append(f"- Newest entry file last modified: **{days_since} day(s) ago** "
                     f"(threshold: {STALE_AFTER_DAYS} days)")
    lines.append(f"- Library path: `{cc.LIBRARY_DIR}`")

    lines += ["", "## This week's add checklist (work through with `/library-add`)"]
    for label, detail in SCAN_CHECKLIST:
        lines.append(f"- **{label}** — {detail}")

    # Surface-only escalation: file ONE deduped idea if the library has gone stale.
    filed: list[str] = []
    if days_since is not None and days_since >= STALE_AFTER_DAYS:
        title = f"Library has not grown in {days_since} days ({count} entries) — pull new exemplars"
        filed = cc.file_new_ideas(
            [title], raised_by="competitor-library-scan", today=today,
            summary=f"The weekly library scan found the library stale for {days_since}+ days; "
                    f"add new exemplars + the System1 Ad-of-the-Week as draft entries.",
            source="cadence (competitor-library-scan)")

    if filed:
        lines += ["", "## Filed this run (deduped — triage to confirm)"]
        lines += [f"- {iid}: {title}" for iid in filed]
    else:
        lines += ["", "## Filed this run", "- None (library is fresh, or an idea was already on file)."]

    lines += ["", "## Next",
              "Pick the strongest 1-3 from the checklist and run `/library-add <url>` for each. "
              "The skill drafts the entry + cross-links + INDEX update for your approval — "
              "this cadence never writes to the library itself."]

    out = cc.write_digest("competitor-library-scan", "competitor-library-scan", lines, today)
    print("\n".join(lines))
    print(f"\n[competitor-library-scan] wrote {out}" +
          (f" · filed {len(filed)} idea(s)" if filed else " · filed 0 ideas"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
