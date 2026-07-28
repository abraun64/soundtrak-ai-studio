#!/usr/bin/env python3
"""
Surface-honesty guard (SYS-059) — a ✅ on an operator surface may sit ONLY on a
genuinely-gated artifact.

Behavioural rule it enforces (docs/workflow.md, "CM rules of orchestration" rule 8):
  "✅ on any operator surface means an explicit operator verdict — nothing else.
   Produced-but-not-gated artifacts (the Insight Brief, the concept moodboard, the
   concept trio menu) are inputs; they never carry an approval ✅. The only gated
   artifacts are the Brief, the concept pick, the Plan, finished assets, and the
   Phase-5/6 plans."

Concrete pain (real retro): CM stamped ✅ on the Insight Brief / concept-trio menu /
moodboard on the dashboard, fabricating an approval and eroding gallery trust. This is
the AUTOMATED backstop.

What it scans, per campaign:
  - campaigns/<slug>/<slug>.md   — the dashboard: phase table + artifact links
  - campaigns/<slug>/campaign.yaml — phases[].artifacts[].title

What it flags: a ✅ ATTACHED TO AN ARTIFACT NAME that is NOT in the gated set.
  - In the dashboard md: a markdown link whose visible text carries a ✅ — `[Foo ✅](x)`.
    (A bare ✅ in prose / a status cell / a history-log row / a budget line is NOT an
    artifact approval, so it is out of scope — rule 8 is about ✅ ON AN ARTIFACT.)
  - In campaign.yaml: an artifact `title:` containing a ✅.

Gated/ungated decision (small allow/deny list + heuristics, easily extendable below):
  ALLOW (✅ legitimate) — Brief, Selected concept (the pick), Plan, finished assets,
    Phase-5/6 plans, gallery roll-up.
  DENY  (✅ fabricates approval) — concept trio/menu, moodboard, editorial backlog,
    research, influencer/outreach targets, and anything that reads as an ungated INPUT.
  CONDITIONAL — the Insight Brief (SYS-067): approved AS PART OF the Brief, so a ✅ on it
    is a violation ONLY when the Phase-1 Brief is not yet approved (a pre-approval tick).

Public entry point: `scan(data_root) -> list[Violation]`, so cm_audit.py can fold the
findings into its report. Also runnable standalone for a focused report:

    python .claude/skills/cm-audit/surface_honesty.py

Exit 0 = clean; exit 1 = at least one violation (printed inline).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a hard dep of the skill
    yaml = None

CHECK = "✅"  # ✅


class Violation(NamedTuple):
    campaign: str
    surface: str      # relative surface path, e.g. "soundtrak-…/dashboard.md"
    where: str        # "line 31" | "phase 2 · artifact 'Insight Brief ✅'"
    offending: str    # the offending "✅ <artifact>" text


# ── Gated / ungated classification ───────────────────────────────────────────
# Keep this list-driven and easily extendable. Matching is on the artifact NAME with
# the ✅ and surrounding markdown/punctuation stripped, lower-cased.
#
# GATED = the five things an operator actually approves. A ✅ here is honest.
GATED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bbrief\b",                       # the Brief (Phase-1 gate)
        r"\bselected\b",                    # "Selected concept" (the concept pick)
        r"concept.*\bpick\b|\bpick\b.*concept",
        r"\bplan\b",                        # the Plan (Phase-3 gate) + Phase-5/6 plans
        r"phase[\s\-]?[56]\b",              # Phase-5 / Phase-6 launch/measurement plans
        r"\bgallery\b",                     # the finished-asset roll-up
        r"\basset\b",                       # a finished, gated asset
        r"^\s*a\d+\b",                      # asset codes like "A4 · Edition #1"
    )
]

# UNGATED (deny) = produced INPUTS that must never carry an approval ✅. These take
# precedence over a coincidental gated-word match (e.g. "Insight Brief" contains
# "brief" but is an input, not the Brief).
UNGATED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        # NOTE: "insight brief" is intentionally NOT in this flat deny list. Post-SYS-067
        # the Insight Brief is approved AS PART OF the Brief, so its ✅ is legitimate ONCE
        # the Phase-1 Brief is approved. It is handled CONDITIONALLY in the scanners below
        # (flag a ✅ on it only when the Brief is not yet approved — a pre-approval tick).
        r"concept\s*trio",                  # the concept trio / menu
        r"\btrio\b",
        r"\bmenu\b",
        r"mood\s*board|moodboard",          # the concept moodboard
        r"editorial\s*backlog",             # editorial backlog / calendar
        r"editorial\s*calendar",
        r"\bresearch\b",                    # research inputs
        r"influencer\s*targets?",           # influencer / outreach target lists
        r"outreach\s*(list|targets?|kit)",
        r"\bfact[\s\-]?find\b",             # raw fact-find notes
        r"\bnotes?\b",
        r"\bdraft\b",
        r"considered.*cut|kill\s*register",
    )
]


def classify(name: str) -> str:
    """Return 'gated' | 'ungated' | 'unknown' for an artifact name.

    Deny (ungated) wins over allow — "Insight Brief" must not be rescued by the
    generic 'brief' allow rule. 'unknown' means no rule matched; unknown is NOT
    flagged (fail-open) so the guard never fabricates a false violation on a novel
    artifact name — extend the deny list when a new input type appears.
    """
    n = name.strip().lower()
    if _INSIGHT_BRIEF_RE.search(n):
        return "unknown"  # SYS-067: conditional — the scanners gate it on Brief approval
    for pat in UNGATED_PATTERNS:
        if pat.search(n):
            return "ungated"
    for pat in GATED_PATTERNS:
        if pat.search(n):
            return "gated"
    return "unknown"


# ── Insight Brief — conditional (SYS-067) ────────────────────────────────────
# The Insight Brief is approved AS PART OF the Brief. So a ✅ on it is legitimate ONCE
# the Phase-1 Brief is approved, and a violation only BEFORE that (a pre-approval / fabricated
# tick — the exact 2026-07-08 retro bug). Handled here, not in the flat deny list.
_INSIGHT_BRIEF_RE = re.compile(r"insight\s*brief", re.IGNORECASE)


def _brief_approved(campaign_dir: Path) -> bool:
    """True iff the campaign's Phase-1 (Brief) status reads as approved (starts with ✅
    or contains 'approved'). Used to allow a legitimate post-approval Insight Brief ✅."""
    if yaml is None:
        return False
    cy = campaign_dir / "campaign.yaml"
    if not cy.exists():
        return False
    try:
        data = yaml.safe_load(cy.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    for phase in (data.get("phases") or []):
        if isinstance(phase, dict) and str(phase.get("id")) == "1":
            s = str(phase.get("status") or "").lower()
            return ("✅" in s) or ("approved" in s)
    return False


# ── Extractors ───────────────────────────────────────────────────────────────
# A markdown link `[text](href)` whose visible text contains a ✅.
_MD_LINK_WITH_CHECK = re.compile(r"\[([^\]]*" + CHECK + r"[^\]]*)\]\(([^)]*)\)")


def _clean_link_text(text: str) -> str:
    """Strip the ✅ and markdown emphasis/punctuation to get the artifact name."""
    t = text.replace(CHECK, " ")
    t = re.sub(r"[\*_`]", "", t)            # markdown emphasis
    return t.strip(" \t·-—:")


def scan_dashboard_md(md: Path, slug: str, rel: str, campaign_dir: Path) -> list[Violation]:
    """Flag every markdown link whose visible text carries a ✅ on an ungated name.

    We deliberately look ONLY at ✅ inside a link's visible text — that is a ✅
    ATTACHED TO AN ARTIFACT. A bare ✅ in a status cell, history row, budget line, or
    prose is a verdict/marker, not an artifact approval, and is out of scope.
    The Insight Brief is a special case (SYS-067): a ✅ on it is a violation only when
    the Phase-1 Brief is not yet approved.
    """
    out: list[Violation] = []
    if not md.exists():
        return out
    brief_ok = None  # lazy: only resolve if we hit an Insight-Brief ✅
    for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        for m in _MD_LINK_WITH_CHECK.finditer(line):
            visible = m.group(1)
            name = _clean_link_text(visible)
            if classify(name) == "ungated":
                out.append(Violation(slug, rel, f"line {i}", f"{CHECK} {name}".strip()))
            elif _INSIGHT_BRIEF_RE.search(name):
                if brief_ok is None:
                    brief_ok = _brief_approved(campaign_dir)
                if not brief_ok:
                    out.append(Violation(slug, rel, f"line {i}",
                                         f"{CHECK} {name} (Brief not yet approved)".strip()))
    return out


def scan_campaign_yaml(cy: Path, slug: str, rel: str, campaign_dir: Path) -> list[Violation]:
    """Flag any phases[].artifacts[].title that carries a ✅ on an ungated name.
    Insight Brief is conditional (SYS-067): a violation only if the Brief isn't approved."""
    out: list[Violation] = []
    if yaml is None or not cy.exists():
        return out
    try:
        data = yaml.safe_load(cy.read_text(encoding="utf-8")) or {}
    except Exception:
        return out
    brief_ok = None
    for phase in (data.get("phases") or []):
        if not isinstance(phase, dict):
            continue
        pid = phase.get("id", "?")
        for art in (phase.get("artifacts") or []):
            title = art.get("title", "") if isinstance(art, dict) else str(art)
            if CHECK not in title:
                continue
            name = _clean_link_text(title)
            if classify(name) == "ungated":
                out.append(Violation(slug, rel, f"phase {pid} · artifact title", title.strip()))
            elif _INSIGHT_BRIEF_RE.search(name):
                if brief_ok is None:
                    brief_ok = _brief_approved(campaign_dir)
                if not brief_ok:
                    out.append(Violation(slug, rel, f"phase {pid} · artifact title",
                                         f"{title.strip()} (Brief not yet approved)"))
    return out


def scan(data_root: Path) -> list[Violation]:
    """Scan every campaign's operator surfaces. Returns all violations found."""
    camp = Path(data_root) / "campaigns"
    out: list[Violation] = []
    if not camp.is_dir():
        return out
    for c in sorted(camp.iterdir()):
        if not c.is_dir() or not (c / "assets").is_dir():
            continue
        slug = c.name
        md = c / f"{slug}.md"
        if not md.exists():
            md = c / "dashboard.md"
        out += scan_dashboard_md(md, slug, f"{slug}/{md.name}", c)
        out += scan_campaign_yaml(c / "campaign.yaml", slug, f"{slug}/campaign.yaml", c)
    return out


# ── Standalone report ────────────────────────────────────────────────────────
def _resolve_data_root() -> Path:
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / ".claude" / "lib"))
    try:
        import repo_paths
        return repo_paths.data_root(root)
    except Exception:
        return root


def main() -> int:
    try:  # Windows consoles default to cp1252, which can't encode ✅
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    violations = scan(_resolve_data_root())
    print("=== SURFACE-HONESTY GUARD (SYS-059) ===")
    print("A ✅ on an operator surface may sit only on a gated artifact")
    print("(Brief · Selected concept · Plan · finished assets · Phase-5/6 plans).\n")
    if not violations:
        print("RESULT: CLEAN — no ✅ on an ungated artifact.")
        return 0
    print(f"RESULT: {len(violations)} VIOLATION(S) — ✅ fabricated on an ungated input:\n")
    for v in violations:
        print(f"  {v.campaign} · {v.surface} · {v.where}\n      offending: \"{v.offending}\"")
    return 1


if __name__ == "__main__":
    sys.exit(main())
