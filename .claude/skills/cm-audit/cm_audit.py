#!/usr/bin/env python3
"""
CM self-audit — is CM actually doing its job on the live surfaces? (read-only)

Answers the operator's "do you know they're doing it?" for the machine-checkable
slice of the CM responsibility catalog (docs/specs/_proposals/cm-responsibility-audit.md).
It does NOT judge content quality — it checks that the operator surfaces are PRESENT,
CURRENT (rendered at least as recently as their data sources), and that the tenant-layer
data CM must maintain is in place.

  python .claude/skills/cm-audit/cm_audit.py

Exit 0 = all green; exit 1 = any finding (printed inline). Pairs with the system
smoke test (which checks presence; this adds currency + tenant-layer + per-campaign data).

Currency principle: a rendered surface should be >= the mtime of its data sources.
If a source (.md / .yaml) is newer than its render, CM changed state without re-rendering
— the exact "stale operator surface" failure. Re-render noise (touching a render without
a data change) does NOT trip this, because we compare render-vs-source, not render-vs-any-file.
"""
from __future__ import annotations
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# campaigns/ + tenant-brand/ are canonical in the MAIN checkout; resolve via the shared
# helper so cm-audit works from a .claude/worktrees/* checkout too (SYS-002 / IDEA-007).
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    _DATA = repo_paths.data_root(ROOT)
except Exception:
    _DATA = ROOT
CAMP = _DATA / "campaigns"
TB = _DATA / "tenant-brand"
EPS = 2.0  # seconds tolerance for same-write filesystem jitter

try:
    import yaml
except ImportError:
    yaml = None

results: list[tuple[str, str, bool, str]] = []  # (group, label, ok, detail)


def check(group: str, label: str, ok: bool, detail: str = "") -> None:
    results.append((group, label, bool(ok), detail))


def _mt(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def _load(p: Path) -> dict:
    if yaml is None or not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _is_active(cdir: Path) -> bool:
    d = _load(cdir / "campaign.yaml")
    return not (bool(d.get("archived")) or str(d.get("status") or "").lower() == "archived")


_UPDATED_RE = re.compile(r"updated[^\n]{0,15}\d{4}-\d{2}-\d{2}", re.IGNORECASE)


def _has_last_updated(md: Path) -> bool:
    """True if the dashboard header carries a DATED update stamp. Accepts the canonical
    `**Last updated**: YYYY-MM-DD` and the richer-header variant `· updated YYYY-MM-DD`
    — the signal is a date adjacent to 'updated', not the exact phrasing."""
    if not md.exists():
        return False
    head = "\n".join(md.read_text(encoding="utf-8").splitlines()[:60])
    return bool(_UPDATED_RE.search(head))


def _stale(render: Path, *sources: Path) -> str:
    """Return a detail string if any source is newer than the render, else ''."""
    if not render.exists():
        return "render missing"
    r = _mt(render)
    newer = [s.name for s in sources if s.exists() and _mt(s) > r + EPS]
    return ("source newer: " + ", ".join(newer)) if newer else ""


# ── Per active campaign ──────────────────────────────────────────────────────
active = []
if CAMP.is_dir():
    active = [c for c in sorted(CAMP.iterdir())
              if c.is_dir() and (c / "assets").is_dir() and _is_active(c)]

for c in active:
    slug = c.name
    cy = c / "campaign.yaml"
    src_md = c / f"{slug}.md"
    if not src_md.exists():
        src_md = c / "dashboard.md"
    dash = c / "dashboard.html"          # canonical operator surface (index links here)
    gallery = c / "gallery.html"

    # canonical dashboard present + current with its sources
    if not dash.exists():
        check("campaign:" + slug, "dashboard.html present", False, "canonical dashboard missing (only <slug>.html?)")
    else:
        det = _stale(dash, src_md, cy)
        check("campaign:" + slug, "dashboard.html current", det == "", det or "")
    # last-updated stamp
    check("campaign:" + slug, "Last-updated stamp", _has_last_updated(src_md), "no 'Last updated' line in dashboard md")
    # gallery present
    check("campaign:" + slug, "gallery.html present", gallery.exists())
    # tenant-layer data CM maintains
    tslug = str(_load(cy).get("tenant") or "").strip()
    check("campaign:" + slug, "campaign.yaml tenant: set", bool(tslug), "no `tenant:` field — won't group under a tenant")
    check("campaign:" + slug, "gallery-config.yaml present", (c / "gallery-config.yaml").exists(),
          "missing → gallery falls back to generic skeleton")

# ── Cross-surface ────────────────────────────────────────────────────────────
newest_cy = max([_mt(c / "campaign.yaml") for c in active], default=0.0)
for name in ("index", "tasks"):
    surf = CAMP / f"{name}.html"
    det = "render missing" if not surf.exists() else (
        "stale vs newest campaign.yaml — a new/changed campaign hasn't been re-rendered here"
        if newest_cy > _mt(surf) + EPS else "")
    check("cross-surface", f"{name}.html current", det == "", det)

# ── Per tenant ───────────────────────────────────────────────────────────────
tenants = []
if TB.is_dir():
    for f in sorted(TB.glob("*.yaml")):
        d = _load(f)
        if str(d.get("tenant") or "") == f.stem:   # identity file
            tenants.append(f.stem)

for t in tenants:
    home = TB / f"{t}-home.html"
    owned_cy = [c / "campaign.yaml" for c in active if str(_load(c / "campaign.yaml").get("tenant") or "") == t]
    if not home.exists():
        check("tenant:" + t, "tenant home present", False, "no <tenant>-home.html — run build-tenant-home.py")
    else:
        det = _stale(home, *owned_cy)
        check("tenant:" + t, "tenant home current", det == "", det or "")

# ── Surface-honesty guard (SYS-059) ──────────────────────────────────────────
# A ✅ on an operator surface may sit ONLY on a genuinely-gated artifact (Brief ·
# Selected concept · Plan · finished assets · Phase-5/6 plans). A ✅ on an ungated
# input (Insight Brief, concept trio/menu, moodboard, editorial backlog, research …)
# fabricates an operator approval and erodes gallery trust — docs/workflow.md rule 8.
try:
    import surface_honesty
    for v in surface_honesty.scan(_DATA):
        check("campaign:" + v.campaign,
              "surface-honesty (no ✅ on ungated input)", False,
              f'{v.surface} · {v.where} · "{v.offending}"')
except Exception as e:
    check("surface-honesty", "guard ran", False, f"surface_honesty guard error: {e}")

# ── Report ───────────────────────────────────────────────────────────────────
groups: list[str] = []
for g, *_ in results:
    if g not in groups:
        groups.append(g)

try:  # Windows consoles default to cp1252, which can't encode ✅ / · in details
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
print("=== CM SELF-AUDIT ===")
print(f"Date: {datetime.now():%Y-%m-%d %H:%M}")
print(f"Active campaigns: {len(active)} · Tenants: {len(tenants)}\n")
all_pass = True
for g in groups:
    rows = [r for r in results if r[0] == g]
    print(g)
    for _, label, ok, detail in rows:
        dots = "." * max(3, 32 - len(label))
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        line = f"  {label} {dots} {status}"
        if detail and not ok:
            line += f"  ({detail})"
        print(line)
    print()
print("RESULT:", "ALL GREEN" if all_pass else "FINDINGS — see FAIL rows above")
sys.exit(0 if all_pass else 1)
