#!/usr/bin/env python3
"""SYS-049 — Phase-0 tenant-baseline operator surface.

A dedicated operator dashboard for a tenant's Phase-0 foundation (the brand tenant):

  1. Every canonical Phase-0 baseline item with its STATE — Complete (+ the date it
     was established), Drafted-not-yet-ratified (the artifact exists on disk but the
     tenant.yaml hasn't declared it), or To do (missing) — so it's unambiguous what
     remains before campaigns run at full strength.
  2. A BEST-PRACTICE LIBRARY block (the shared tenant/library) with a CTA that adds a
     new entry via a prompt to the assistant (the /library-add flow).
  3. An AUDIT HISTORY at the foot — a timeline of when each baseline item was
     established, derived from the artifacts' own dates.

Reads:  tenant-brand/<tenant>.yaml (+ the artifacts it points at on disk)
Writes: tenant-brand/<tenant>-phase0.md -> renders to <tenant>-phase0.html (index template)

Canonical baseline set: docs/specs/phase-0-tenant-baseline.md §The durable tenant compound.
Build-on, not rebuild: complements build-tenant-home.py (the tenant home links here).

  python .claude/skills/render-html/build-phase0-surface.py --tenant soundtrak
  python .claude/skills/render-html/build-phase0-surface.py --all
"""
from __future__ import annotations
import argparse
import html as _html
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RENDER = ROOT / ".claude" / "skills" / "render-html" / "render.py"
TENANT_BRAND = ROOT / "tenant-brand"

sys.path.insert(0, str(ROOT / ".claude" / "skills" / "render-html"))
import yaml  # noqa: E402

# The canonical Phase-0 compound (docs/specs/phase-0-tenant-baseline.md). `rel` resolves
# the expected source artifact per tenant; `shared` items are cross-tenant resources
# (not counted in the tenant's own completion ratio).
def canonical(slug: str) -> list[dict]:
    return [
        {"key": "brand_context", "title": "Brand Context (voice · visual · style)",
         "rel": f"tenant-brand/{slug}.md", "shared": False},
        {"key": "playbook", "title": "Playbook §0 (value prop · claim map · segment pointer)",
         "rel": f"tenant-brand/{slug}-playbook.md", "shared": False},
        {"key": "segments", "title": "Segment map",
         "rel": f"tenant-brand/{slug}-segments.md", "shared": False},
        {"key": "market", "title": "Market landscape + competitors",
         "rel": f"tenant-brand/{slug}-market.md", "shared": False},
        {"key": "compliance", "title": "Compliance Profile",
         "rel": f"tenant-brand/{slug}-compliance.md", "shared": False},
        {"key": "audience_truths", "title": "Audience truths (durable per-segment tensions)",
         "rel": f"tenant-brand/{slug}-audience-truths.md", "shared": False},
        {"key": "integrations", "title": "Tech stack (integrations)",
         "rel": f"tenant/{slug}/integrations.yaml", "shared": False},
        {"key": "library", "title": "Best-practice asset library",
         "rel": "tenant/library/entries", "shared": True},
        {"key": "research_library", "title": "Research library",
         "rel": "tenant/research-library", "shared": True},
    ]

_DATE_PATTERNS = [
    r"[Aa]pproved[^\n]*?(\d{4}-\d{2}-\d{2})",
    r"[Ll]ast graduation\**\s*:?\**\s*(\d{4}-\d{2}-\d{2})",
    r"[Ll]ast updated\**\s*:?\**\s*(\d{4}-\d{2}-\d{2})",
    r"[Oo]nboarded[^\n]*?(\d{4}-\d{2}-\d{2})",
]


def artifact_date(path: Path) -> tuple[str, str]:
    """(YYYY-MM-DD, how) — prefer an Approved/Updated/Graduation/Onboarded date in the
    artifact header, else the first ISO date near the top, else the file's mtime."""
    try:
        if path.is_file() and path.suffix == ".md":
            head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:60])
            for pat in _DATE_PATTERNS:
                m = re.search(pat, head)
                if m:
                    return m.group(1), "established"
            m = re.search(r"(\d{4}-\d{2}-\d{2})", head)
            if m:
                return m.group(1), "dated"
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d"), "file date"
    except Exception:  # noqa: BLE001
        return "", ""


def _load_tenant(slug: str) -> dict | None:
    p = TENANT_BRAND / f"{slug}.yaml"
    if not p.exists():
        return None
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"  ERROR parsing {p}: {e}", file=sys.stderr)
        return None


def _declared(tenant: dict) -> dict:
    """key -> baseline entry, for items the tenant.yaml declares."""
    return {str(r.get("key")): r for r in (tenant.get("baseline") or []) if r.get("key")}


def assess(slug: str, tenant: dict) -> list[dict]:
    """Per canonical item: state in {complete, drafted, todo, broken}, date, link."""
    declared = _declared(tenant)
    rows = []
    for item in canonical(slug):
        src = ROOT / item["rel"]
        exists = src.exists() and (any(src.glob("*.md")) if src.is_dir() else True)
        entry = declared.get(item["key"])
        is_declared = bool(entry) and str(entry.get("status") or "present").lower() == "present"

        if item["shared"]:
            state = "complete" if exists else "todo"   # shared resources aren't ratified per-tenant
        elif is_declared and exists:
            state = "complete"
        elif is_declared and not exists:
            state = "broken"
        elif not is_declared and exists:
            state = "drafted"       # on disk but the tenant hasn't ratified it into the baseline
        else:
            state = "todo"

        date, how = (artifact_date(src) if exists else ("", ""))
        # An explicit completed_date on the yaml entry wins.
        if entry and entry.get("completed_date"):
            date, how = str(entry["completed_date"]), "established"

        # Link target: the yaml href (already tenant-brand-relative) if declared, else the
        # on-disk artifact resolved relative to this surface (which lives in tenant-brand/).
        href = None
        if entry and entry.get("href"):
            href = str(entry["href"])
        elif exists:
            if src.is_dir():
                idx = next((c for c in (src / "INDEX.html", src.parent / "INDEX.html") if c.exists()), None)
                href = ("../" + "/".join(idx.relative_to(ROOT).parts)) if idx else None
            else:
                target = src.with_suffix(".html") if src.with_suffix(".html").exists() else src
                relp = target.relative_to(ROOT)
                href = ("/".join(relp.parts[1:]) if relp.parts[0] == "tenant-brand"
                        else "../" + "/".join(relp.parts))

        rows.append({**item, "state": state, "date": date, "how": how, "href": href})
    return rows


def foundation_status(slug: str, tenant: dict) -> dict:
    """SYS-092 — the ONE Phase-0 completion computation, shared by the phase0 page AND
    the tenant home so they cannot disagree. Ratio is over the tenant's OWN (non-shared)
    canonical items; drafted/todo are the gaps. Returns the assessed rows too, so callers
    render from the same data."""
    rows = assess(slug, tenant)
    own = [r for r in rows if not r["shared"]]
    done = sum(1 for r in own if r["state"] == "complete")
    return {
        "done": done,
        "drafted": sum(1 for r in own if r["state"] == "drafted"),
        "todo": sum(1 for r in own if r["state"] == "todo"),
        "total": len(own),
        "pct": round(100 * done / len(own)) if own else 0,
        "rows": rows,
    }


_STATE = {
    "complete": ("✅", "Complete"),
    "drafted":  ("🟡", "Drafted — ratify into baseline"),
    "todo":     ("⬜", "To do"),
    "broken":   ("⚠️", "Declared but file missing"),
}


def _items_table(rows: list[dict]) -> str:
    out = ["| Baseline item | Status | Established | Open |",
           "|---|---|---|---|"]
    for r in rows:
        icon, label = _STATE[r["state"]]
        title = _html.escape(r["title"]) + (" _(shared)_" if r["shared"] else "")
        status = f"{icon} {label}"
        date = r["date"] if r["state"] in ("complete", "drafted") and r["date"] else "—"
        link = f"[open]({_html.escape(r['href'])})" if r["href"] else "—"
        out.append(f"| {title} | {status} | {date} | {link} |")
    return "\n".join(out)


def _library_block(slug: str) -> str:
    entries_dir = ROOT / "tenant" / "library" / "entries"
    index = ROOT / "tenant" / "library" / "INDEX.html"
    files = sorted(entries_dir.glob("*.md"), key=lambda p: -p.stat().st_mtime) if entries_dir.exists() else []
    n = len(files)
    recent = ", ".join(f"`{p.stem}`" for p in files[:5]) if files else "_none yet_"
    idx_link = "[browse the Library index](../tenant/library/INDEX.html)" if index.exists() else "_(no INDEX yet)_"
    prompt = (f"Add a best-practice example to the tenant library via /library-add. "
              f"Entry to add: [name the campaign or asset, the brand, WHY it is exemplary "
              f"for {slug}, and a source link].")
    prompt_js = prompt.replace("`", "").replace("\\", "\\\\").replace("'", "\\'")
    cta = (
        f'<button class="p0-cta" style="display:inline-block;margin:8px 0;padding:10px 16px;'
        f'background:#e63c3c;color:#fff;border:0;border-radius:6px;font-weight:600;cursor:pointer;'
        f'font-family:system-ui,sans-serif;" onclick="var t=\'{prompt_js}\';'
        f'if(window.sendPrompt){{sendPrompt(t);}}else{{if(navigator.clipboard)navigator.clipboard.writeText(t);'
        f'this.textContent=\'\\u2713 Prompt copied — paste it into Claude\';}}">'
        f'➕ Add a best-practice entry</button>'
    )
    return (
        f"**{n} entries** in the shared best-practice library — {idx_link}.\n\n"
        f"Most recent: {recent}.\n\n"
        f"{cta}\n\n"
        f"<small>The button sends the add-prompt straight to Claude when this page is opened in the "
        f"app; from a plain browser it copies the prompt for you to paste. Or just tell Claude: "
        f'"add to the library: …".</small>'
    )


def _audit_block(rows: list[dict]) -> str:
    dated = [r for r in rows if r["state"] in ("complete", "drafted") and r["date"]]
    dated.sort(key=lambda r: r["date"], reverse=True)
    if not dated:
        return "_No dated baseline artifacts yet._"
    out = ["| Date | Baseline item | Event |", "|---|---|---|"]
    for r in dated:
        ev = "established" if r["state"] == "complete" else "drafted (awaiting ratification)"
        out.append(f"| {r['date']} | {_html.escape(r['title'])} | {ev} |")
    return "\n".join(out)


def build(slug: str) -> int:
    tenant = _load_tenant(slug)
    if tenant is None:
        print(f"ERROR: tenant-brand/{slug}.yaml not found or unparseable", file=sys.stderr)
        return 1
    name = str(tenant.get("name") or slug)
    summary = str(tenant.get("summary") or "")
    st = foundation_status(slug, tenant)   # SYS-092 — shared with the tenant home
    rows = st["rows"]
    done, total, pct = st["done"], st["total"], st["pct"]
    gaps = ""
    if st["drafted"]:
        gaps += f" · {st['drafted']} drafted (not ratified)"
    if st["todo"]:
        gaps += f" · {st['todo']} still to do"

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# {name} — Phase 0 Baseline

**Last updated**: {stamp}     **Tenant**: `{slug}`     [← Tenant home]({slug}-home.html) · [← All campaigns](../campaigns/index.html)

{summary}

## Foundation status — {done}/{total} established ({pct}%){gaps}

_The durable per-business foundation every campaign inherits as FIXED INPUT. Built **once** at the tenant layer, cited per campaign (never re-built). Spec: [`phase-0-tenant-baseline.md`](../docs/specs/phase-0-tenant-baseline.md)._

{_items_table(rows)}

<small>✅ complete · 🟡 the artifact exists on disk but `{slug}.yaml` hasn't ratified it into the baseline (add it) · ⬜ to do · ⚠️ declared present but the file is missing. Established dates are read from each artifact's own header (Approved / Last updated / Onboarded), falling back to the file date.</small>

## Best-practice library

{_library_block(slug)}

## Audit history

{_audit_block(own)}

<small>Derived from each artifact's own date. Rebuild: `python .claude/skills/render-html/build-phase0-surface.py --tenant {slug}`.</small>
"""
    md_path = TENANT_BRAND / f"{slug}-phase0.md"
    md_path.write_text(md, encoding="utf-8")
    html_path = TENANT_BRAND / f"{slug}-phase0.html"
    res = subprocess.run(
        [sys.executable, str(RENDER), "--markdown", str(md_path),
         "--template", "index", "--output", str(html_path)],
        capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  render FAILED for {slug}: {res.stderr.strip()}", file=sys.stderr)
        return 1
    print(f"  Phase-0 surface: {md_path.name} -> {html_path.name}  "
          f"({done}/{total} established, {len(drafted)} drafted, {len(todo)} to do)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tenant", help="tenant slug (matches tenant-brand/<slug>.yaml)")
    g.add_argument("--all", action="store_true", help="build every tenant identity yaml")
    args = p.parse_args()
    if args.all:
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
        rc = 0
        for s in slugs:
            rc |= build(s)
        return rc
    return build(args.tenant)


if __name__ == "__main__":
    sys.exit(main())
