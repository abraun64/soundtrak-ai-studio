#!/usr/bin/env python3
"""
Regression tests for surface_freshness.py — the module that GUARANTEES no operator surface
serves content older than its data.

Stdlib only (no pytest — it isn't installed). Run directly:
    python .claude/lib/test_surface_freshness.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this. The tests are read-only: they build a synthetic campaigns/
tree in a temp dir and point the module's DATA globals at it, so nothing on OneDrive is
touched and no render is invoked.
"""
from __future__ import annotations
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import surface_freshness as sf  # noqa: E402

_FAILED: list[str] = []

# Minimal stand-in for a render-html output: it must carry the pipeline chrome signature,
# because that signature is the discriminator separating "the pipeline rebuilds this from the
# .md" from "a Producer hand-built this once".
_RENDERED = '<html><body><nav class="crumb"><a href="../">back</a></nav><p>surface</p></body></html>'
_HANDBUILT = '<html><body><div class="mockup">a Producer artifact — nothing re-renders it</div></body></html>'

OLD = time.time() - 4 * 86400
NEW = time.time()


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _write(p: Path, text: str, mtime: float) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    os.utime(p, (mtime, mtime))
    return p


def _build(root: Path) -> Path:
    """A campaigns/ tree carrying one of each case the enumeration has to get right."""
    cd = root / "campaigns" / "camp-2026q1"
    _write(cd / "campaign.yaml", "slug: camp-2026q1\nstatus: active\n", OLD)

    # already-covered surfaces — must not ALSO appear as kind 'doc' (double-reporting)
    _write(cd / "camp-2026q1.md", "# Dashboard\n", OLD)
    _write(cd / "dashboard.html", _RENDERED, NEW)
    _write(cd / "gallery.html", _RENDERED, NEW)

    # STALE doc — a rendered surface behind its own markdown (the SYS-143 hole)
    _write(cd / "brief.md", "# Brief\n", NEW)
    _write(cd / "brief.html", _RENDERED, OLD)

    # FRESH doc — rendered after its markdown; must stay quiet
    _write(cd / "plan.md", "# Plan\n", OLD)
    _write(cd / "plan.html", _RENDERED, NEW)

    # hand-built Producer artifact with a newer same-stem .md — the original false-positive
    # class. No pipeline rebuilds it, so flagging it gives the operator an unactionable row.
    _write(cd / "assets" / "01-tile" / "mockup.md", "notes\n", NEW)
    _write(cd / "assets" / "01-tile" / "mockup.html", _HANDBUILT, OLD)

    # rendered asset record — inside assets/, still a reviewed surface
    _write(cd / "assets" / "01-tile" / "01-tile.md", "# Tile\n", NEW)
    _write(cd / "assets" / "01-tile" / "01-tile.html", _RENDERED, OLD)

    # rendered surface with NO same-stem source — nothing to compare against
    _write(cd / "assets" / "01-tile" / "og-card.html", _RENDERED, OLD)
    return cd


def _stale_names(root: Path) -> set[str]:
    """Run the real enumeration against the synthetic tree."""
    saved = (sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND)
    sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND = root, root / "campaigns", root / "tenant-brand"
    try:
        return {e["surface"] for e in sf.stale_surfaces()}
    finally:
        sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND = saved


def test_enumeration() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build(root)
        names = _stale_names(root)

        check("a doc behind its markdown is STALE (SYS-143 — the hole)",
              "camp-2026q1/brief.html" in names, f"got {sorted(names)}")
        check("an asset record behind its markdown is STALE",
              "camp-2026q1/assets/01-tile/01-tile.html" in names, f"got {sorted(names)}")
        check("a doc rendered after its markdown is not flagged",
              "camp-2026q1/plan.html" not in names, f"got {sorted(names)}")
        check("a hand-built Producer artifact is not flagged (no pipeline signature)",
              "camp-2026q1/assets/01-tile/mockup.html" not in names, f"got {sorted(names)}")
        check("a rendered surface with no same-stem source is not flagged",
              "camp-2026q1/assets/01-tile/og-card.html" not in names, f"got {sorted(names)}")
        check("dashboard.html is not double-reported as a doc",
              len([n for n in names if n.endswith("dashboard.html")]) <= 1, f"got {sorted(names)}")


def test_agrees_with_stale_sweep() -> None:
    """The two staleness sensors must agree BY CONSTRUCTION. stale-sweep's discriminator is the
    render-html chrome signature plus a same-stem .md; if this module stops sharing it, the two
    drift apart again and stale-sweep starts auto-filing ideas the gate calls fine (2026-08-22:
    stale-sweep flagged 7, the gate exited 0)."""
    sweep = Path(__file__).resolve().parents[1] / "skills" / "cadences" / "stale-sweep.py"
    if not sweep.exists():
        check("stale-sweep present to compare discriminators", True)
        return
    text = sweep.read_text(encoding="utf-8", errors="replace")
    check("stale-sweep and surface_freshness use the same pipeline signature",
          all(sig in text for sig in sf._PIPELINE_SIG),
          f"surface_freshness uses {sf._PIPELINE_SIG}, stale-sweep no longer matches")


def test_heal_converges_through_a_cascade() -> None:
    """Rebuilds CASCADE: healing an asset record bumps its mtime, which makes the gallery that
    aggregates it stale in turn. A single-pass heal ends by reporting that cascade as
    "STILL STALE after rebuild" — a loud failure for a surface that is merely one rebuild
    behind (observed live 2026-08-22: 8 healed, gallery.html falsely reported unfixable)."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cd = _build(root)
        # rebuild() stands in for the real renderer: touch the output, and (for the asset
        # record) also bump a ship file so the gallery goes stale the way it does live.
        def fake_rebuild(entry):
            now = time.time()
            os.utime(entry["out"], (now, now))
            if entry["out"].name == "01-tile.html":
                _write(cd / "assets" / "01-tile" / "tile.png", "x", now)
            return True

        saved = (sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND, sf.rebuild)
        sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND = root, root / "campaigns", root / "tenant-brand"
        sf.rebuild = fake_rebuild
        try:
            healed, still = sf.heal()
        finally:
            sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND, sf.rebuild = saved
        check("heal() converges through a cascade instead of crying wolf",
              not still, f"still stale after heal: {still}")
        check("heal() reports the surfaces it actually rebuilt",
              "camp-2026q1/brief.html" in healed, f"healed: {healed}")


def test_heal_still_reports_a_real_failure() -> None:
    """The bound must not turn into "retry until it looks fine". A surface whose rebuild does
    NOT fix it has to survive the loop and be reported loudly."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build(root)
        saved = (sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND, sf.rebuild)
        sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND = root, root / "campaigns", root / "tenant-brand"
        sf.rebuild = lambda entry: True          # claims success, changes nothing
        try:
            healed, still = sf.heal()
        finally:
            sf.DATA, sf.CAMPAIGNS, sf.TENANT_BRAND, sf.rebuild = saved
        check("a surface a rebuild cannot fix is still reported loudly",
              "camp-2026q1/brief.html" in still, f"still: {still}")


def test_missing_surface_keystone() -> None:
    """team-deployment.md §10 / the SYS-126 keystone.

    Under `profile: team` generated HTML is gitignored, so a FRESH CLONE has no surfaces at
    all. The exists() guards were written for a world where HTML is tracked, so an ABSENT
    surface was simply skipped — and the gate would tell an operator with zero surfaces that
    every surface was fresh. That is fail-loud inverted by a state it never contemplated.
    Where HTML is DERIVED, missing must count as needing a build; where it is committed,
    nothing changes.
    """
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _run_keystone(Path(_td))


def _run_keystone(tmp: Path) -> None:
    root = tmp / "keystone"
    camp = root / "campaigns" / "acme"
    (camp / "assets").mkdir(parents=True)
    (camp / "campaign.yaml").write_text("slug: acme\nphases: []\n", encoding="utf-8")
    (camp / "dashboard.md").write_text("# Acme\n", encoding="utf-8")

    saved = (sf.CAMPAIGNS, sf.DATA, sf.TENANT_BRAND, sf.missing_counts_as_stale)
    try:
        sf.CAMPAIGNS, sf.DATA = root / "campaigns", root
        sf.TENANT_BRAND = root / "tenant-brand"

        sf.missing_counts_as_stale = lambda: False          # html committed (small-business)
        found = {r["surface"] for r in sf.stale_surfaces()}
        check("small-business ignores a MISSING surface", "acme/dashboard.html" not in found,
              f"got {sorted(found)}")

        sf.missing_counts_as_stale = lambda: True           # html derived (team)
        found = {r["surface"] for r in sf.stale_surfaces()}
        check("team treats a MISSING surface as needing a build", "acme/dashboard.html" in found,
              f"got {sorted(found)}")
    finally:
        sf.CAMPAIGNS, sf.DATA, sf.TENANT_BRAND, sf.missing_counts_as_stale = saved


def main() -> int:
    print("surface_freshness regression tests")
    test_enumeration()
    test_heal_converges_through_a_cascade()
    test_heal_still_reports_a_real_failure()
    test_agrees_with_stale_sweep()
    test_missing_surface_keystone()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll surface_freshness tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
