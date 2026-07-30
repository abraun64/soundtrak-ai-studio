#!/usr/bin/env python3
"""nav-audit — keeps docs/NAVIGATION_INDEX.md honest.

Diffs the navigation index against what's actually on disk (specs · skills · agents ·
playbooks), flags dead links and a stale "Last updated" stamp, and nudges on the docs
not touched in a while (the ones most likely to have quietly gone out of date).

Exit code: 0 = clean (green), 1 = drift found (missing index entries and/or dead links).
So a CI/smoke-test caller can gate on it.

Usage: python nav_audit.py
"""
from __future__ import annotations
import re
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .claude/skills/nav-audit/ -> repo root
# campaigns/ links live in the MAIN checkout (separate repo); resolve them against the
# canonical data root too, else a worktree run flags every campaigns/ link dead (SYS-002).
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
except Exception:
    DATA = ROOT
IDX = ROOT / "docs" / "NAVIGATION_INDEX.md"

# Categories of doc the index is expected to enumerate, with how to find them on disk.
def disk_docs() -> list[tuple[str, str, Path]]:
    items: list[tuple[str, str, Path]] = []
    for p in sorted((ROOT / "docs" / "specs").glob("*.md")):
        if p.name.upper() in ("README.MD", "INDEX.MD"):
            continue  # a folder index, not a spec (SYS-024 — categorised spec index)
        items.append(("spec", p.name, p))
    skills = ROOT / ".claude" / "skills"
    if skills.exists():
        for d in sorted(skills.iterdir()):
            if d.is_dir() and d.name != "_archive" and (d / "SKILL.md").exists():
                items.append(("skill", d.name, d / "SKILL.md"))
    agents = ROOT / ".claude" / "agents"
    if agents.exists():
        for d in sorted(agents.iterdir()):
            if d.is_dir() and d.name != "_archive" and (d / "AGENT.md").exists():
                items.append(("agent", d.name, d / "AGENT.md"))
    for p in sorted((ROOT / "docs" / "playbooks").glob("*.md")):
        items.append(("playbook", p.name, p))
    return items


def main() -> int:
    if not IDX.exists():
        print("RED: docs/NAVIGATION_INDEX.md not found"); return 1
    text = IDX.read_text(encoding="utf-8")
    items = disk_docs()

    # 1. On disk but NOT in the index (the real drift).
    missing: list[tuple[str, str]] = []
    for cat, name, _p in items:
        key = name[:-3] if name.endswith(".md") else name
        if key not in text and name not in text:
            missing.append((cat, name))

    # 2. Dead links — file paths the index names that don't exist on disk.
    refs = set(re.findall(r"`([^`]+\.md)`", text)) | set(re.findall(r"\(([^)]+\.(?:md|html|py|yaml|ps1))\)", text))
    dead: list[str] = []
    for r in refs:
        rr = r.split("#")[0].strip()
        # Skip: externals, template patterns (<slug>), and bare filenames with no path —
        # the latter are memory-rule references (memory lives OUTSIDE the repo) or section
        # labels, not repo file links.
        if not rr or rr.startswith("http") or "<" in rr or "/" not in rr:
            continue
        cands = [ROOT / rr, IDX.parent / rr, ROOT / "docs" / rr, ROOT / Path(rr).name,
                 DATA / rr, DATA / Path(rr).name]
        # .html links usually mirror a .md sibling — accept either
        alt = rr[:-5] + ".md" if rr.endswith(".html") else None
        if alt:
            cands += [ROOT / alt, IDX.parent / alt, ROOT / "docs" / alt, DATA / alt]
        if not any(c.exists() for c in cands):
            dead.append(r)

    # 3. Stale "Last updated" stamp — older than the newest indexed doc.
    m = re.search(r"Last updated\**:?\**\s*(\d{4}-\d{2}-\d{2})", text)
    stamp = m.group(1) if m else None
    newest_mtime = max((p.stat().st_mtime for _, _, p in items), default=0)
    newest_date = datetime.date.fromtimestamp(newest_mtime).isoformat() if newest_mtime else None
    stale_stamp = bool(stamp and newest_date and stamp < newest_date)

    # 4. Untouched-doc nudge — oldest 8 by mtime (review these for quiet rot).
    today = datetime.date.today()
    aged = sorted(items, key=lambda t: t[2].stat().st_mtime)[:8]

    # ---- report ----
    print("=== NAV-INDEX AUDIT ===")
    print(f"Index: docs/NAVIGATION_INDEX.md  ·  stamp: {stamp or '(none)'}  ·  newest indexed doc: {newest_date}")
    print(f"On disk: {sum(1 for i in items if i[0]=='spec')} specs · "
          f"{sum(1 for i in items if i[0]=='skill')} skills · "
          f"{sum(1 for i in items if i[0]=='agent')} agents · "
          f"{sum(1 for i in items if i[0]=='playbook')} playbooks")
    print()

    if missing:
        print(f"MISSING from index ({len(missing)}) — on disk, not referenced:")
        for cat, name in missing:
            print(f"  [{cat}] {name}")
    else:
        print("MISSING from index .......... none")
    print()

    if dead:
        print(f"DEAD links ({len(dead)}) — named in index, not found on disk:")
        for r in dead:
            print(f"  {r}")
    else:
        print("DEAD links .................. none")
    print()

    print(f"STALE stamp ................. {'YES — index older than a doc it lists; re-stamp' if stale_stamp else 'no'}")
    print()
    print("Oldest docs (review for quiet rot):")
    for cat, name, p in aged:
        days = (today - datetime.date.fromtimestamp(p.stat().st_mtime)).days
        print(f"  {days:>4}d  [{cat}] {name}")
    print()

    problems = len(missing) + len(dead)
    if problems == 0:
        print("RESULT: GREEN — index matches disk." + (" (stamp stale — re-stamp)" if stale_stamp else ""))
        return 0
    print(f"RESULT: {'AMBER' if not missing else 'RED'} — {len(missing)} missing, {len(dead)} dead link(s). Update docs/NAVIGATION_INDEX.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
