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

TEAM DEPLOYMENT (docs/specs/team-deployment.md §3). Under a multi-operator deployment the
DATA dirs live in a SEPARATE repo, cloned to a location that differs per operator — so
walking up from the running checkout no longer terminates anywhere useful. `data_root()`
therefore accepts an EXPLICIT data root, resolved first-hit-wins:

    1. the MAS_DATA_ROOT environment variable
    2. `.claude/local/config.json` -> {"data_root": "<abs path>"}  (per-machine, gitignored)
    3. the worktree -> main walk below  (unchanged; this is what a single-operator install uses)

With neither 1 nor 2 present, behaviour is byte-identical to before — so the existing
single-operator install is unaffected until someone opts in.

A CONFIGURED-BUT-BROKEN data root raises DataRootError rather than falling back. Falling
back would point DATA at the code checkout and write campaign/system data into it — the
worktree blind spot (SYS-103) in a worse form, because it would then ride a code release.

Usage:
    import sys; sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
    import repo_paths
    DATA = repo_paths.data_root(REPO_ROOT)
    campaigns = DATA / "campaigns"
"""
from __future__ import annotations
import json
import os
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


class DataRootError(RuntimeError):
    """An EXPLICIT data root was configured but cannot be used.

    Raised, never swallowed: the caller is about to read or write campaign / system /
    tenant data, and the only alternative to stopping is writing it somewhere wrong.
    """


ENV_VAR = "MAS_DATA_ROOT"
CONFIG_REL = Path(".claude") / "local" / "config.json"


def _read_config_data_root(cfg: Path):
    """`data_root` value from a per-machine config.json, or None if absent/empty.
    Raises DataRootError if the file exists but cannot be parsed — a machine that
    HAS a config and got it wrong must be told, not silently ignored."""
    if not cfg.is_file():
        return None
    try:
        raw = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DataRootError(f"{cfg} exists but is unreadable / not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise DataRootError(f"{cfg} must contain a JSON object, got {type(raw).__name__}.")
    value = raw.get("data_root")
    return (str(value), str(cfg)) if value else None


def configured_data_root(repo_root) -> Path | None:
    """The EXPLICIT data root (env var, then per-machine config), or None if unset.

    Config is looked up in the running checkout AND — when running from a worktree —
    in the main checkout, so a worktree inherits the machine's configuration instead of
    silently falling back to the single-operator walk.
    """
    p = Path(repo_root).resolve()

    found = None
    env = os.environ.get(ENV_VAR, "").strip()
    if env:
        found = (env, f"${ENV_VAR}")
    else:
        candidates = [p]
        main = _path_heuristic_main(p) or _git_main_root(p)
        if main and main != p:
            candidates.append(main)
        for root in candidates:
            found = _read_config_data_root(root / CONFIG_REL)
            if found:
                break

    if not found:
        return None

    raw, source = found
    resolved = Path(raw).expanduser()
    if not resolved.is_dir():
        raise DataRootError(
            f"{source} sets data_root to {resolved!s}, which is not an existing directory. "
            "Refusing to fall back to the code checkout — fix the path or unset it."
        )
    return resolved.resolve()


def data_root(repo_root) -> Path:
    """Canonical root for DATA dirs (campaigns/, system/, tenant-brand/, system/).

    Resolution order, first hit wins:
      1. EXPLICIT — $MAS_DATA_ROOT, else `.claude/local/config.json` `data_root`
         (team deployment: DATA is a separate repo, cloned per operator).
      2. From a worktree — the in-tree `<main>/.claude/worktrees/<name>` layout OR a
         git linked worktree anywhere on disk — the main checkout.
      3. repo_root unchanged (the main checkout, or on any git error, so behaviour
         degrades safely to the running checkout).

    With no explicit configuration this is byte-identical to the pre-team-deployment
    behaviour. A configured-but-broken root raises DataRootError instead of falling back.
    """
    p = Path(repo_root).resolve()
    explicit = configured_data_root(p)
    if explicit is not None:
        return explicit
    return _path_heuristic_main(p) or _git_main_root(p) or p
