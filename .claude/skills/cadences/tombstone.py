#!/usr/bin/env python3
"""SYS-144 — record a KILLED cadence finding so it stays killed.

A cadence dedupes what it files against open ideas, open tickets, and this tombstone store.
Killing an idea REMOVES it from ideas.yaml, which leaves nothing to match on — so without a
tombstone the finding returns on the very next run, and an inbox that keeps re-raising
decided items teaches the operator to skim past it. That is how a genuinely new finding
gets missed.

The System Manager TRIAGE job runs this whenever it kills an idea that has a `fingerprint:`.

  # kill: never raise this finding again
  python .claude/skills/cadences/tombstone.py --fingerprint stale-sweep:parked-assets \
      --ref IDEA-059 --reason "Belongs in the tasks queue, not the system backlog."

  # see what is currently suppressed
  python .claude/skills/cadences/tombstone.py --list

To let a finding be raised again, delete its entry from system/cadence-tombstones.yaml.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cadence_common as cc  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Record a killed cadence finding (SYS-144).")
    ap.add_argument("--fingerprint", help="stable <cadence>:<category>[:<scope>] key from the idea")
    ap.add_argument("--ref", default="", help="the IDEA id being killed (for the audit trail)")
    ap.add_argument("--reason", default="", help="one line: why it was killed")
    ap.add_argument("--list", action="store_true", help="print the suppressed fingerprints and exit")
    a = ap.parse_args(argv)

    if a.list:
        tombs = sorted(cc.load_tombstones())
        print(f"suppressed cadence findings ({len(tombs)}):")
        for f in tombs:
            print(f"  · {f}")
        if not tombs:
            print("  (none — every finding a cadence raises can be filed)")
        return 0

    if not a.fingerprint:
        print("tombstone: --fingerprint is required (or use --list)", file=sys.stderr)
        return 2
    if not a.ref:
        print("tombstone: --ref is required — a tombstone with no idea id has no audit trail",
              file=sys.stderr)
        return 2

    if cc.add_tombstone(a.fingerprint, a.ref, cc.today_str(), a.reason):
        print(f"tombstone: '{a.fingerprint}' suppressed (killed as {a.ref}). "
              f"Cadences will not raise it again.")
        return 0
    print(f"tombstone: '{a.fingerprint}' was already suppressed — nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
