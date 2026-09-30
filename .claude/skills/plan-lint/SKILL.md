---
name: plan-lint
description: >-
  Deterministic structure check on a campaign Plan before it reaches the operator — declared
  Launch/Ongoing setting, wave windows in order, row target dates inside their wave, permanent row
  ids, a runnable Check on every setup row, and the Plan's channels matching the gallery's. Run it
  alongside review-ready whenever a Plan is authored or edited. Triggers include "lint the plan",
  "check the plan", "is the plan ready to surface", "run plan-lint".
  DO NOT use for judging whether the plan is any GOOD — it checks structure, never strategy.
---

# plan-lint — the deterministic half of the Plan gate

```bash
python .claude/skills/plan-lint/plan_lint.py campaigns/<slug>/plan.md
```

Exit 0 = clean, 1 = issues. Governed by [`docs/specs/plan.md`](../../../docs/specs/plan.md) (v4,
finding J).

## Why it exists

Four things on a long programme were being checked by eye, and two were caught only by accident:

| Check | Fails when | The real failure behind it |
|---|---|---|
| **Setting declared** | no `Setting:` line | the renderer guessed Launch/Ongoing from wording and filed January's ongoing builds into a group of their own |
| **Row ids permanent** | a duplicate `#` | `S17` was used twice; every dependency naming it silently repointed |
| **Setup rows have a `Check:`** | a `setup` row with no runnable test in Notes | the programme shipped with no mailing lists and no form routing, because the marketing item existed and looked complete |
| **Wave windows** | no dated window · a wave starting before the previous one · a wave where every row depends on a sibling | ten waves whose rollout could not be reconciled against the strategy |
| **Dates inside their wave** | a row dated outside its wave's window | checked by hand, every time |
| **Channels match the gallery** | a channel in the Plan but not `gallery-config.yaml`, or the reverse | setup rows filed under "Measurement" because it was the nearest bucket |

## How it reads a Plan

**Tables are parsed by header NAME, never by column position** — the asset list has fourteen columns
and they move between versions.

**A plan whose asset table can't be recognised is REPORTED, not skipped.** A lint that quietly
checks nothing is the failure it exists to prevent, so "no asset-list table found" is itself an
issue rather than a silent pass.

## What it does not do

It says nothing about whether the strategy is right, the assets are the right assets, or the copy is
any good. Pair it with:

- **`review-ready`** — the jargon lint plus a cold read, mandatory before any surface is shown.
- **`slop-lint`** — AI texture, if the Plan carries much prose.
- **`check-state`** — the Plan ↔ `asset.yaml` ↔ gallery drift check across the campaign.

An edit after a check re-opens that check: re-run it on anything you touch after it passed.
