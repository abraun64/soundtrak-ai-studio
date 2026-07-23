#!/usr/bin/env python3
"""
surface_freshness — SYS-112 prong A. Make operator surfaces impossible to show stale.

THE PROBLEM: the operator surfaces (per-campaign dashboard.html + gallery.html, the
cross-campaign tasks.html + index.html, tenant homes) are pre-rendered STATIC HTML with no
running server. Each is a snapshot that must be re-generated after every data change; a
skipped regeneration (a no-op hook, a dead subagent, a forgotten render) leaves the surface
behind the data — and the operator reviews stale content without knowing.

THE GUARANTEE (this module): don't rely on REMEMBERING to render — VERIFY it. Every turn,
compare each surface's mtime against the newest of its data inputs; any surface behind its
data is STALE. `heal()` rebuilds the stale ones and re-verifies; if a surface is STILL behind
after a rebuild, that's a hard failure the caller surfaces loudly. So the dirty-ledger becomes
an optimisation, not the guarantee — even a completely missed re-render is caught here.

The freshness rule is coarse but SOUND: a surface must be at least as new as the newest
NON-generated data file it could depend on. Over-inclusion only costs an occasional rebuild;
it can never let a stale surface through (the safe direction).

Usage:
  python surface_freshness.py --check         # exit 1 if any surface is behind its data
  python surface_freshness.py --heal          # rebuild stale surfaces; exit 1 if any remain
  python surface_freshness.py --check --campaign <slug>   # scope to one campaign
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]        # .claude/lib -> checkout root (CODE)
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)             # DATA dirs canonical in main checkout
except Exception:
    DATA = ROOT
CAMPAIGNS = DATA / "campaigns"
TENANT_BRAND = DATA / "tenant-brand"
# SYS-116: the surfaces we heal are MAIN-canonical (they live under DATA), so render them with
# MAIN's canonical renderer — NOT the running checkout's. From a worktree, ROOT is the worktree
# and its render code may be stale/unlanded; rendering main's dashboard.html with it silently
# clobbers the surface (a worktree's stale code reverted a landed fix — the bug this fixes). DATA
# is the main checkout root, so DATA/.claude/... is main's code. From the main checkout DATA==ROOT.
_CODE = DATA
RENDER = _CODE / ".claude" / "skills" / "render-html" / "render.py"
BASE_TMPL = _CODE / ".claude" / "skills" / "render-html" / "templates" / "base.html"
BUILD_GALLERY = _CODE / ".claude" / "skills" / "asset-gallery" / "build-gallery.py"
BUILD_TENANT = _CODE / ".claude" / "skills" / "render-html" / "build-tenant-home.py"

EPSILON = 2.0  # seconds — absorb git-checkout same-stamp + sub-second render timing

_SKIP_DIR = ("/gallery-thumbs/",)

# SYS-116: mtime-freshness is necessary but NOT sufficient — a surface can be NEWER than its data
# yet contain an UNRESOLVED auto-inject sentinel (rendered by stale code that didn't know the
# marker). That reads as a blank/broken section while passing the mtime check. So a surface that
# still carries any of these sentinels is treated as STALE and rebuilt (with main's code, above);
# if it survives a rebuild, heal() reports it loudly instead of letting it through silently.
_SENTINEL_RE = re.compile(
    r"<!--\s*(?:[A-Z0-9_]*(?:_AUTO|_MARKER|AUTO_INJECT)[A-Z0-9_]*"
    r"|PHASE_COST:\d+|PHASE_HUMAN_TIME:\d+)\s*-->"
)


def _has_sentinel(p: Path) -> bool:
    try:
        return bool(_SENTINEL_RE.search(p.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        return False


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def _newest(paths) -> float:
    m = 0.0
    for p in paths:
        m = max(m, _mtime(p))
    return m


def _newest_under(root: Path, suffixes: tuple[str, ...] | None = None,
                  skip_generated: set[Path] | None = None) -> float:
    """Newest mtime of files under `root`, optionally restricted to `suffixes`, skipping
    gallery-thumbs and any explicitly-generated surfaces (so a surface isn't 'newer than
    itself')."""
    skip_generated = skip_generated or set()
    m = 0.0
    if not root.is_dir():
        return m
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        s = str(p).replace("\\", "/")
        if any(sd in s for sd in _SKIP_DIR):
            continue
        if p in skip_generated:
            continue
        if suffixes and p.suffix.lower() not in suffixes:
            continue
        m = max(m, _mtime(p))
    return m


def _is_archived(campaign_dir: Path) -> bool:
    y = campaign_dir / "campaign.yaml"
    if not y.exists():
        return False
    try:
        import yaml
        d = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
        return bool(d.get("archived")) or str(d.get("status") or "").lower() == "archived"
    except Exception:
        return False


def _active_campaigns():
    if not CAMPAIGNS.is_dir():
        return []
    return [d for d in sorted(CAMPAIGNS.iterdir())
            if d.is_dir() and (d / "campaign.yaml").exists() and not _is_archived(d)]


def stale_surfaces(scope_campaign: str | None = None) -> list[dict]:
    """Return the list of surfaces whose rendered HTML is behind its data. Each entry:
    {surface, kind, slug|tenant, out (Path), data_mtime, out_mtime}. Pure/read-only."""
    stale: list[dict] = []
    camps = _active_campaigns()
    if scope_campaign:
        camps = [c for c in camps if c.name == scope_campaign]

    for cd in camps:
        slug = cd.name
        assets = cd / "assets"
        dash = cd / "dashboard.html"
        gallery = cd / "gallery.html"

        # dashboard.html ← every .md/.yaml in the campaign (operator_actions, plan, brief,
        # the dashboard md itself). Exclude the generated surfaces so it isn't newer-than-self.
        dash_data = _newest_under(cd, suffixes=(".md", ".yaml"), skip_generated={dash, gallery})
        if dash.exists() and ((dash_data and _mtime(dash) < dash_data - EPSILON) or _has_sentinel(dash)):
            stale.append({"surface": f"{slug}/dashboard.html", "kind": "dashboard",
                          "slug": slug, "out": dash, "data_mtime": dash_data, "out_mtime": _mtime(dash)})

        # gallery.html ← every asset file (asset.yaml + ship files: html/png/mp4/md).
        gal_data = _newest_under(assets)
        if gallery.exists() and ((gal_data and _mtime(gallery) < gal_data - EPSILON) or _has_sentinel(gallery)):
            stale.append({"surface": f"{slug}/gallery.html", "kind": "gallery",
                          "slug": slug, "out": gallery, "data_mtime": gal_data, "out_mtime": _mtime(gallery)})

    # Cross-campaign tasks.html + index.html ← their md source + every campaign's .yaml/.md.
    if not scope_campaign:
        cross_data = max(
            _newest([CAMPAIGNS / "tasks.md", CAMPAIGNS / "index.md"]),
            _newest(p for c in _active_campaigns()
                    for p in [c / "campaign.yaml"] + list((c / "assets").rglob("*.yaml"))),
        )
        for name in ("tasks", "index"):
            out = CAMPAIGNS / f"{name}.html"
            if out.exists() and ((cross_data and _mtime(out) < cross_data - EPSILON) or _has_sentinel(out)):
                stale.append({"surface": f"{name}.html", "kind": "cross", "name": name,
                              "out": out, "data_mtime": cross_data, "out_mtime": _mtime(out)})

        # Tenant homes ← the tenant's campaigns' campaign.yaml AND asset.yaml (the home shows
        # per-campaign "N/M assets approved" counts derived from asset STATES, so an asset
        # approval must flag it stale), plus the tenant's own yaml/home md. Coarse-but-sound:
        # newest asset.yaml across ALL active campaigns (over-inclusive, never misses).
        if TENANT_BRAND.is_dir():
            _campaign_data = _newest(
                p for c in _active_campaigns()
                for p in [c / "campaign.yaml"] + list((c / "assets").rglob("*.yaml"))
            )
            for home in sorted(TENANT_BRAND.glob("*-home.html")):
                tenant = home.name[:-len("-home.html")]
                t_data = max(
                    _campaign_data,
                    _mtime(TENANT_BRAND / f"{tenant}.yaml"),
                    _mtime(TENANT_BRAND / f"{tenant}-home.md"),
                )
                if (t_data and _mtime(home) < t_data - EPSILON) or _has_sentinel(home):
                    stale.append({"surface": f"tenant-brand/{tenant}-home.html", "kind": "tenant",
                                  "tenant": tenant, "out": home, "data_mtime": t_data, "out_mtime": _mtime(home)})
    return stale


def _run(args: list[str]) -> bool:
    try:
        # SYS-116: run from the main checkout (DATA) so the canonical renderer's relative
        # resolution + any imports come from main, matching the main-canonical surface it writes.
        r = subprocess.run(["python"] + args, cwd=str(DATA), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=180)
        return r.returncode == 0
    except Exception:
        return False


def rebuild(entry: dict) -> bool:
    """Rebuild one stale surface via the canonical render tool."""
    kind = entry["kind"]
    if kind == "dashboard":
        slug = entry["slug"]
        md = CAMPAIGNS / slug / f"{slug}.md"
        return _run([str(RENDER), "--markdown", str(md), "--template", str(BASE_TMPL),
                     "--output", str(CAMPAIGNS / slug / "dashboard.html")])
    if kind == "gallery":
        return _run([str(BUILD_GALLERY), "--campaign", entry["slug"]])
    if kind == "cross":
        return _run([str(RENDER), "--markdown", str(CAMPAIGNS / f"{entry['name']}.md"),
                     "--template", str(BASE_TMPL)])
    if kind == "tenant":
        return _run([str(BUILD_TENANT), "--tenant", entry["tenant"]])
    return False


def heal(scope_campaign: str | None = None) -> tuple[list[str], list[str]]:
    """Rebuild every stale surface, then re-verify. Returns (healed, still_stale)."""
    healed, failed = [], []
    for e in stale_surfaces(scope_campaign):
        (healed if rebuild(e) else failed).append(e["surface"])
    still = [e["surface"] for e in stale_surfaces(scope_campaign)]
    return sorted(set(healed) - set(still)), sorted(set(still) | set(failed))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Guarantee operator-surface freshness (SYS-112).")
    ap.add_argument("--check", action="store_true", help="report stale surfaces; exit 1 if any")
    ap.add_argument("--heal", action="store_true", help="rebuild stale surfaces; exit 1 if any remain")
    ap.add_argument("--campaign", help="scope to one campaign slug")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if a.heal:
        healed, still = heal(a.campaign)
        if healed:
            print(f"surface-freshness: rebuilt {len(healed)} stale surface(s): {', '.join(healed)}")
        if still:
            print(f"surface-freshness: STILL STALE after rebuild ({len(still)}): {', '.join(still)}", file=sys.stderr)
            return 1
        if not healed:
            print("surface-freshness: all surfaces current.")
        return 0

    # default / --check
    stale = stale_surfaces(a.campaign)
    if not stale:
        print("surface-freshness: OK — every surface is at least as new as its data.")
        return 0
    print(f"surface-freshness: {len(stale)} STALE surface(s) — behind their data:", file=sys.stderr)
    for e in stale:
        print(f"  x {e['surface']}: rendered {datetime.fromtimestamp(e['out_mtime']):%Y-%m-%d %H:%M} < "
              f"data {datetime.fromtimestamp(e['data_mtime']):%Y-%m-%d %H:%M} — rebuild (or run --heal)",
              file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
