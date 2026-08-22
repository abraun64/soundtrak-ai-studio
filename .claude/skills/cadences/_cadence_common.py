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
except ImportError:  # noqa: BLE001 — never let path resolution crash a read-only cadence
    DATA = ROOT

SYSTEM_DIR = DATA / "system"
SKILLS = ROOT / ".claude" / "skills"
# SYS-144 — killed cadence findings. A kill REMOVES the idea from ideas.yaml, so without a
# tombstone there is nothing left to dedupe against and the finding returns on the next run.
TOMBSTONES = SYSTEM_DIR / "cadence-tombstones.yaml"
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


def fingerprints_of(record) -> set:
    """The finding(s) a record owns. `fingerprint:` is a string OR a list, because a MERGE
    hands a ticket everything the records folded into it were tracking — after merging an idea
    and a duplicate ticket into SYS-146 it owns three findings, and a single-value field would
    have silently dropped two of them, releasing both to refile on the next run. The owning
    ticket holding all of them is also what makes the release correct: when it closes, every
    finding it absorbed becomes raisable again together."""
    fp = record.get("fingerprint")
    values = fp if isinstance(fp, list) else [fp]
    return {str(v).strip() for v in values if v and str(v).strip()}


# SYS-144 — WHICH tickets suppress a refile. An OPEN ticket (todo / in_progress) means the
# finding is already on the board. A KILLED ticket means the operator decided against it. But a
# DONE ticket means the problem was FIXED — if a cadence detects it again that is a NEW
# occurrence and must be raised, not swallowed. (The old title-dedupe suppressed on done too,
# which quietly turned "we fixed it once" into "never tell me again".)
_SUPPRESSING_STATUSES = ("todo", "in_progress", "killed")


def _suppresses(rec) -> bool:
    return str(rec.get("status", "todo")).strip().lower() in _SUPPRESSING_STATUSES


def load_tombstones() -> set[str]:
    """SYS-144 — fingerprints of cadence findings the operator has KILLED. Read-only; an
    absent or malformed file means "no tombstones", never a crash."""
    out = set()
    for e in load_yaml_items(TOMBSTONES, "entries"):
        out |= fingerprints_of(e)
    return out


def add_tombstone(fingerprint: str, ref: str, today: str, reason: str = "") -> bool:
    """Record a KILLED cadence finding so it stays killed. TEXT-append + parse-then-rollback,
    like every other write in this module. Returns True if written (False if already present,
    or on rollback). Called by the System Manager triage job via tombstone.py."""
    fingerprint = str(fingerprint).strip()
    if not fingerprint or fingerprint in load_tombstones():
        return False
    if not TOMBSTONES.exists():
        TOMBSTONES.write_text(
            "# Killed cadence findings (SYS-144).\n"
            "#\n"
            "# A cadence dedupes what it files against open ideas, open tickets, AND this list.\n"
            "# Killing an idea removes it from ideas.yaml, which leaves nothing to match on, so a\n"
            "# killed finding used to return on the very next run. Its FINGERPRINT lives here\n"
            "# instead: a stable <cadence>:<category>[:<scope>] key that survives retitling.\n"
            "#\n"
            "# Written by the triage job via: python .claude/skills/cadences/tombstone.py\n"
            "# To let a finding be raised again, delete its entry.\n"
            "entries:\n", encoding="utf-8")
    existing = TOMBSTONES.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"
    safe_r = str(reason or "Killed at triage.").replace('"', "'")
    TOMBSTONES.write_text(
        existing
        + f'  - fingerprint: "{fingerprint}"\n'
        + f"    ref: {ref}\n"
        + f"    date: {today}\n"
        + f'    reason: "{safe_r}"\n',
        encoding="utf-8")
    try:
        import yaml as _y

        _y.safe_load(TOMBSTONES.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — never leave the tombstone store unparseable
        TOMBSTONES.write_text(existing, encoding="utf-8")
        return False
    return True


def file_new_ideas(new_titles: list[str], raised_by: str, today: str,
                   summary: str = "", source: str = "cadence",
                   fingerprint: "str | list[str] | None" = None) -> list[str]:
    """Append deduped idea entries to system/ideas.yaml as TEXT.

    Mirrors the weekly-digest helper exactly: preserves the file header/comments
    (no safe_dump), QUOTES the title (idea titles contain colons), and rolls back
    if the append ever leaves ideas.yaml unparseable.

    DEDUPE IS BY FINGERPRINT (SYS-144), not by title. `fingerprint` is a stable
    `<cadence>:<category>[:<scope>]` key — one per title, or one string applied to all —
    matched against the `fingerprint:` of every open idea, every backlog ticket, and the
    killed-findings tombstone store. Title matching stays as a fallback for records that
    predate fingerprints, but it must never be the primary key, because the title is the
    part that CHANGES:
      - counts live in it ("31 asset(s)..." vs "32 asset(s)..."), so the same standing
        finding refiled whenever the number moved;
      - triage MANDATES sharpening the title on promote, so every promoted finding refiled
        on the next run — the two rules were in direct conflict;
      - a kill deletes the record outright, so a killed finding had nothing to match at all.
    Observed live 2026-08-22: IDEA-063 (promoted to SYS-143) and a finding killed on
    2026-08-06 both refiled within one session.

    Counts belong in the SUMMARY. Never put them in the fingerprint.

    Returns the list of filed IDEA-ids ([] if nothing new or on rollback)."""
    if not new_titles:
        return []

    fps = fingerprint if isinstance(fingerprint, list) else [fingerprint] * len(new_titles)
    fps = [str(f).strip() if f else "" for f in fps] + [""] * len(new_titles)

    ideas = load_yaml_items(SYSTEM_DIR / "ideas.yaml")
    backlog = load_yaml_items(SYSTEM_DIR / "backlog.yaml")
    # PRIMARY key — survives retitling, count drift, promotion and kill.
    fp_seen = set()
    for rec in ideas:
        fp_seen |= fingerprints_of(rec)
    for rec in backlog:
        if _suppresses(rec):
            fp_seen |= fingerprints_of(rec)
    fp_seen |= load_tombstones()
    # FALLBACK key — only reaches records filed before fingerprints existed.
    seen = {str(i.get("title", "")).strip().lower() for i in ideas} | \
           {str(b.get("title", "")).strip().lower() for b in backlog}

    fresh, fresh_fps = [], []
    for t, fp in zip(new_titles, fps):
        key = str(t).strip().lower()
        if not key:
            continue
        if fp:
            if fp in fp_seen:
                continue
            fp_seen.add(fp)
        elif key in seen:
            continue
        seen.add(key)
        fresh.append(t)
        fresh_fps.append(fp)
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
    for t, fp in zip(fresh, fresh_fps):
        iid = f"IDEA-{nxt:03d}"
        nxt += 1
        filed.append(iid)
        safe_t = str(t).replace('"', "'")          # title is controlled, but be defensive
        safe_s = str(default_summary).replace('"', "'")
        # SYS-144: the fingerprint is the dedupe key. Triage MUST carry it onto the ticket on
        # promote (see the System Manager triage job) or the finding refiles despite the ticket.
        fp_line = f'    fingerprint: "{fp}"\n' if fp else ""
        chunks.append(
            f"\n  - id: {iid}\n"
            f'    title: "{safe_t}"\n'              # QUOTED — titles contain colons
            f"{fp_line}"
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
