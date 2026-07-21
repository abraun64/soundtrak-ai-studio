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
stale = _bg._copy_stale_vs_render
DRIFT_S = _bg.COPY_RENDER_DRIFT_SECONDS  # 14400 (4h) at time of writing

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


# _copy_stale_vs_render(copy_mtime, ship_mtime): True iff the shipped surface is NEWER than
# the edit-copy by more than the 4h threshold — the directional intra-asset stale-mirror
# check (the 2026-07-09 A4 bug: copy.md a day behind the reworked edition.md/issue-header).
# Copy newer than ship (the normal source-first / mid-edit order) NEVER flags; either None
# is no-signal. (copy_mtime, ship_mtime, expected).
_T = DRIFT_S
STALE_CASES = [
    (1000, 1000, False),                 # equal -> not stale
    (1000, 1000 + _T - 1, False),        # ship ahead but within window -> not stale
    (1000, 1000 + _T + 1, True),         # ship ahead past window -> STALE (A4 class)
    (1000, 1000 + 86400, True),          # ship a day ahead of copy -> STALE
    (1000 + 86400, 1000, False),         # copy AHEAD of ship (mid-edit / source-first) -> not stale
    (1000 + _T + 5, 1000, False),        # copy newer, never flags regardless of gap
    (None, 1000, False),                 # no copy mtime -> no signal
    (1000, None, False),                 # no ship mtime -> no signal
]

# The copy-staleness tripwire (asset_ship_mtime in run_check) EXEMPTS binary visual
# surfaces: a re-rendered/imported tile (.png from Canva, a Playwright PNG render) must
# not flag the article copy.md as stale. Guard the exempt/non-exempt split so it can't
# regress silently (the 2026-07-21 Canva-tile false-positive class).
EXEMPT_SUFFIX_CASES = [
    (".png", True), (".jpg", True), (".jpeg", True), (".webp", True),
    (".gif", True), (".svg", True), (".mp4", True), (".mov", True),
    (".html", False), (".md", False), (".pptx", False),   # copy-authored surfaces still trip
    (".pdf", False), (".csv", False), (".docx", False),
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
    for cm, sm, exp in STALE_CASES:
        got = stale(cm, sm)
        if got != exp:
            fails.append(f"  _copy_stale_vs_render({cm!r}, {sm!r}) = {got!r}, expected {exp!r}")
    for suffix, exp in EXEMPT_SUFFIX_CASES:
        got = suffix in _bg._COPY_SYNC_EXEMPT_SUFFIXES
        if got != exp:
            fails.append(f"  {suffix!r} in _COPY_SYNC_EXEMPT_SUFFIXES = {got!r}, expected {exp!r}")
    total = len(SHIPS_CASES) + len(NID_CASES) + len(STALE_CASES) + len(EXEMPT_SUFFIX_CASES)
    if fails:
        print(f"FAIL — {len(fails)}/{total} build-gallery parser cases failed:")
        print("\n".join(fails))
        return 1
    print(f"OK — all {total} build-gallery parser cases pass.")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
