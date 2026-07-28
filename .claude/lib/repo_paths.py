#!/usr/bin/env python3
"""Canonical data-root resolution across git worktrees (SYS-002).

The system repo can be checked out in two shapes:
  - MAIN checkout:     <root>/                              — has campaigns/ (a SEPARATE
                                                              gitignored repo), system/,
                                                              tenant-brand/, docs/, .claude/
  - WORKTREE checkout: <root>/.claude/worktrees/<name>/     — system CODE only; campaigns/
                                                              is NOT present (separate repo)

A worktree is for isolated work on system CODE (skills / specs / hooks). The DATA dirs
(campaigns/, system/, tenant-brand/) are canonical in the MAIN checkout. Any tool that
reads or writes DATA must resolve back to the main checkout when it happens to run from a
worktree — otherwise it sees an absent campaigns/ and silently no-ops or reports false
failures. That silent failure is the "worktree blind spot."

Rule of thumb for callers:
  - CODE paths (render.py, build scripts, templates, hooks): use the running checkout's
    own root — you want the code you're editing.
  - DATA paths (campaigns/, system/, tenant-brand/): use data_root() — always the main
    checkout, whichever checkout you're running from.

Usage:
    import sys; sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
    import repo_paths
    DATA = repo_paths.data_root(REPO_ROOT)
    campaigns = DATA / "campaigns"
"""
from __future__ import annotations
import subprocess
from pathlib import Path


def _path_heuristic_main(p: Path) -> Path | None:
    """Main checkout via the in-tree `<main>/.claude/worktrees/<name>` layout.
    Returns the main root, or None if `p` isn't under such a path."""
    parts = p.parts
    for i in range(len(parts) - 1):
        if parts[i] == ".claude" and parts[i + 1] == "worktrees":
            return Path(*parts[:i]) if i > 0 else p
    return None


def _git_main_root(p: Path) -> Path | None:
    """Main working tree of a LINKED git worktree, via git — works for ANY worktree
    location (SYS-104: the WorktreeCreate hook checks worktrees out under
    %LOCALAPPDATA%\\claude-worktrees\\<name>, NOT <main>/.claude/worktrees, so the
    path heuristic alone misses them and data tools silently no-op).

    A linked worktree's common git dir is `<main>/.git` (elsewhere than `<p>/.git`);
    its parent is the main working tree. Returns None from the main checkout itself,
    a non-worktree, or on any git error (caller falls back to repo_root)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(p), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            return None
        common = Path(out.stdout.strip()).resolve()
        main = common.parent
        # Only a redirect if git points the common dir somewhere OTHER than this
        # checkout's own root — i.e. we really are a linked worktree.
        if main != p and main.exists():
            return main
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return None


def is_worktree(path) -> bool:
    """True if `path` is a linked worktree (either the in-tree
    `.claude/worktrees/<name>` layout or any git linked worktree)."""
    p = Path(path).resolve()
    return _path_heuristic_main(p) is not None or _git_main_root(p) is not None


def data_root(repo_root) -> Path:
    """Canonical root for DATA dirs (campaigns/, system/, tenant-brand/).

    From the main checkout, returns repo_root unchanged. From a worktree — whether
    the in-tree `<main>/.claude/worktrees/<name>` layout OR a git linked worktree
    anywhere on disk — returns the main checkout. Falls back to repo_root on any
    git error, so behaviour degrades safely to the running checkout.
    """
    p = Path(repo_root).resolve()
    return _path_heuristic_main(p) or _git_main_root(p) or p
