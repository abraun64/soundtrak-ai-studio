#!/usr/bin/env python3
"""Regression tests for publish_surfaces.py — the ONLY surface non-Studio colleagues ever see.

Stdlib only. Run directly:  python .claude/lib/test_publish_surfaces.py

Two properties, and they pull against each other:

  1. Every published page must SAY how current it is. A stakeholder has no repo, no health
     check and no way to tell a live dashboard from one whose publisher laptop has been shut
     for a week. Where an operator gets a loud failure, a stakeholder gets a plausible page,
     which is worse because it is believed. (the operator, 2026-09-16: the dashboards are the
     interface the WHOLE organisation reads, with or without Claude.)

  2. Unchanged pages must still be SKIPPED. The stamp therefore carries the source's
     last-changed time, never the publish time — a publish-time stamp changes every byte of
     every page on every run, so nothing is skippable and the sync client is handed the entire
     tree each time. That is the sync storm the design explicitly set out to avoid.

Regress either and the other silently breaks, which is why they are tested together.
"""
from __future__ import annotations
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import publish_surfaces as ps  # noqa: E402

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def main() -> int:
    print("publish_surfaces regression tests")
    with tempfile.TemporaryDirectory() as td:
        data, dest = Path(td) / "data", Path(td) / "pub"
        (data / "campaigns" / "acme").mkdir(parents=True)
        page = data / "campaigns" / "acme" / "dashboard.html"
        page.write_text("<html><body><h1>Acme</h1></body></html>", encoding="utf-8")
        old = time.time() - 5 * 86400
        os.utime(page, (old, old))

        r1 = ps.publish(dest, data)
        out = (dest / "campaigns" / "acme" / "dashboard.html").read_text(encoding="utf-8")
        check("published page carries a visible freshness stamp", ps.BANNER_MARK in out)
        check("stamp names it read-only", "Read-only copy" in out)
        check("original markup is preserved", "<h1>Acme</h1>" in out
              and out.rstrip().endswith("</html>"))
        check("first publish copies", r1["copied"] == 1, str(r1))

        r2 = ps.publish(dest, data)
        check("an unchanged page is SKIPPED (no sync storm)",
              r2["skipped"] == 1 and r2["copied"] == 0, str(r2))

        page.write_text("<html><body><h1>Acme v2</h1></body></html>", encoding="utf-8")
        r3 = ps.publish(dest, data)
        out3 = (dest / "campaigns" / "acme" / "dashboard.html").read_text(encoding="utf-8")
        check("an edited page republishes", r3["copied"] == 1, str(r3))
        check("the stamp is not duplicated on republish", out3.count(ps.BANNER_MARK) == 1)
        check("the _PUBLISHED.txt sidecar is still written", (dest / "_PUBLISHED.txt").is_file())

    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll publish_surfaces tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
