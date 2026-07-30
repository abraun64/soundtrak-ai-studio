---
name: nav-audit
description: |
  Keeps docs/NAVIGATION_INDEX.md (the system's own dashboard of every doc) honest.
  Diffs the index against what's actually on disk — specs, skills, agents, playbooks —
  and reports anything on disk but missing from the index, any dead link the index names,
  a stale "Last updated" stamp, and the oldest-untouched docs (the ones most likely to have
  quietly gone out of date). Read-only; prints a red/amber/green report.

  TRIGGER when: the operator asks whether the navigation index / doc list is fresh or
  complete ("is the nav index up to date?", "run nav audit", "any docs missing from the
  index?", "which docs haven't been touched in a while?"); after adding/removing a spec,
  skill, agent, or playbook; periodically as system hygiene. Also runs automatically inside
  system-smoke-test (Layer 5).

  DO NOT TRIGGER for: campaign-content currency (use cm-audit), cross-campaign drift like
  zombie To-Do rows (use system-drift-watcher), or asset status drift (use check-state).
---

# Nav-audit

The navigation index (`docs/NAVIGATION_INDEX.md`) is the cold-start map of the whole system — and it's exactly the kind of doc that rots silently, because nothing forces it to update when a new spec/skill/agent lands. This is the forcing function.

## Run it

```
python .claude/skills/nav-audit/nav_audit.py
```

## What it checks

1. **Missing from index** — every `docs/specs/*.md`, `.claude/skills/*/SKILL.md`, `.claude/agents/*/AGENT.md`, and `docs/playbooks/*.md` on disk; flags any whose name the index doesn't reference. *(This is the load-bearing check — it catches the new doc you forgot to list.)*
2. **Dead links** — file paths the index names (real repo paths only — `<slug>` template patterns and memory-rule filenames are correctly ignored) that no longer exist on disk.
3. **Stale stamp** — the index's "Last updated" date is older than the newest doc it lists (→ re-stamp).
4. **Oldest docs** — the 8 least-recently-touched docs, as a "review for quiet rot" nudge.

## Exit code

`0` = green (index matches disk; a stale stamp alone is still 0 — it's a nudge). `1` = drift (missing entries or dead links) — so `system-smoke-test` Layer 5 gates on it.

## Fixing what it finds

Edit `docs/NAVIGATION_INDEX.md`: add a row for each missing doc (right section), fix/remove dead links, bump the **Last updated** stamp + version, then re-render (`render-html`). Re-run nav-audit to confirm green.

## Cross-references
`system-smoke-test` (runs this as Layer 5) · `cm-audit` (operator-surface currency) · `system-drift-watcher` (cross-campaign content drift).
