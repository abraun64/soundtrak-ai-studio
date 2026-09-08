---
name: system-drift-watcher
description: |
  On-demand cross-campaign drift scan for the AI Marketing System.

  Checks all active campaigns for: stale dashboard Last-updated stamps,
  zombie To Do rows (items still listed but actually done), Producers
  in-flight longer than expected, memory rules with no propagation history,
  and spec cross-references that may be stale. Returns a per-campaign
  traffic-light report with specific items that need attention.

  TRIGGER when: start of a new session after a gap; before a retro; when
  something feels out of date but you can't pinpoint it; periodic maintenance
  check (~monthly).
  Common phrasings: "check system drift", "anything stale across campaigns?",
  "cross-campaign health check", "is everything up to date?", "run drift watcher".

  DO NOT TRIGGER for: single-campaign status checks (use that campaign's
  dashboard instead); routine session work.
---

# System Drift Watcher

**Version**: v0.1 scaffold · 2026-06-08
**Status**: Scaffold only — implementation deferred until first cross-campaign drift incident surfaces operator-blind.
**Owner**: CM (operator-triggered on demand via natural language)
**Replaces**: the previously-killed "Process Observer" persistent agent. This is on-demand, not persistent — avoids the overhead of a running background agent.

---

## What it checks

### Check 1 — Dashboard Last-updated stamps

For each active campaign: compare the dashboard's "Last updated" stamp against the newest file mtime in the campaign folder. If the gap is >3 days and the campaign is active, flag it.

Expected output: `gamma: dashboard says 2026-05-28 but newest file is 2026-06-05 — 8 days behind`

### Check 2 — Zombie To Do rows

For each active campaign: scan the To Do table for rows that reference assets or tasks whose status elsewhere says "Approved" or "Done." Flag any row where the task appears resolved but the row hasn't been removed.

Expected output: `soundtrak: To Do row "Asset #4 website deployment" still listed but asset.yaml shows status: Approved`

### Check 3 — Producers in-flight too long

For each campaign: check the "Producers in flight" section. If any Producer has been listed as in-flight for >7 days, flag it.

Expected output: `soundtrak: Producer for Asset #0 listed in-flight since 2026-05-28 (12 days) — returned or timed out?`

### Check 4 — Memory rules without propagation confirmation

Scan memory rule files for entries where the `## What to propagate` section lists targets that haven't been crossed off. (Heuristic: look for lines starting with `- [ ]` or `TODO:` in the propagation sections.)

Expected output: `feedback_X.md: propagation target docs/specs/plan.md listed but no confirmation it was updated`

### Check 5 — Spec cross-reference staleness

For each spec in `docs/specs/`: check if any cross-referenced files it mentions still exist at the referenced paths. Flag broken cross-references.

Expected output: `plan.md references docs/specs/phase-4-rollout.md which no longer exists (renamed)`

---

## Output format

```
=== CROSS-CAMPAIGN DRIFT SCAN ===
Date: YYYY-MM-DD

Gamma Foods LAUNCH (gamma-launch-2026q2)
  Dashboard stamp ................ OK (2026-06-05, 3 days)
  Zombie To Do rows .............. 1 ISSUE: "Deploy Asset #17" still listed; marked approved 2026-05-28
  Producers in-flight ............ OK (none)

Beta Corp (beta-corp-podcast-engine-2026q2)
  Dashboard stamp ................ OK (2026-06-04, campaign paused)
  Zombie To Do rows .............. OK
  Producers in-flight ............ OK (none)

THE SIGNAL (the-signal-amp-2026q2)
  Dashboard stamp ................ WARN: 4 days since last update; Wk 2 was due 2026-06-02
  Zombie To Do rows .............. 1 ISSUE: "Send launch update" still P1 — may be resolved?
  Producers in-flight ............ OK

SOUNDTRAK AI OVERVIEW (soundtrak-ai-system-overview-2026q2)
  Dashboard stamp ................ OK (2026-06-04, 4 days)
  Zombie To Do rows .............. OK
  Producers in-flight ............ OK

MEMORY RULES
  Propagation checks ............. OK (no outstanding TODO markers found)

SPEC CROSS-REFERENCES
  Broken paths ................... 0

RESULT: 2 ISSUES, 1 WARNING — see above
```

---

## Implementation notes (for when this is built)

- Parse dashboard MDs for the `Last updated:` field using the existing `parse_dashboard_last_updated()` function in `stop.py`
- Scan To Do tables for task names that appear as approved in the asset list or history
- Read "Producers in flight" sections from dashboard MDs
- For memory rule propagation: grep for `- [ ]` in `## What to propagate` sections
- For spec cross-references: extract all internal links from spec MDs and verify path existence

---

## Deferred until first blind incident

Build when: a cross-campaign drift incident surfaces that the operator only catches by accident, and which this check would have flagged.

Per `docs/specs/retro.md` queued-cleanup-decay: scaffold captures the design; implementation waits for the trigger moment.
