#!/usr/bin/env python3
"""
Regression tests for build_seed's leak scan allowlist (SYS-149).

Stdlib only. Run directly:
    python .claude/lib/test_build_seed_leakscan.py

WHAT THIS PROTECTS. The leak scan is the gate between the master and anything public, so it
has two failure modes and both matter:

  TOO LAX   a real client name ships. Catastrophic, and the reason the scan exists.
  TOO NOISY it reports the licensor's own name in the licence file, on a clean tree. Not a
            shipping risk, but a scan that cries wolf is one people learn to wave through -
            and that is how a genuinely bad hit eventually gets waved through too.

SYS-149 was the noisy kind: LEGAL_LICENSOR_FILES lists the legal files by their SINGLE-repo
path, so after a team split (`code/LICENSE`, `code/docs/legal/NOTICE.md`) the allowlist
stopped matching. These tests pin the fix AND pin the laxness boundary around it, because
"strip a prefix before matching" is exactly the kind of change that quietly allowlists more
than intended.
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_seed as bs  # noqa: E402

_FAILED: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got {got!r}, want {want!r}")
        _FAILED.append(name)


def test_allowlist_paths() -> None:
    print("\nALLOWLIST resolves in BOTH deployment shapes, and no further")
    cases = [
        ("LICENSE", True, "single-repo shape"),
        ("docs/legal/NOTICE.md", True, "single-repo, nested"),
        ("code/LICENSE", True, "team shape - the SYS-149 bug"),
        ("code/docs/legal/NOTICE.md", True, "team shape, nested"),
        ("data/CONTRIBUTING.md", True, "data side of a split"),
        # The laxness boundary. Prefix-stripping must not become a wildcard.
        ("code/README.md", False, "README is not a legal file"),
        ("code/docs/specs/brief.md", False, "ordinary doc under code/"),
        ("code/code/LICENSE", False, "doubled prefix must not slip through"),
        ("mycode/LICENSE", False, "lookalike prefix must not slip through"),
        ("LICENSE.backup", False, "near-miss filename"),
        ("", False, "empty path"),
    ]
    for rel, want, why in cases:
        check(f"{rel or '(empty)'} -> {want}  ({why})", bs._is_legal_licensor_file(rel), want)


def test_scan_still_catches_what_matters() -> None:
    """The half that would be a real disaster: prove the scan can still FAIL.

    An allowlist change is only safe if the things it must never tolerate are still caught,
    so this plants them deliberately rather than asserting the happy path.
    """
    print("\nSCAN still catches what it must, in the team shape")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        (out / "code" / "docs" / "legal").mkdir(parents=True)

        # Allowed: the LICENSOR naming themselves in the licence.
        (out / "code" / "LICENSE").write_text(
            "Licensed by the operator, Soundtrak Consulting.\n", encoding="utf-8")
        # NEVER allowed anywhere, legal files included: a real client name.
        (out / "code" / "docs" / "legal" / "NOTICE.md").write_text(
            "Copyright the operator. Portions used by Beta Corp.\n", encoding="utf-8")
        # Ordinary file: the operator name IS a leak here.
        (out / "code" / "README.md").write_text("Written by the operator.\n", encoding="utf-8")

        hits = bs.leak_scan(out)
        check("licensor name in code/LICENSE is tolerated", "code/LICENSE" in hits, False)
        check("CLIENT name in an allowlisted legal file is CAUGHT",
              "code/docs/legal/NOTICE.md" in hits, True)
        check("operator name in an ordinary file is CAUGHT", "code/README.md" in hits, True)


def main() -> int:
    print("build_seed leak-scan allowlist tests (SYS-149)")
    test_allowlist_paths()
    test_scan_still_catches_what_matters()
    print()
    if _FAILED:
        print(f"RESULT: {len(_FAILED)} FAILED - " + ", ".join(_FAILED))
        return 1
    print("RESULT: all leak-scan allowlist tests pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
