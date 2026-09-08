---
name: docs-audit
description: |
  The CONTENT + STRUCTURE layer over the navigation index — the half nav-audit
  can't see. Where nav-audit proves the docs EXIST and are LISTED, docs-audit
  reads what's INSIDE them: stale agent-count prose ("five"/"six" after the 7th
  agent landed), class-table columns that quietly went missing, docs/public that
  fell behind the roster/specs, and the hand-maintained index sections (public /
  memory / retros) drifting from disk. Read-only; prints a red/green report.

  TRIGGER when: the operator asks whether the docs CONTENT is current / accurate
  ("are the docs consistent?", "run docs audit", "is the agent count right
  everywhere?", "did the public docs fall behind?"); after adding an agent,
  editing the public docs, or restructuring an index table; periodically as
  system hygiene. Also runs automatically inside system-smoke-test (Layer 6) and
  the weekly digest.

  DO NOT TRIGGER for: presence/dead-link checks (use nav-audit — docs-audit
  assumes the docs exist and are listed); campaign-content currency (use
  cm-audit); cross-campaign drift (use system-drift-watcher).
---

# Docs-audit

`nav-audit` keeps the navigation index *complete* — every spec/skill/agent/playbook
on disk is listed, no dead links, stamp fresh. But it never opens a doc. So the
hand-maintained half of the system's documentation rots silently while the
smoke test stays green. That's exactly what caused the **SYS-018 / SYS-026
agent-count drift**: the system grew to SEVEN roles, but the prospect-facing docs
kept saying "five" / "six" and nothing flagged it.

docs-audit is the content layer that closes that gap. nav-audit stays as-is
(presence); docs-audit adds the four checks below (content + structure).

## Run it

```
python .claude/skills/docs-audit/docs_audit.py
```

## What it checks

1. **Agent-count consistency** — the system has SEVEN roles (Campaign Manager +
   6 specialists: Creative Director, Insights Manager, Governance Manager, Brand
   Manager, Producer, Marketing Forensic Analyst). The true count is derived from
   `.claude/agents/` + the CM skill (fallback: hardcoded 7). Scans `docs/workflow.md`
   + `docs/public/*.md` for stale total-count language ("the other five", "five
   team members", "six agents", …) and flags it. The correct framings
   ("the other six", "six specialists — seven agents in all") are whitelisted, so
   it won't false-positive on accurate prose.
2. **Structural consistency** — verifies each NAVIGATION_INDEX class table carries
   its expected columns (e.g. the **Where** path column on Specs / Agents / Tenant
   data, **Trigger phrases** on Skills, **When to use** on Playbooks). Flags a
   table that lost a column to a hand-edit.
3. **Staleness** — compares the newest mtime of `docs/public/*.md` against the
   newest of `.claude/agents/*/AGENT.md` (the roster) and `docs/specs/*.md`. If the
   roster or specs changed more recently than the public docs, the prospect-facing
   material is behind the system — flag it.
4. **Coverage** — the hand-maintained index sections must point at reality: §11
   Public-facing lists exactly the `docs/public/*.md` on disk (both directions),
   §9 Memory references the memory store, §10 System retros links only real
   `docs/retros/*.md` files.

## Exit code

`0` = green (content + structure consistent). `1` = RED (any stale count,
missing column, behind-the-roster public doc, or coverage mismatch) — so
`system-smoke-test` Layer 6 and the weekly digest gate on it, and persistent
failures auto-escalate to a ticket (SYS-010 pattern).

## Fixing what it finds

- **Agent-count**: edit the flagged doc line to the correct seven-role framing,
  then re-render (`render-html`).
- **Structure**: restore the missing column to the index table.
- **Staleness**: review the public docs against the changed roster/specs; refresh
  and re-render so their mtime catches up.
- **Coverage**: add/remove the index row so §9/§10/§11 match disk.

Then re-stamp `docs/NAVIGATION_INDEX.md` (Last updated + version) and re-run.

## Cross-references

`nav-audit` (presence + dead links — the layer below this) ·
`system-smoke-test` (runs this as Layer 6) · `cm-audit` (operator-surface
currency) · `system-drift-watcher` (cross-campaign content drift).
