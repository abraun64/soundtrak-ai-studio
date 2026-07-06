#!/usr/bin/env python3
"""Shared helpers for the SYS-020 scheduled cadences.

Factored out of the proven SYS-005 weekly-digest pattern so all four cadences
share ONE copy of the load-bearing safety logic:

  - repo_paths-based DATA resolution (worktree-aware — DATA dirs are canonical
    in the MAIN checkout even when a cadence runs from a worktree);
  - deduped idea-filing as TEXT append (never safe_dump — that would drop the
    file's header + comments), with a YAML-safe QUOTED title (idea titles
    contain colons → invalid unquoted) and a parse-then-rollback safety net so
    ideas.yaml can never be left unparseable;
  - digest writing to system/digests/<date>.md + HTML render so the dashboard
    can link a viewable version.

HARD GUARDRAIL (every cadence, non-negotiable): READ-ONLY + SURFACES only. A
cadence writes a dated markdown digest and/or files a DEDUPED inbox idea. It
NEVER auto-triages, auto-edits campaigns/tenants, auto-ships, or takes any
destructive action. These helpers only ever APPEND to ideas.yaml (deduped) and
WRITE digest files — nothing else.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# .claude/skills/cadences/_cadence_common.py -> parents[3] == repo root (the
# running checkout). DATA dirs resolve to the MAIN checkout via repo_paths.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths

    DATA = repo_paths.data_root(ROOT)
except Exception:  # noqa: BLE001 — never let path resolution crash a read-only cadence
    DATA = ROOT

SYSTEM_DIR = DATA / "system"
SKILLS = ROOT / ".claude" / "skills"
CAMPAIGNS_DIR = DATA / "campaigns"
TENANT_BRAND_DIR = DATA / "tenant-brand"
LIBRARY_DIR = DATA / "tenant" / "library"

# Digests are written UTF-8, but the printed echo of those same lines (with → / ⚠️)
# must not crash on a cp1252 console (Windows interactive shell OR a non-interactive
# scheduled task). Reconfigure stdout/stderr to UTF-8 with errors=replace so a print
# can never bring down an otherwise-successful read-only cadence.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — older/odd streams without reconfigure
        pass


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_yaml_items(path: Path, key: str = "items") -> list:
    """Read a YAML file and return its `key` list, or [] on any problem.

    Read-only and exception-swallowing by design: a cadence must never crash on
    a malformed or absent data file."""
    try:
        import yaml
    except ImportError:
        return []
    if not path.exists():
        return []
    try:
        return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(key, []) or []
    except Exception:  # noqa: BLE001
        return []


def file_new_ideas(new_titles: list[str], raised_by: str, today: str,
                   summary: str = "", source: str = "cadence") -> list[str]:
    """Append deduped idea entries to system/ideas.yaml as TEXT.

    Mirrors the weekly-digest helper exactly: preserves the file header/comments
    (no safe_dump), QUOTES the title (idea titles contain colons), and rolls back
    if the append ever leaves ideas.yaml unparseable. Dedupe is by case-folded
    title against existing ideas AND backlog tickets, so a finding already filed
    or already promoted to a ticket is NOT re-raised.

    Returns the list of filed IDEA-ids ([] if nothing new or on rollback)."""
    if not new_titles:
        return []

    ideas = load_yaml_items(SYSTEM_DIR / "ideas.yaml")
    backlog = load_yaml_items(SYSTEM_DIR / "backlog.yaml")
    seen = {str(i.get("title", "")).strip().lower() for i in ideas} | \
           {str(b.get("title", "")).strip().lower() for b in backlog}

    fresh = []
    for t in new_titles:
        key = str(t).strip().lower()
        if key and key not in seen:
            fresh.append(t)
            seen.add(key)
    if not fresh:
        return []

    nums = [int(str(i.get("id", "IDEA-0")).split("-")[-1]) for i in ideas
            if str(i.get("id", "")).startswith("IDEA-")
            and str(i.get("id", "")).split("-")[-1].isdigit()]
    # SYS-057: next-IDEA must respect the FULL guard view — the MAX id across ideas + backlog +
    # audit-log ref: fields — not just ideas.yaml. Otherwise a promoted+removed cadence id (whose
    # only remaining trace is an audit ref:) gets re-minted. Scan the other two stores for IDEA ids
    # too; combined with the `captured` audit write below, the cadence can never re-mint a used id.
    import re as _re_id
    for _store in ("audit-log.yaml", "backlog.yaml"):
        _p = SYSTEM_DIR / _store
        if _p.exists():
            try:
                nums += [int(n) for n in _re_id.findall(r"IDEA-(\d+)", _p.read_text(encoding="utf-8"))]
            except Exception:  # noqa: BLE001
                pass
    nxt = (max(nums) + 1) if nums else 1

    default_summary = summary or "Auto-filed by a scheduled cadence; triage to confirm or kill."
    chunks, filed = [], []
    for t in fresh:
        iid = f"IDEA-{nxt:03d}"
        nxt += 1
        filed.append(iid)
        safe_t = str(t).replace('"', "'")          # title is controlled, but be defensive
        safe_s = str(default_summary).replace('"', "'")
        chunks.append(
            f"\n  - id: {iid}\n"
            f'    title: "{safe_t}"\n'              # QUOTED — titles contain colons
            f"    raised_by: {raised_by}\n"
            f"    date: {today}\n"
            f"    source: {source}\n"
            f'    summary: "{safe_s}"\n'
            f"    description: >-\n"
            f"      A scheduled cadence found: {safe_t.lower()}. This is a SURFACED finding,\n"
            f"      not an action taken — investigate and triage (promote / merge / kill).\n"
        )

    ideas_path = SYSTEM_DIR / "ideas.yaml"
    if not ideas_path.exists():
        return []
    existing = ideas_path.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"
    ideas_path.write_text(existing + "".join(chunks), encoding="utf-8")
    # Safety net: NEVER leave ideas.yaml unparseable. Roll back if the append broke it.
    try:
        import yaml as _y

        _y.safe_load(ideas_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        ideas_path.write_text(existing, encoding="utf-8")
        return []

    # SYS-057: also write a guard-visible `captured` audit entry per filed idea. The SYS-025 id
    # guard derives next-IDEA from the MAX id across id:/ref: in ALL THREE stores; without a ref:
    # entry a cadence-filed id lives only in ideas.yaml, so once it's promoted + removed the id
    # vanishes from the guard's view and can be re-minted. Prepend (newest-first), TEXT-only +
    # rollback-safe, exactly like the Capture job and the ideas append above.
    audit_path = SYSTEM_DIR / "audit-log.yaml"
    if audit_path.exists():
        aud = audit_path.read_text(encoding="utf-8")
        ki = aud.find("entries:")
        nl = aud.find("\n", ki) if ki != -1 else -1
        if nl != -1:
            block = "".join(
                f"  - date: {today}\n"
                f"    ref: {iid}\n"
                f"    event: captured\n"
                f'    detail: "Auto-filed by the {source} cadence; triage the inbox (SYS-057 guard-visible capture)."\n'
                for iid in filed
            )
            insert_at = nl + 1
            new_aud = aud[:insert_at] + block + aud[insert_at:]
            audit_path.write_text(new_aud, encoding="utf-8")
            try:
                import yaml as _y2

                _y2.safe_load(audit_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 — never leave audit-log unparseable
                audit_path.write_text(aud, encoding="utf-8")
    return filed


def write_digest(subfolder: str, slug: str, lines: list[str], today: str) -> Path:
    """Write the digest markdown to system/digests/<subfolder>/<today>-<slug>.md
    and render an HTML sibling. Returns the markdown path.

    Each cadence gets its own digests subfolder so the four cadences never
    collide on a shared <date>.md (the weekly system-health digest owns the
    top-level system/digests/<date>.md)."""
    digests_dir = SYSTEM_DIR / "digests" / subfolder
    digests_dir.mkdir(parents=True, exist_ok=True)
    out = digests_dir / f"{today}-{slug}.md"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    _render_html(out)
    return out


def _render_html(md_path: Path) -> None:
    """Best-effort render of a digest md to HTML via the render-html skill.
    Failure is swallowed — the markdown digest is the source of truth."""
    try:
        subprocess.run(
            [sys.executable, str(SKILLS / "render-html" / "render.py"),
             "--markdown", str(md_path), "--template", "base",
             "--output", str(md_path.with_suffix(".html"))],
            cwd=str(ROOT), capture_output=True, timeout=60,
        )
    except Exception:  # noqa: BLE001
        pass


def discover_tenants() -> list[str]:
    """Tenants = the set named by campaign.yaml `tenant:` keys, intersected with
    those that actually have a playbook in tenant-brand/. Read-only."""
    import re

    tenants: set[str] = set()
    for cy in sorted(CAMPAIGNS_DIR.glob("*/campaign.yaml")):
        try:
            for line in cy.read_text(encoding="utf-8").splitlines():
                m = re.match(r'^tenant:\s*["\']?([A-Za-z0-9_-]+)', line)
                if m:
                    tenants.add(m.group(1))
                    break
        except Exception:  # noqa: BLE001
            continue
    return sorted(tenants)


def campaigns_for_tenant(tenant: str) -> list[Path]:
    """Campaign dirs whose campaign.yaml declares `tenant: <tenant>`. Read-only."""
    import re

    out = []
    for cy in sorted(CAMPAIGNS_DIR.glob("*/campaign.yaml")):
        try:
            for line in cy.read_text(encoding="utf-8").splitlines():
                m = re.match(r'^tenant:\s*["\']?([A-Za-z0-9_-]+)', line)
                if m:
                    if m.group(1) == tenant:
                        out.append(cy.parent)
                    break
        except Exception:  # noqa: BLE001
            continue
    return out
