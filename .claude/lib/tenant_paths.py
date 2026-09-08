#!/usr/bin/env python3
"""
Dual-path tenant / campaign resolution (W4 — business-rooted support).

⚠ DORMANT (2026-06-15). The physical business-rooted restructure this module
supports was SUPERSEDED by logical tenant grouping on the FLAT structure
(tenant.yaml + campaign.yaml `tenant:` field + build-tenant-home.py + cross-links;
see docs/specs/phase-0-tenant-baseline.md §Tenant Dashboard and the implementation
plan's "W4 SUPERSEDED" section). Kept as an additive no-op: with no business-rooted
tenant on disk, every function returns nothing extra, so the wired callers behave
identically to flat. Left only as a future option — do NOT resurrect the 9-file
restructure without re-confirming with the operator.

Two layouts coexist:
  - FLAT (existing tenants — your tenants):  campaigns/<slug>/  +  tenant-brand/<tenant>-*
  - BUSINESS-ROOTED (new Phase-0 tenants):            <Tenant>/baseline/  +  <Tenant>/campaigns/<slug>/

This module is ADDITIVE. It finds business-rooted campaigns IN ADDITION to flat ones.
A business-rooted tenant is identified by the exact signature: a top-level dir that has
BOTH `baseline/` AND `campaigns/`. With zero business-rooted tenants, every function
returns nothing extra — so callers behave identically to flat (provably non-breaking
until a business-rooted tenant is created). Existing tenants are NEVER migrated by this;
the flat code paths in each caller stay untouched.

Usage (from a skill or hook):
    import sys; sys.path.insert(0, str(REPO_ROOT / ".claude" / "lib"))
    import tenant_paths as tp
    dirs = flat_dirs + tp.business_rooted_campaign_dirs(REPO_ROOT)
"""
from pathlib import Path

# Top-level dirs that are NEVER tenants (system / infra / the flat campaigns root itself).
_NON_TENANT = {
    "campaigns", "tenant", "tenant-brand", "docs", ".claude", ".git",
    "craft", "operator", "retros", "examples", "best practices", "_archive",
    "node_modules",
}


def is_business_rooted_tenant(p: Path) -> bool:
    """A business-rooted tenant = a top-level dir with BOTH baseline/ and campaigns/."""
    try:
        return (
            p.is_dir()
            and p.name.lower() not in _NON_TENANT
            and (p / "baseline").is_dir()
            and (p / "campaigns").is_dir()
        )
    except OSError:
        return False


def business_rooted_tenants(repo_root: Path) -> list:
    """All business-rooted tenant dirs under repo_root. [] until one is created."""
    try:
        return sorted((p for p in repo_root.iterdir() if is_business_rooted_tenant(p)), key=lambda p: p.name)
    except OSError:
        return []


def business_rooted_campaign_dirs(repo_root: Path) -> list:
    """All <Tenant>/campaigns/<slug>/ dirs. [] today (no business-rooted tenant exists)."""
    out = []
    for t in business_rooted_tenants(repo_root):
        camps = t / "campaigns"
        try:
            out += [c for c in camps.iterdir() if c.is_dir()]
        except OSError:
            continue
    return sorted(out, key=lambda p: p.name)


def find_campaign_dir(repo_root: Path, slug: str):
    """Locate a campaign dir by slug in EITHER layout. Flat (campaigns/<slug>/) first,
    then business-rooted (<Tenant>/campaigns/<slug>/). Returns None if not found."""
    flat = repo_root / "campaigns" / slug
    if flat.is_dir():
        return flat
    for c in business_rooted_campaign_dirs(repo_root):
        if c.name == slug:
            return c
    return None


def tenant_of(campaign_dir: Path) -> Path | None:
    """Return the business-rooted tenant dir for a campaign (its parent.parent when that
    is a business-rooted tenant), or None for a flat campaign (campaigns/<slug>/)."""
    try:
        parent = campaign_dir.parent            # .../campaigns
        grandparent = parent.parent             # .../<Tenant>  (or the repo root, for flat)
        if parent.name == "campaigns" and is_business_rooted_tenant(grandparent):
            return grandparent
    except (OSError, ValueError):
        pass
    return None
