#!/usr/bin/env python3
"""
deployment_profile — which SHAPE is this install? (SYS-028 / team-deployment.md §12)

One codebase serves two deployment shapes:

  small-business  ONE operator, local data, edit-in-place code, surfaces on disk.
                  This is what a fresh Seed is, and what the operator's master is.
  team            N operators at one organisation, DATA in a shared git repo Claude
                  drives, pinned-release code, surfaces published to SharePoint.

The toggle changes **DEFAULTS, NOT CODE** — that was the whole point of the Retro-5 §1.7
decision. Nothing here forks a code path; callers ask this module a question and get a
different default answer. That keeps the two shapes one product rather than two.

    profile: small-business | team          # config.yaml at the DATA root

THE HARD RULE: with NO config.yaml present, every accessor returns the small-business
answer, which is the behaviour the system had before this module existed. A fresh Seed and
the operator's master must be byte-identical to their pre-toggle selves. Tests assert this.

Config lives at the DATA root, not the code root, because the profile describes the
DEPLOYMENT and every operator in it must agree. (In a small-business install the two roots
are the same directory, so this is invisible there.)

Usage:
    import sys; sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
    import deployment_profile as dp
    if dp.claim_locks_enabled():
        ...

Any single axis can be overridden explicitly, so an organisation can run team defaults but
(say) keep compliance gating light:

    profile: team
    overrides:
      compliance_gating: false
"""
from __future__ import annotations
import os
from pathlib import Path

SMALL_BUSINESS = "small-business"
TEAM = "team"
VALID = (SMALL_BUSINESS, TEAM)

CONFIG_NAME = "config.yaml"
ENV_VAR = "MAS_PROFILE"          # test hook + per-machine escape hatch

# The §12 axis table, as data. Adding an axis = adding a row here plus an accessor;
# it must never mean adding an `if profile == ...` anywhere else in the codebase.
AXES: dict[str, dict[str, object]] = {
    #  axis                        small-business        team
    "multi_operator":            {SMALL_BUSINESS: False, TEAM: True},
    "claim_locks":               {SMALL_BUSINESS: False, TEAM: True},
    "attribution_required":      {SMALL_BUSINESS: False, TEAM: True},
    "shared_data_remote":        {SMALL_BUSINESS: False, TEAM: True},
    "pinned_release_updates":    {SMALL_BUSINESS: False, TEAM: True},
    "commit_generated_html":     {SMALL_BUSINESS: True,  TEAM: False},   # §10 — derived, not tracked
    "publish_to_sharepoint":     {SMALL_BUSINESS: False, TEAM: True},
    "multi_approver":            {SMALL_BUSINESS: False, TEAM: True},
    "compliance_gating":         {SMALL_BUSINESS: False, TEAM: True},
}


class ProfileError(ValueError):
    """config.yaml exists but declares something unusable.

    Raised rather than defaulted: an install that MEANT to be a team deployment and
    silently ran as single-operator would skip claim locks and attribution without
    anyone noticing — the failure mode this whole spec exists to prevent.
    """


def _data_root() -> Path:
    """The DATA root, via repo_paths when available. Falls back to this checkout so the
    module is still usable in a stripped/frozen tree (ImportError ONLY — a configured-but-
    broken data root must keep raising, per team-deployment.md §3)."""
    here = Path(__file__).resolve().parents[2]
    try:
        import repo_paths
    except ImportError:
        return here
    return repo_paths.data_root(here)


def _read_config(root: Path | None = None) -> dict:
    root = Path(root) if root is not None else _data_root()
    path = root / CONFIG_NAME
    if not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError) as exc:
        raise ProfileError(f"{path} is unreadable or not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ProfileError(f"{path} must contain a mapping, got {type(raw).__name__}.")
    return raw


def load(root: Path | None = None) -> dict:
    """Resolved config: {'profile': str, 'overrides': {axis: bool}}. Never raises for an
    ABSENT config — only for a present-but-broken one."""
    cfg = _read_config(root)

    name = os.environ.get(ENV_VAR, "").strip() or str(cfg.get("profile", "") or "").strip()
    if not name:
        name = SMALL_BUSINESS
    if name not in VALID:
        raise ProfileError(
            f"profile must be one of {', '.join(VALID)} - got {name!r}. "
            f"Fix `profile:` in {CONFIG_NAME} (or ${ENV_VAR})."
        )

    overrides = cfg.get("overrides") or {}
    if not isinstance(overrides, dict):
        raise ProfileError(f"`overrides:` in {CONFIG_NAME} must be a mapping.")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ProfileError(
            f"unknown axis in `overrides:`: {', '.join(sorted(unknown))}. "
            f"Known axes: {', '.join(sorted(AXES))}."
        )
    return {"profile": name, "overrides": {k: bool(v) for k, v in overrides.items()}}


def profile(root: Path | None = None) -> str:
    return load(root)["profile"]


def is_team(root: Path | None = None) -> bool:
    return profile(root) == TEAM


def axis(name: str, root: Path | None = None) -> bool:
    """Value of one axis for this deployment: explicit override, else profile default."""
    if name not in AXES:
        raise KeyError(f"unknown deployment axis {name!r}; known: {', '.join(sorted(AXES))}")
    cfg = load(root)
    if name in cfg["overrides"]:
        return cfg["overrides"][name]
    return bool(AXES[name][cfg["profile"]])


# Named accessors — call sites read as intent, not as config lookups.
def multi_operator(root=None) -> bool:         return axis("multi_operator", root)
def claim_locks_enabled(root=None) -> bool:    return axis("claim_locks", root)
def attribution_required(root=None) -> bool:   return axis("attribution_required", root)
def shared_data_remote(root=None) -> bool:     return axis("shared_data_remote", root)
def pinned_release_updates(root=None) -> bool: return axis("pinned_release_updates", root)
def commit_generated_html(root=None) -> bool:  return axis("commit_generated_html", root)
def publish_to_sharepoint(root=None) -> bool:  return axis("publish_to_sharepoint", root)
def multi_approver(root=None) -> bool:         return axis("multi_approver", root)
def compliance_gating(root=None) -> bool:      return axis("compliance_gating", root)


def summary(root: Path | None = None) -> str:
    cfg = load(root)
    rows = [f"deployment profile: {cfg['profile']}"]
    for name in sorted(AXES):
        val = axis(name, root)
        mark = "  (override)" if name in cfg["overrides"] else ""
        rows.append(f"  {name:24} {'on' if val else 'off'}{mark}")
    return "\n".join(rows)


if __name__ == "__main__":
    print(summary())
