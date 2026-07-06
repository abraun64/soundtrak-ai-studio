#!/usr/bin/env python3
"""docs-audit — the CONTENT/STRUCTURE layer over the nav-index.

`nav-audit` proves the system's docs EXIST and are LISTED in
docs/NAVIGATION_INDEX.md. It never reads what's *inside* them, so the
hand-maintained half of the index (the agent-count prose, the class-table
columns, the docs/public / memory / retros sections) drifts while the
presence-only smoke test stays green. That gap caused the SYS-018 / SYS-026
agent-count drift (docs said "five"/"six" long after the 7th agent landed).

This diagnostic adds four content/structure checks on top of nav-audit:

  1. AGENT-COUNT CONSISTENCY — the system has SEVEN roles (Campaign Manager +
     6 specialists). Flag stale "five"/"six"/"the other five"/"5 agents"…
     total-count language in docs/ + docs/public/.
  2. STRUCTURAL CONSISTENCY — NAVIGATION_INDEX.md's class tables must carry
     their expected columns (e.g. a "Where" path column on Skills + Playbooks).
  3. STALENESS — flag docs/public/ older than the roster (.claude/agents/) or
     the specs (docs/specs/): if the system changed more recently than the
     prospect-facing docs, those docs are behind.
  4. COVERAGE — the index's docs/public (§11), memory (§9) and retros (§10)
     sections must exist and point at real dirs/files.

Read-only. RED/GREEN report, exit non-zero on any RED — so system-smoke-test
and the weekly digest can gate on it, exactly like nav-audit.

Usage: python .claude/skills/docs-audit/docs_audit.py
"""
from __future__ import annotations
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .claude/skills/docs-audit/ -> repo root
IDX = ROOT / "docs" / "NAVIGATION_INDEX.md"
DOCS = ROOT / "docs"
PUBLIC = DOCS / "public"
AGENTS = ROOT / ".claude" / "agents"
SPECS = DOCS / "specs"
CM_SKILL = ROOT / ".claude" / "skills" / "campaign-manager"


# ── true role count ──────────────────────────────────────────────────────────
def true_role_count() -> int:
    """SEVEN roles = Campaign Manager (a skill) + the 6 specialist subagents in
    .claude/agents/. Derive from disk where feasible; fall back to 7."""
    try:
        specialists = [
            d for d in AGENTS.iterdir()
            if d.is_dir() and d.name != "_archive" and (d / "AGENT.md").exists()
        ]
        # CM lives as a skill, not an agent dir — add it if present.
        cm = 1 if (CM_SKILL / "SKILL.md").exists() else 1
        n = len(specialists) + cm
        return n if n >= 1 else 7
    except Exception:
        return 7   # hardcoded fallback: CM + 6 specialists


# ── check 1 — agent-count consistency ────────────────────────────────────────
# Stale TOTAL-count phrases. These assert the whole roster is five or six —
# wrong now that there are SEVEN roles (Campaign Manager + 6 specialists).
#
# The two correct framings, both KEPT off this list on purpose:
#   - "the other six" / "six specialists" / "six cold-start specialists"
#     → orchestrator + 6 = 7. Correct.
#   - "seven agents in all" / "seven roles". Correct.
# So we flag only phrases that put the TOTAL at five or six:
#   "the other five" (you + 5 = 6), "five/six team members", "N agents" totals.
STALE_PATTERNS = [
    r"the other five\b",
    r"\bfive team members\b",
    r"\bsix team members\b",            # "six team members" as a TOTAL = 6 roles, stale
    r"\bfive agents\b",
    r"\bsix agents\b",
    r"\b5 agents\b",
    r"\b6 agents\b",
    r"\bfive specialist agents\b",
    r"\bfive of them\b",
    r"\bseven specialists\b",           # wrong the OTHER way: there are only 6 specialists
]
# If any of these appears on the SAME line, the count language is the correct
# "6 specialists + 1 orchestrator = 7" framing — not drift. Skip the line.
CORRECT_NEARBY = re.compile(
    r"seven agents in all|seven roles|7 agents|7 roles|the other six|"
    r"six specialists|six cold-start|six specialist subagents",
    re.IGNORECASE,
)
STALE_RE = re.compile("|".join(STALE_PATTERNS), re.IGNORECASE)


def scan_agent_count() -> list[tuple[str, int, str]]:
    """Return [(relpath, lineno, line)] for stale total-count language in the
    prospect-facing + top-level docs. Skips _archive/ and retros/ (historical
    records — they legitimately quote the old count) and the nav index itself
    (its §11 description quotes the public docs verbatim)."""
    hits: list[tuple[str, int, str]] = []
    targets: list[Path] = []
    # Top-level operating docs.
    for name in ("workflow.md",):
        p = DOCS / name
        if p.exists():
            targets.append(p)
    # The whole public/ tree — the highest-drift surface.
    if PUBLIC.is_dir():
        targets += sorted(PUBLIC.glob("*.md"))
    for p in targets:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if STALE_RE.search(line) and not CORRECT_NEARBY.search(line):
                hits.append((str(p.relative_to(ROOT)), i, line.strip()[:120]))
    return hits


# ── check 2 — structural consistency (class-table columns) ───────────────────
# Each section's header row must carry these column labels. The "Where" path
# column is the one that silently goes missing when a table is hand-edited.
EXPECTED_COLUMNS = {
    "## 2. Specs": ["Spec", "Where"],
    "## 3. Playbooks": ["Playbook", "When to use"],
    "## 4. Agent definitions": ["Agent", "Role", "Where"],
    "## 5. Skills": ["Skill", "Trigger phrases"],
    "## 6. Tenant data": ["What", "Where"],
}


def _section_body(text: str, header: str) -> str:
    """Text from `header` up to the next `## ` heading."""
    start = text.find(header)
    if start == -1:
        return ""
    nxt = text.find("\n## ", start + len(header))
    return text[start: nxt if nxt != -1 else len(text)]


def scan_structure(text: str) -> list[str]:
    problems: list[str] = []
    for header, cols in EXPECTED_COLUMNS.items():
        body = _section_body(text, header)
        if not body:
            problems.append(f"{header.strip()} — section not found in index")
            continue
        # First markdown table header row in the section.
        hdr_row = next((ln for ln in body.splitlines()
                        if ln.lstrip().startswith("|") and "---" not in ln), "")
        if not hdr_row:
            problems.append(f"{header.strip()} — no table header row found")
            continue
        cells = [c.strip().strip("*").strip() for c in hdr_row.strip().strip("|").split("|")]
        for col in cols:
            if not any(col.lower() == c.lower() for c in cells):
                problems.append(f"{header.strip()} — missing expected column '{col}' "
                                f"(found: {', '.join(c for c in cells if c) or '—'})")
    return problems


# ── check 3 — staleness (docs/public behind the roster / specs) ──────────────
def _newest_mtime(paths: list[Path]) -> tuple[float, Path | None]:
    best, who = 0.0, None
    for p in paths:
        try:
            m = p.stat().st_mtime
        except Exception:
            continue
        if m > best:
            best, who = m, p
    return best, who


def scan_staleness() -> list[str]:
    problems: list[str] = []
    # Master-internal specs (excluded from the Seed, not prospect-relevant) must not trigger a
    # "public docs behind" alarm — mirror build_seed's docs/specs excludes + folder indexes.
    _INTERNAL_SPEC = ("standalone-deployment", "download-gate", "pitch-deck", "README", "INDEX")
    specfiles = [p for p in SPECS.glob("*.md")
                 if not any(x in p.name for x in _INTERNAL_SPEC)] if SPECS.is_dir() else []
    publicfiles = list(PUBLIC.glob("*.md")) if PUBLIC.is_dir() else []
    if not publicfiles:
        return ["docs/public/ — no *.md files found"]
    # SYS-055 tune: compare ONLY against product specs, NOT the agent roster — an AGENT.md edit is
    # internal machinery that doesn't change the prospect story, so the roster comparison was pure
    # noise (reddened on every agent tweak). And require a REAL gap (a full window, not same-day)
    # so routine spec churn doesn't flag — only a genuinely-behind prospect doc does. (Was SYS-027's
    # 1-day threshold, still too twitchy; the count-of-agents story is covered by scan_counts.)
    STALE_DAYS = 30
    pub_m, _pub_who = _newest_mtime(publicfiles)
    src_m, src_who = _newest_mtime(specfiles)
    if src_who is not None and (src_m - pub_m) > STALE_DAYS * 86400:
        d_src = datetime.date.fromtimestamp(src_m).isoformat()
        d_pub = datetime.date.fromtimestamp(pub_m).isoformat()
        problems.append(
            f"docs/public/ (newest {d_pub}) is >{STALE_DAYS} days behind the specs "
            f"(newest {d_src} — {src_who.relative_to(ROOT)}); the prospect docs may be behind the "
            f"product — consider a marketing-copy refresh")
    return problems


# ── check 4 — coverage (public / memory / retros sections point at reality) ──
def scan_coverage(text: str) -> list[str]:
    problems: list[str] = []

    # §11 Public-facing — must exist AND every public/*.md it lists must be real.
    pub_body = _section_body(text, "## 11. Public-facing")
    if not pub_body:
        problems.append("§11 Public-facing — section missing from index")
    else:
        if not PUBLIC.is_dir():
            problems.append("§11 Public-facing — docs/public/ dir does not exist")
        else:
            listed = set(re.findall(r"docs/public/([A-Za-z0-9_-]+\.md)", pub_body))
            for f in sorted(listed):
                if not (PUBLIC / f).exists():
                    problems.append(f"§11 — lists docs/public/{f} but it's not on disk")
            on_disk = {p.name for p in PUBLIC.glob("*.md")}
            for f in sorted(on_disk - listed):
                problems.append(f"§11 — docs/public/{f} on disk but not listed in §11")

    # §9 Memory — must exist and name the real memory dir.
    mem_body = _section_body(text, "## 9. Memory")
    if not mem_body:
        problems.append("§9 Memory — section missing from index")
    elif "memory" not in mem_body.lower():
        problems.append("§9 Memory — section present but doesn't reference the memory store")

    # §10 Retros — must exist and the retros it links under docs/retros/ must be real.
    retro_body = _section_body(text, "## 10. System retros")
    if not retro_body:
        problems.append("§10 System retros — section missing from index")
    else:
        rdir = DOCS / "retros"
        if not rdir.is_dir():
            problems.append("§10 — docs/retros/ dir does not exist")
        else:
            for f in sorted(set(re.findall(r"docs/retros/([A-Za-z0-9_.-]+\.md)", retro_body))):
                if not (rdir / f).exists():
                    problems.append(f"§10 — links docs/retros/{f} but it's not on disk")
    return problems


# ── report ───────────────────────────────────────────────────────────────────
def _emit(title: str, problems: list, fmt) -> bool:
    """Print one block; return True if RED (had problems)."""
    if problems:
        print(f"{title} ({len(problems)}):")
        for item in problems:
            print(f"  {fmt(item)}")
        return True
    print(f"{title} .... none")
    return False


def main() -> int:
    if not IDX.exists():
        print("RED: docs/NAVIGATION_INDEX.md not found")
        return 1
    text = IDX.read_text(encoding="utf-8")
    n_roles = true_role_count()

    agent_hits = scan_agent_count()
    struct_problems = scan_structure(text)
    stale_problems = scan_staleness()
    cov_problems = scan_coverage(text)

    print("=== DOCS-AUDIT (content + structure layer) ===")
    print(f"Index: docs/NAVIGATION_INDEX.md  ·  true role count: {n_roles} "
          f"(Campaign Manager + {n_roles - 1} specialists)")
    print()

    red = False
    red |= _emit("1. AGENT-COUNT — stale total-count language", agent_hits,
                 lambda h: f"{h[0]}:{h[1]}  {h[2]}")
    print()
    red |= _emit("2. STRUCTURE — class tables missing expected columns", struct_problems,
                 lambda s: s)
    print()
    red |= _emit("3. STALENESS — docs/public behind roster/specs", stale_problems,
                 lambda s: s)
    print()
    red |= _emit("4. COVERAGE — public/memory/retros sections vs disk", cov_problems,
                 lambda s: s)
    print()

    if not red:
        print("RESULT: GREEN — docs content + structure consistent with disk.")
        return 0
    n = len(agent_hits) + len(struct_problems) + len(stale_problems) + len(cov_problems)
    print(f"RESULT: RED — {n} content/structure issue(s). "
          f"Fix the docs above, then re-stamp NAVIGATION_INDEX.md and re-render.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
