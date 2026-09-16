#!/usr/bin/env python3
"""Regression tests for operator_versions.py — making a version split visible.

Stdlib only. Run directly:  python .claude/lib/test_operator_versions.py

Why this matters more than it looks: every guard lives in the CODE half, so a team's real
protection is the MINIMUM version anyone runs. One person left behind can commit into shared
history what everybody else's machine would have blocked, and shared history is permanent.
Before this, nothing anywhere recorded or compared versions.
"""
from __future__ import annotations
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operator_versions as ov  # noqa: E402

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _write(data: Path, who: str, version: str, days_ago: int = 0) -> None:
    d = data / ov.REL
    d.mkdir(parents=True, exist_ok=True)
    when = datetime.now(timezone.utc) - timedelta(days=days_ago)
    (d / f"{ov._slug(who)}.yaml").write_text(
        f"operator: {who}\nversion: {version}\nlast_seen: {when.isoformat(timespec='seconds')}\n",
        encoding="utf-8")


def main() -> int:
    print("operator_versions tests")
    # Pin THIS machine's version. Previously these read the repo's actual tag, so they passed
    # only while HEAD happened to sit on one — a test of the environment, not of the code.
    ov.my_version = lambda *a, **k: "v1.10.0"
    with tempfile.TemporaryDirectory() as td:
        data = Path(td)

        st = ov.status(data=data, identity="me@x.com")
        check("a lone operator is never warned", st["level"] == "ok", str(st))

        _write(data, "me@x.com", "v1.10.0")
        _write(data, "colleague@x.com", "v1.10.0")
        st = ov.status(data=data, identity="me@x.com")
        check("a team all on one version is quiet", st["level"] == "ok", str(st))

        _write(data, "colleague@x.com", "v1.11.0")
        st = ov.status(data=data, identity="me@x.com")
        check("being BEHIND a colleague is reported", st["level"] == "behind", str(st))
        check("...and names the newest version", st["newest"] == "v1.11.0", str(st))
        check("...and says why it matters, not just that it differs",
              "weaker safety checks" in ov.describe(st), ov.describe(st))

        _write(data, "colleague@x.com", "v1.9.0")
        st = ov.status(data=data, identity="me@x.com")
        check("being AHEAD is reported as a split, not as fine",
              st["level"] == "split", str(st))

        _write(data, "onleave@x.com", "v1.2.0", days_ago=90)
        st = ov.status(data=data, identity="me@x.com")
        check("someone away for months is not counted",
              all(r["operator"] != "onleave@x.com" for r in st["others"]), str(st))
        check("...but is still listed when asked for everyone",
              any(r["operator"] == "onleave@x.com" for r in ov.everyone(data, include_stale=True)))

        _write(data, "newjoiner@x.com", ov.UNPINNED)
        st = ov.status(data=data, identity="me@x.com")
        check("an unpinned colleague does not crash the comparison",
              st["level"] in ("behind", "split"), str(st))

        (data / ov.REL / "junk.yaml").write_text("not: a record\n", encoding="utf-8")
        check("an unreadable file is skipped rather than fatal",
              isinstance(ov.everyone(data), list))

        p = ov.record(data=data, identity="writer@x.com")
        check("record() writes one file per operator (no shared list to conflict on)",
              p is not None and p.name == "writer-x.com.yaml", str(p))

    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll operator_versions tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
