#!/usr/bin/env python3
"""Classify what KIND of install this checkout is, before anything tries to set it up.

An unprovisioned TEAM code clone and a fresh SINGLE-PERSON install look almost identical:
both have no campaigns, no tenant baseline and no system backlog. They need opposite
remedies, and applying the single-person one to a team clone does real damage:

  `Setup Studio` scaffolds campaigns/index.md and renders into it. With no data root
  configured, that lands INSIDE the pull-only code repo. The tree is then dirty, so
  system_update.py refuses every future update, and the stray campaigns/ directory makes
  the clone look like a single-person install from then on — the damage hides its own cause.

Observed live 2026-09-16: a second operator's machine, standup reported "no campaigns/
directory" and offered `Setup Studio`. Provisioning had never run.

THE DISCRIMINATOR: build_seed ships campaigns/ and tenant-brand/ (empty) in a single-person
Seed — see EMPTY_DIRS — but moves them to the DATA repo under `--profile team` — see
TEAM_DATA_PATHS. So in a team CODE clone they are ABSENT, not merely empty. Absence is the
signal; emptiness is not.

    python .claude/lib/install_state.py        # report, exit 0 ready / 1 needs action
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_REL = Path(".claude") / "local" / "config.json"

READY = "ready"
UNPROVISIONED_TEAM = "unprovisioned-team"
SINGLE_PERSON = "single-person"


def classify(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    cfg = root / CONFIG_REL
    configured = None
    if cfg.is_file():
        try:
            raw = json.loads(cfg.read_text(encoding="utf-8")).get("data_root", "")
            configured = Path(raw).resolve() if raw else None
        except (OSError, ValueError):
            configured = None

    # A configured data root that no longer exists is its own failure — louder than either
    # of the states below, because it means work is being written somewhere unexpected.
    if configured is not None and not configured.is_dir():
        return {"state": UNPROVISIONED_TEAM, "data_root": configured,
                "why": f"configured data root does not exist: {configured}",
                "fix": "python .claude/lib/provision.py --data <path to the data clone>"}

    if configured is not None and configured != root:
        return {"state": READY, "data_root": configured,
                "why": f"provisioned — data lives at {configured}", "fix": ""}

    has_data_dirs = (root / "campaigns").is_dir() or (root / "tenant-brand").is_dir()
    if has_data_dirs:
        return {"state": SINGLE_PERSON, "data_root": root,
                "why": "single-operator install — code and data are the same folder", "fix": ""}

    sibling = root.parent / "data"
    hint = f" (a sibling 'data' folder exists: {sibling})" if sibling.is_dir() else ""
    return {
        "state": UNPROVISIONED_TEAM, "data_root": None,
        "why": "team code clone that has NOT been provisioned: no campaigns/ or tenant-brand/, "
               "and no data root configured" + hint,
        "fix": "python .claude/lib/provision.py --data ../data --full",
    }


def is_unprovisioned_team(root: Path = ROOT) -> bool:
    return classify(root)["state"] == UNPROVISIONED_TEAM


def main() -> int:
    r = classify()
    print(f"install state: {r['state']}")
    print(f"  {r['why']}")
    if r["state"] == UNPROVISIONED_TEAM:
        print("\n  DO NOT run first-run setup here. It would write campaign data into the")
        print("  pull-only code repo, block every future update, and disguise the cause.")
        print(f"  Run this instead:\n    {r['fix']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
