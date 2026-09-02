#!/usr/bin/env python3
"""
large_file_guard — stop a file entering the repo that should never have been in it.

Measured on the master 2026-09-02: campaigns/ was 6.4 GB, of which 6.1 GB sat in LFS and
**90% was raw screen captures and _tmp/ intermediates that were never deliverables**. The
actual finished assets came to 673 MB. Nothing about that was a "video problem" - it was
working files being tracked because nothing said not to.

Two defences, and they do different jobs:

  1. IGNORE RULES (build_seed's .gitignore) keep the predictable cases out by convention:
     raw captures, _tmp/, node_modules. That is where the 6 GB went.
  2. THIS GUARD catches what convention misses - the one-off 300 MB export saved into an
     asset folder under a name nobody anticipated. It runs before the commit, because after
     the commit is too late: the bytes are in history, and only a rewrite removes them.

WHAT IS ACTUALLY DANGEROUS is a large file that is NOT LFS-tracked:
  - GitHub blocks any file over 100 MiB outright, so the push fails at the worst moment
  - below that it still bloats the pack for every clone, forever

A large file that IS LFS-tracked is fine in the repo (git stores a pointer) but costs LFS
quota, which scales with headcount because every operator's first clone pulls it. So that
is a WARNING, not a block - it is a budget question, not a broken push.

  python .claude/lib/large_file_guard.py <path>...   # check files or dirs
  python .claude/lib/large_file_guard.py --dirty     # check what git sees as changed

Exit 0 = nothing blocking, 1 = at least one blocking finding.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

# GitHub's own numbers (docs verified 2026-09-02): hard block at 100 MiB, warning at 50 MiB.
HARD_BLOCK = 100 * 1024 * 1024
WARN_AT = 50 * 1024 * 1024
# An LFS-tracked file is safe in the repo but costs quota; flag it far lower so a team can
# see spend coming rather than discover it in a bill.
LFS_NOTE_AT = 25 * 1024 * 1024

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def _mib(n: int) -> str:
    return f"{n / 1048576:.0f} MiB"


def _rel(p: Path, repo: Path) -> str:
    """`p` as a forward-slash path relative to `repo`.

    Must be computed the SAME way everywhere: `git check-attr` echoes back the path exactly
    as it was passed, so if the lookup key and the comparison key differ by a separator or a
    leading prefix, every file silently reads as NOT LFS-tracked - which is how this guard
    first reported 14 correctly-tracked files as blocking.
    """
    try:
        return str(p.resolve().relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def lfs_tracked(paths: list[Path], repo: Path) -> set:
    """Which of `paths` git would route through LFS, per .gitattributes."""
    if not paths:
        return set()
    rels = [_rel(p, repo) for p in paths]
    try:
        r = subprocess.run(["git", "check-attr", "filter", "--", *rels],
                           cwd=str(repo), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line.rsplit(": filter: ", 1)[0]
            for line in r.stdout.splitlines() if line.endswith(": filter: lfs")}


def collect(targets) -> list[Path]:
    out: list[Path] = []
    for raw in targets:
        p = Path(raw)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and not (SKIP_DIRS & set(f.parts)):
                    out.append(f)
        elif p.is_file():
            out.append(p)
    return out


def dirty_files(repo: Path) -> list[Path]:
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                           cwd=str(repo), capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return []
    except (OSError, subprocess.SubprocessError):
        return []
    files = []
    for line in r.stdout.splitlines():
        name = line[3:].strip().strip('"')
        if " -> " in name:                      # renames
            name = name.split(" -> ", 1)[1]
        f = repo / name
        if f.is_file():
            files.append(f)
    return files


def scan(paths: list[Path], repo: Path) -> tuple[list, list]:
    """(blocking, advisory). Blocking = big AND not LFS-tracked."""
    candidates = [p for p in paths if p.is_file() and p.stat().st_size >= LFS_NOTE_AT]
    lfs = lfs_tracked(candidates, repo)
    blocking, advisory = [], []
    for p in sorted(candidates, key=lambda x: -x.stat().st_size):
        size = p.stat().st_size
        rel = _rel(p, repo)
        is_lfs = rel in lfs
        if not is_lfs and size >= WARN_AT:
            blocking.append((size, rel, "not LFS-tracked"))
        elif is_lfs and size >= LFS_NOTE_AT:
            advisory.append((size, rel, "LFS - counts against quota"))
    return blocking, advisory


def report(blocking, advisory) -> str:
    lines = []
    if blocking:
        lines.append(f"large-file guard: {len(blocking)} file(s) too big and NOT in LFS:")
        for size, rel, _ in blocking[:20]:
            over = "  OVER GITHUB'S 100 MiB HARD LIMIT" if size >= HARD_BLOCK else ""
            lines.append(f"  {_mib(size):>9}  {rel}{over}")
        lines.append("  A file this size in plain git is downloaded by every clone, forever,")
        lines.append("  and over 100 MiB the push is refused outright.")
        lines.append("  Fix ONE of these:")
        lines.append("    - it is a working file (raw capture, export, intermediate): add it to")
        lines.append("      .gitignore. Most oversized files are this.")
        lines.append("    - it is a real deliverable: track it in LFS, then re-add it:")
        lines.append("        git lfs track \"*.<ext>\"   then   git add .gitattributes <file>")
    if advisory:
        lines.append(f"large-file guard: {len(advisory)} large LFS file(s) - quota, not a blocker:")
        for size, rel, _ in advisory[:10]:
            lines.append(f"  {_mib(size):>9}  {rel}")
        lines.append("  Fine to commit. LFS usage grows with HEADCOUNT, since every operator's")
        lines.append("  first clone pulls it - worth watching if this becomes routine.")
    return "\n".join(lines) if lines else "large-file guard: clean."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--dirty", action="store_true", help="check what git reports as changed")
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    targets = dirty_files(repo) if a.dirty else collect(a.paths)
    if not targets:
        print("large-file guard: nothing to check.")
        return 0
    blocking, advisory = scan(targets, repo)
    print(report(blocking, advisory))
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
