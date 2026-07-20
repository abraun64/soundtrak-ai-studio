---
name: brief-lint
description: >-
  Checks a campaign Brief against the LOCKED canonical section template (docs/specs/brief.md
  §"Canonical section order") — flags missing mandatory sections, non-canonical headings that
  should fold into "Anything else", out-of-order sections, and a missing Approval-record block.
  The STRUCTURE gate the Campaign Manager runs before surfacing a Brief (sibling to review-ready,
  which is the READABILITY gate). Invoke before any "surface the Brief" step, or on demand:
  "lint this brief", "is this brief canonical?", "check the brief structure".
---

# brief-lint — the canonical Brief structure gate (SYS-085)

Briefs drifted campaign-to-campaign (the buildlog brief dropped Business objective / Tech-setup /
Roles / Cadence / Approval-record and added its own headings; acme followed the older spec). This
gate makes every Brief use the same sections, in the same order, with the same names — so any
reader who didn't write it can navigate any campaign's Brief the same way.

## The locked template

The canonical order + names live in **`docs/specs/brief.md` §"Canonical section order"** (the single
source of truth): Why this campaign · Business objective · The offer · Audience · Insights that
matter · How to reach them · Single-minded proposition · Goal & KPI · Brand context · Mandatories ·
Budget · Timeline · Tech setup · Roles · Cadence · **Anything else** · **Approval record**.
Campaign-specific extras go in "Anything else", never as new top-level headings.

## Run it

```
python .claude/skills/brief-lint/brief_lint.py <brief.md> [<brief.md> ...]   # exit 1 if any issue
```
Reports, per brief: MISSING mandatory sections · NON-CANONICAL headings (fold into "Anything else"
or rename) · sections OUT OF ORDER · a missing Approval record. Optional sections (Insights / How
to reach them / Tech setup / Roles / Cadence / Anything else) don't trigger a "missing" error.

## When it runs — MANDATORY pre-surface (with review-ready)

The CM runs this on the Brief immediately before surfacing it for approval — same shape as
`review-ready` (readability) and `content-subedit` (copy voice). brief-lint checks the Brief's
STRUCTURE; review-ready checks its READABILITY. A Brief that fails either gate is fixed before it's
surfaced. On a flag: re-author the section into canonical order / fold the extra into "Anything
else" / add the missing section (or the Approval-record block), then re-run.

## Extending it

The canonical list + the heading-match aliases live in `brief_lint.py` (CANONICAL). When the spec's
canonical order changes, update both together.
