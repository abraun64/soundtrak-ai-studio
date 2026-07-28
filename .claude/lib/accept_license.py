#!/usr/bin/env python3
"""SYS-048 (part B) — first-run license acceptance gate.

A public GitHub repo can't present a click-through, so the strongest assent the tool
itself can capture is a first-run "I AGREE" gate: before the install doctor runs its
setup checks, it shows the disclaimer and refuses to proceed until the user accepts —
either interactively (types I AGREE) or with --accept-license (non-interactive). The
acceptance is recorded LOCALLY to `.claude/state/license-accepted.json` (version +
timestamp + method); that path is not shipped in the Seed, so every fresh install must
accept once. This converts "download = browse-wrap" into an affirmative act of assent
at the point of use, through any channel.

  python .claude/lib/accept_license.py                 # prompt (interactive) / block (piped)
  python .claude/lib/accept_license.py --accept-license # accept + record (scripted)
  python .claude/lib/accept_license.py --status         # show acceptance state
  python .claude/lib/accept_license.py --reset          # clear the record (re-prompt next run)

NOT legal advice; the LICENSE text it points to is DRAFT pending counsel. This module is
the mechanism; the legal wording lives in LICENSE.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[2]  # .claude/lib/ -> checkout root
RECORD_REL = Path(".claude") / "state" / "license-accepted.json"


def record_path(root: Path) -> Path:
    return root / RECORD_REL


def current_version(root: Path) -> str:
    """The latest RELEASED version from CHANGELOG (skips [Unreleased]); else 'unversioned'."""
    try:
        for line in (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines():
            m = re.match(r"##\s*\[(\d+\.\d+\.\d+)\]", line)
            if m:
                return m.group(1)
    except Exception:  # noqa: BLE001
        pass
    return "unversioned"


def is_accepted(root: Path) -> bool:
    p = record_path(root)
    if not p.exists():
        return False
    try:
        json.loads(p.read_text(encoding="utf-8"))
        return True
    except Exception:  # noqa: BLE001
        return False


def acceptance_info(root: Path) -> dict | None:
    try:
        return json.loads(record_path(root).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def record(root: Path, method: str) -> None:
    p = record_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "accepted": True,
        "version": current_version(root),
        "accepted_at": datetime.now().isoformat(timespec="seconds"),
        "method": method,
    }, indent=2), encoding="utf-8")


def disclaimer(root: Path) -> str:
    return (
        "=====================================================================\n"
        "  Soundtrak AI Studio - License & Disclaimer (please read)\n"
        "=====================================================================\n"
        "This software is provided AS IS and ENTIRELY AT YOUR OWN RISK, with no\n"
        "warranty of any kind. You assume all risk - including software bugs,\n"
        "data loss, security / cyber incidents, and AI-generated output which\n"
        "you are solely responsible for verifying before you rely on it. To the\n"
        "maximum extent permitted by law Soundtrak Consulting accepts no\n"
        "liability, and you agree to the limitation of liability and indemnity\n"
        "set out in the LICENSE (which names the parties it protects).\n"
        "\n"
        "Full terms: the LICENSE file in this folder. (DRAFT - not legal advice.)\n"
        "====================================================================="
    )


def require(root: Path, auto_accept: bool = False, interactive: bool = True) -> bool:
    """The gate. Returns True if accepted (already, via flag, or via interactive I AGREE);
    False if declined or blocked (non-interactive with no --accept-license). Silent when
    already accepted."""
    if is_accepted(root):
        return True
    print(disclaimer(root))
    if auto_accept:
        record(root, "flag")
        print("\nLicense accepted (--accept-license). Recorded to .claude/state/license-accepted.json.")
        return True
    if interactive:
        try:
            resp = input("\nType 'I AGREE' to accept these terms and continue (anything else declines): ")
        except EOFError:
            resp = ""
        if resp.strip().upper() == "I AGREE":
            record(root, "interactive")
            print("Accepted. Recorded to .claude/state/license-accepted.json.")
            return True
        print("Declined - you have not accepted the terms. Not proceeding.")
        return False
    print("\nLicense not yet accepted. If you are an assistant running setup FOR the operator:"
          " show the disclaimer above and ask them to reply 'I AGREE' in the chat, then re-run"
          " with --accept-license. Do NOT accept on their behalf. A person running this directly"
          " at a terminal can instead just type 'I AGREE' when prompted.")
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="First-run license acceptance gate (SYS-048).")
    ap.add_argument("--accept-license", action="store_true", help="accept the terms and record it (scripted)")
    ap.add_argument("--status", action="store_true", help="print current acceptance state and exit")
    ap.add_argument("--reset", action="store_true", help="clear the acceptance record (re-prompt next run)")
    ap.add_argument("--root", help="checkout root (default: inferred)")
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else ROOT_DEFAULT

    if a.status:
        info = acceptance_info(root)
        if info:
            print(f"ACCEPTED - version {info.get('version')} on {info.get('accepted_at')} "
                  f"({info.get('method')})")
        else:
            print("NOT ACCEPTED - the license has not been accepted on this install.")
        return 0
    if a.reset:
        p = record_path(root)
        if p.exists():
            p.unlink()
            print("Acceptance record cleared.")
        else:
            print("No acceptance record to clear.")
        return 0

    ok = require(root, auto_accept=a.accept_license, interactive=sys.stdin.isatty())
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
