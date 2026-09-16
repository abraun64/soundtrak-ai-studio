#!/usr/bin/env python3
"""Regression tests for system_update.check() — who gets offered an update.

Stdlib only. Run directly:  python .claude/lib/test_system_update.py

THE CASE THAT WAS WRONG: an operator whose checkout is not on a release tag. That is not an
edge case, it is how everybody starts. An organisation creates its code repo by uploading the
downloaded Studio — one untagged commit — and every operator clones the default BRANCH. So
`git describe --exact-match` finds nothing, `current` is None, and the old logic required a
current tag before it would offer anything. Every operator at every organisation was therefore
told they were up to date, permanently, and the FIRST upgrade could never be offered.

It hid where nobody looks: "you are up to date" is the answer people expect and do not question.
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import system_update as su  # noqa: E402

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _repo(td: Path, *, tags: list[str], sit_on_first: bool) -> Path:
    r = td / "repo"
    r.mkdir()

    def g(*a):
        subprocess.run(["git", *a], cwd=r, capture_output=True)

    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (r / "f.txt").write_text("v1")
    g("add", "-A")
    g("commit", "-qm", "initial upload")
    first = subprocess.run(["git", "rev-parse", "HEAD"], cwd=r,
                           capture_output=True, text=True).stdout.strip()
    for t in tags:
        (r / "f.txt").write_text(t)
        g("add", "-A")
        g("commit", "-qm", t)
        g("tag", "-a", t, "-m", t)
    if sit_on_first:
        g("checkout", "-q", first)
    return r


def main() -> int:
    print("system_update.check tests")
    with tempfile.TemporaryDirectory() as td:
        r = _repo(Path(td), tags=["v1.10.0"], sit_on_first=True)
        info = su.check(r, fetch=False)
        check("an UNTAGGED clone is offered the latest release",
              info["available"] == ["v1.10.0"], str(info))
        check("...and is not described to the operator as 'None'",
              "None" not in su.describe_current(info), su.describe_current(info))
        check("...and is reported as unpinned", info["pinned"] is False, str(info))

    with tempfile.TemporaryDirectory() as td:
        r = _repo(Path(td), tags=["v1.10.0", "v1.11.0"], sit_on_first=False)
        info = su.check(r, fetch=False)
        check("a clone already on the newest release is offered nothing",
              info["available"] == [] and info["pinned"] is True, str(info))
        ok, msg = su.apply("v1.10.0", r)
        info2 = su.check(r, fetch=False)
        check("a clone on an older release is offered only what is newer",
              info2["available"] == ["v1.11.0"], str(info2))
        check("...and knows which release it is on", info2["current"] == "v1.10.0", str(info2))

    with tempfile.TemporaryDirectory() as td:
        r = _repo(Path(td), tags=[], sit_on_first=False)
        info = su.check(r, fetch=False)
        check("a repo with no releases at all offers nothing",
              info["available"] == [] and info["latest"] is None, str(info))

    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll system_update tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
