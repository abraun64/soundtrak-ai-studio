#!/usr/bin/env python3
"""
Build the Tenant Dashboard — one operator HTML home per tenant, on the FLAT structure.

  Reads:  tenant-brand/<tenant>.yaml    (identity + baseline-compound pointers)
  Scans:  campaigns/*/campaign.yaml     (campaigns where `tenant: <slug>`)
  Writes: tenant-brand/<tenant>-home.md  -> renders to <tenant>-home.html

Why this is render-safe + additive:
  - The output lives under tenant-brand/, so NONE of render.py's auto-injection
    fires (dashboard + cross-surface injection are keyed to the campaigns/
    location). It renders as plain markdown with the `index` template's card CSS.
  - Reuses operator_actions.scan_all_campaigns + _phase_pill so the campaign rows
    match the master index exactly (single source of truth, no drift).
  - Touches no existing file. The auto-fire hooks are untouched.

Decided 2026-06-15 (logical tenant grouping on flat — supersedes the physical
business-rooted restructure that would have required dual-pathing the render chain).
Spec: docs/specs/phase-0-tenant-baseline.md §Tenant Dashboard.

Usage:
  python .claude/skills/render-html/build-tenant-home.py --tenant soundtrak
  python .claude/skills/render-html/build-tenant-home.py --all
"""
from __future__ import annotations
import argparse
import html as _html
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RENDER = ROOT / ".claude" / "skills" / "render-html" / "render.py"  # CODE — running checkout
# tenant-brand/ + campaigns/ are DATA, canonical in the MAIN checkout. Resolve via the
# shared helper so a worktree session reads the real campaigns (not an absent worktree
# campaigns/, which silently rendered every tenant home as "No active campaigns yet" —
# the SYS-103 blind spot, third instance) and writes the homes back to main.
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    _DATA = repo_paths.data_root(ROOT)
except Exception:
    _DATA = ROOT
TENANT_BRAND = _DATA / "tenant-brand"
CAMPAIGNS = _DATA / "campaigns"

sys.path.insert(0, str(ROOT / ".claude" / "skills" / "render-html"))
import operator_actions as oa  # noqa: E402
import yaml  # noqa: E402

# SYS-092 — reuse the phase0 surface's assessment so the home's Phase-0 snapshot can't
# disagree with the phase0 page (kills the "5/5" home vs "5/7 · 2 drafted" phase0 drift).
import importlib.util as _ilu  # noqa: E402
_p0_spec = _ilu.spec_from_file_location(
    "build_phase0_surface", ROOT / ".claude" / "skills" / "render-html" / "build-phase0-surface.py")
_phase0 = _ilu.module_from_spec(_p0_spec)
_p0_spec.loader.exec_module(_phase0)

STATUS_ICON = {"present": "✅", "planned": "🟡", "absent": "⚪"}


def _load_tenant_yaml(slug: str) -> dict | None:
    path = TENANT_BRAND / f"{slug}.yaml"
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"  ERROR parsing {path}: {e}", file=sys.stderr)
        return None


def _baseline_md(tenant: dict) -> str:
    """Compound list — present items link; planned items show as knowledge gaps."""
    rows = tenant.get("baseline") or []
    if not rows:
        return "_No baseline artifacts declared yet._"
    out = []
    for r in rows:
        title = _html.escape(str(r.get("title") or r.get("key") or "?"))
        status = str(r.get("status") or "present").lower()
        icon = STATUS_ICON.get(status, "•")
        href = str(r.get("href") or "")
        # Link only if present AND the file actually exists on disk (no dead links).
        if status == "present" and href and (TENANT_BRAND / href).exists():
            out.append(f"- {icon} **{title}** — [open]({_html.escape(href)})")
        elif status == "present" and href:
            out.append(f"- {icon} **{title}** — _declared `present` but `{_html.escape(href)}` not found (re-render the source)_")
        else:
            out.append(f"- {icon} **{title}** — _not yet established (Phase 0)_")
    return "\n".join(out)


def _campaign_card(camp: dict) -> str:
    """One camp-card, mirroring the master index (reuses operator_actions helpers).
    Hrefs are tenant-brand/-relative → ../campaigns/<slug>/..."""
    slug = camp["slug"]
    camp_dir = camp["campaign_dir"]
    cy = camp["campaign_yaml"]
    assets = camp["assets"]
    phases = cy.get("phases") or []
    total = len(assets)
    approved = sum(1 for a in assets if "Approved" in a["status_display"])

    nickname = cy.get("nickname")
    display = _html.escape(str(nickname or camp["name"]))
    formal = (f'<span class="camp-card__formal">{_html.escape(str(camp["name"]))}</span>'
              if nickname else "")
    pill_cls, pill_txt = oa._phase_pill(phases, total, camp_dir)

    stats = []
    if total:
        stats.append(f"{approved}/{total} assets approved")
    stats_html = ('<div class="camp-card__stats">'
                  + "".join(f"<span>{_html.escape(s)}</span>" for s in stats)
                  + "</div>") if stats else ""

    surfaces = [("📊 Dashboard", f"../campaigns/{slug}/dashboard.html"),
                ("🖼 Gallery", f"../campaigns/{slug}/gallery.html")]
    surfaces_html = "".join(
        f'<a href="{_html.escape(h)}">{_html.escape(l)}</a>' for l, h in surfaces)

    return (
        '<div class="camp-card">'
        '<div class="camp-card__head">'
        f'<div class="camp-card__headL"><span class="camp-card__name">{display}</span>{formal}</div>'
        f'<div class="camp-card__headR"><span class="pill {pill_cls}">{_html.escape(pill_txt)}</span></div>'
        '</div>'
        f'{stats_html}'
        f'<div class="camp-card__surfaces">{surfaces_html}</div>'
        '</div>'
    )


def build(slug: str) -> int:
    tenant = _load_tenant_yaml(slug)
    if tenant is None:
        print(f"ERROR: tenant-brand/{slug}.yaml not found or unparseable", file=sys.stderr)
        return 1
    name = str(tenant.get("name") or slug)
    summary = str(tenant.get("summary") or "")

    # SYS-092 — Phase-0 counts from the SAME shared computation the phase0 page uses, so
    # the home snapshot can't disagree with it (killed the 5/5-vs-5/7 drift).
    _st = _phase0.foundation_status(slug, tenant)
    _established, _total, _drafted = _st["done"], _st["total"], _st["drafted"]
    _drafted_txt = f" · {_drafted} drafted" if _drafted else ""

    # Campaigns owned by this tenant (single source of truth = campaign.yaml `tenant:`).
    all_camps = oa.scan_all_campaigns(CAMPAIGNS)
    owned = [c for c in all_camps if str(c["campaign_yaml"].get("tenant") or "") == slug]
    active, archived = [], []
    for c in owned:
        cy = c["campaign_yaml"]
        is_arch = bool(cy.get("archived")) or str(cy.get("status") or "").lower() == "archived"
        (archived if is_arch else active).append(c)

    active_cards = "".join(_campaign_card(c) for c in active) or '<p><em>No active campaigns yet.</em></p>'
    archived_html = ""
    if archived:
        rows = "".join(
            f'<li><a href="../campaigns/{c["slug"]}/dashboard.html">'
            f'{_html.escape(str(c["campaign_yaml"].get("nickname") or c["name"]))}</a></li>'
            for c in archived)
        archived_html = (
            f'\n\n<details class="camp-archived"><summary><strong>🗄 Archived campaigns '
            f'({len(archived)})</strong></summary>\n<ul>{rows}</ul></details>')

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# {name} — Home

**Last updated**: {stamp}     **Tenant**: `{slug}`     [← All campaigns](../campaigns/index.html)

{summary}

## Phase 0 — Tenant Baseline

_The durable compound every campaign inherits — built **once** at the tenant layer, **cited** per campaign (never re-built per campaign). **{_established}/{_total} established{_drafted_txt}.**_

**[→ Full Phase-0 baseline status (completion dates · drafted-vs-done · audit history)]({slug}-phase0.html)**

{_baseline_md(tenant)}

<small>✅ established · 🟡 planned (Phase 0 artifact not yet built). This is the Phase 0 artifact set — campaigns link up here, they don't duplicate it. Edit `tenant-brand/{slug}.yaml` to change what shows.</small>

## Campaigns

<div class="camp-grid">
{active_cards}
</div>{archived_html}

<small>Campaigns auto-derived from `campaigns/*/campaign.yaml` where `tenant: {slug}`. Rebuild: `python .claude/skills/render-html/build-tenant-home.py --tenant {slug}`.</small>
"""
    md_path = TENANT_BRAND / f"{slug}-home.md"
    md_path.write_text(md, encoding="utf-8")
    html_path = TENANT_BRAND / f"{slug}-home.html"
    res = subprocess.run(
        [sys.executable, str(RENDER), "--markdown", str(md_path),
         "--template", "index", "--output", str(html_path)],
        capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  render FAILED for {slug}: {res.stderr.strip()}", file=sys.stderr)
        return 1
    # Refresh the detailed Phase-0 baseline surface (SYS-049) alongside the home, so it
    # stays current on the same turn-end / stop-hook cadence.
    p0 = ROOT / ".claude" / "skills" / "render-html" / "build-phase0-surface.py"
    if p0.exists():
        subprocess.run([sys.executable, str(p0), "--tenant", slug], capture_output=True, text=True)
    print(f"  tenant home built: {md_path.name} -> {html_path.name} "
          f"({len(active)} active, {len(archived)} archived campaigns)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tenant", help="tenant slug (matches tenant-brand/<slug>.yaml)")
    g.add_argument("--all", action="store_true", help="build every tenant-brand/*.yaml")
    args = p.parse_args()

    if args.all:
        # A tenant identity file is any tenant-brand/*.yaml whose `tenant:` key
        # matches its own stem (robust against hyphenated slugs like acme-co
        # and against future non-tenant yaml siblings).
        slugs = []
        for f in sorted(TENANT_BRAND.glob("*.yaml")):
            if f.stem.startswith("_"):
                continue
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if str(data.get("tenant") or "") == f.stem:
                slugs.append(f.stem)
        if not slugs:
            print("(no tenant-brand/*.yaml identity files found)")
            return 0
        rc = 0
        for s in slugs:
            rc |= build(s)
        return rc
    return build(args.tenant)


if __name__ == "__main__":
    sys.exit(main())
