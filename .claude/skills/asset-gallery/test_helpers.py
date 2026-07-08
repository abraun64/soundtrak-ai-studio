#!/usr/bin/env python3
"""
Regression tests for the pure helper functions in build-gallery.py.

These are the fiddly string parsers that decide the Plan<->gallery reconciliation.
They have tricky inputs (pixel dimensions, retina tags, A/S-prefixed ids) and a
history of silent mis-parses that only surfaced inside a live campaign
(e.g. `256×256` read as a 256x multiplier -> a "4290" ship-count, 2026-07-08).

Stdlib only (no pytest — it isn't installed). Run directly:
    python .claude/skills/asset-gallery/test_helpers.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this, so a change that regresses a parser goes RED
there, before it can reach a campaign. When you touch _plan_ships_count or
_normalize_asset_id, add the case that would have caught your bug here first.
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

_BG = Path(__file__).resolve().parent / "build-gallery.py"
_spec = importlib.util.spec_from_file_location("_build_gallery", _BG)
_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bg)

ships = _bg._plan_ships_count
nid = _bg._normalize_asset_id

# (input, expected) — grow this list whenever a parser bug is found.
SHIPS_CASES = [
    # The 2026-07-08 bug: pixel dimensions + @2x retina must NOT count as multipliers.
    ("256×256 icon + 512 @2x icon + 1344×256 header + 2688×512 @2x header", 4),
    ("1344×256 header", 1),
    ("256x256 icon", 1),            # ascii 'x' dimension too
    ("email header @2x", 1),        # retina tag alone
    # Genuine leading multipliers still work.
    ("2 × MP4", 2),
    ("6 PNG", 6),
    ("3 share-images", 3),
    ("3 launch tiles + 1 hub + 2 posts", 6),
    # Plain +/·-separated items.
    ("Issue + trailer", 2),
    ("Storyboard + video (MP4)", 2),
    ("Look kit + issue-header template", 2),
    ("icon + icon retina + email header + header retina", 4),
    # Single named outputs / copy-only / empty.
    ("Welcome and About copy", 1),
    ("Launch post copy", 1),
    ("1 PNG email header", 1),
    ("The production skill", 1),
    ("—", None),
    ("", None),
]

# _normalize_asset_id: A-prefixed Plan ids <-> zero-padded produced ids must match;
# S-setup ids stay distinct (the 2026-07-08 A1<->01 / A14<->14 fix).
NID_CASES = [
    ("A1", "1"), ("01", "1"),
    ("A14", "14"), ("14", "14"),
    ("A0", "0"), ("00", "0"),
    ("A9b", "9b"), ("09b", "9b"),
    ("S1", "s1"), ("S2", "s2"),     # setup ids kept distinct so they never collide with A-ids
    ("", ""), ("—", ""), ("#", ""),
]


def _run() -> int:
    fails = []
    for val, exp in SHIPS_CASES:
        got = ships(val)
        if got != exp:
            fails.append(f"  _plan_ships_count({val!r}) = {got!r}, expected {exp!r}")
    for val, exp in NID_CASES:
        got = nid(val)
        if got != exp:
            fails.append(f"  _normalize_asset_id({val!r}) = {got!r}, expected {exp!r}")
    total = len(SHIPS_CASES) + len(NID_CASES)
    if fails:
        print(f"FAIL — {len(fails)}/{total} build-gallery parser cases failed:")
        print("\n".join(fails))
        return 1
    print(f"OK — all {total} build-gallery parser cases pass.")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
