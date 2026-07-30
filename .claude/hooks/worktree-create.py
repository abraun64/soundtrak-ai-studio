#!/usr/bin/env python3
"""WorktreeCreate hook (SYS-023) — create Claude Code session worktrees OUTSIDE the
OneDrive-synced project tree.

Why: by default Claude Code creates worktrees under <project>/.claude/worktrees/<name>.
When the project lives in OneDrive, that means every worktree (a full checkout + its git
internals) gets cloud-synced — which locks files (breaking `git worktree remove`), churns
the sync, and forces worktree-deep relative paths. This hook redirects them to a LOCAL,
non-synced path: %LOCALAPPDATA%\\claude-worktrees\\<name>.

Contract (Claude Code WorktreeCreate hook): reads {"name": "<worktree-name>"} on stdin,
creates the worktree, and echoes the worktree's absolute path on stdout (Claude Code uses
that path). Runs with cwd = the project root, so `git worktree add` targets this repo.

Activate it by pointing a WorktreeCreate hook at this script — see the SYS-023 setup note.
Inert until wired into settings; safe to ship (does nothing unless invoked as a hook).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — no/garbled stdin: fall back to a default name
        data = {}
    name = (str(data.get("name") or "session").strip() or "session")

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:  # macOS/Linux: use the XDG state dir, not a Windows AppData-shaped path
        base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    dest = Path(base) / "claude-worktrees" / name
    branch = f"claude/{name}"

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Create a worktree on a fresh branch; if the branch already exists, attach to it.
    r = subprocess.run(["git", "worktree", "add", str(dest), "-b", branch],
                       capture_output=True, text=True)
    if r.returncode != 0 and "already exists" in (r.stderr or "").lower():
        r = subprocess.run(["git", "worktree", "add", str(dest), branch],
                           capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or "git worktree add failed\n")
        return 1

    # SYS-126 — a git worktree checks out its BRANCH's committed files, so a reused/old branch
    # can lack .claude/lib/repo_paths.py. Without it the worktree's post_tool_use + Stop hooks
    # can't resolve the canonical dirs and SILENTLY rebuild nothing — the operator reviews stale
    # surfaces (the 2026-07-27 stale-worktree-hooks bug). If the new worktree is missing
    # repo_paths.py, overlay the MAIN checkout's CURRENT .claude/lib + .claude/hooks so its
    # automation matches main. ONLY when missing — never clobber a worktree that already carries
    # (possibly intentionally edited) hook code.
    try:
        if not (dest / ".claude" / "lib" / "repo_paths.py").exists():
            import shutil
            main_root = Path.cwd()   # hook cwd = the project root (main checkout)
            for sub in ((".claude", "lib"), (".claude", "hooks")):
                src = main_root.joinpath(*sub)
                dst = dest.joinpath(*sub)
                if not src.is_dir():
                    continue
                for item in src.rglob("*"):
                    if "__pycache__" in item.parts:
                        continue
                    tgt = dst / item.relative_to(src)
                    if item.is_dir():
                        tgt.mkdir(parents=True, exist_ok=True)
                    else:
                        tgt.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, tgt)
            sys.stderr.write("[worktree-create] synced current .claude/lib + .claude/hooks into "
                             "the new worktree (it lacked repo_paths.py — SYS-126)\n")
    except Exception as e:  # noqa: BLE001 — provisioning aid; never fail worktree creation on it
        sys.stderr.write(f"[worktree-create] warning: could not sync hooks/lib into worktree: {e}\n")

    print(str(dest))   # Claude Code reads the worktree path from stdout
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
