---
name: check-state
description: Walks every asset folder in one campaign or all campaigns and reports any drift between asset.yaml status, the numeric-prefix asset record, preview.md, and the dashboard. Surfaces the bug class where status updates land in one layer but not others. Pair with status-propagator to fix what it finds.
---

# check-state

**Read-only drift detector. Run before review sessions to catch what status-propagator hasn't been pointed at yet.**

## When to use

- Before any operator review session — surface any pre-existing drift so it doesn't confuse the review
- After hand-editing asset metadata — verify nothing got missed
- During retros — catch latent issues across the whole project
- Pre-launch — sanity check that all approved assets are consistently marked Approved everywhere

## Usage

```bash
# One campaign
python .claude/skills/check-state/check.py --campaign gamma-launch-2026q2

# All campaigns under campaigns/
python .claude/skills/check-state/check.py --all-campaigns
```

## What it reports

Per asset folder:
- yaml status, record status, preview status, drift flag

Then per campaign:
- Dashboard cross-check: any approved assets surfacing as "Queued", "in flight", or "Gate Asset #N" rows in the dashboard md
- **Plan roster cross-check (Layer E, added 2026-06-09)**: every numeric-prefix asset folder on disk must have a `| <id> |` row in plan.md — catches operator-added assets that never got a Plan row (the Plan-rot class caught live on Soundtrak 2026-06-09)
- **campaign.yaml cross-check (Layer F, added 2026-06-09)**: phase titles claiming "N assets" checked against disk count; `status_mode: derive_blocks_launch` with zero `blocks_launch` declarations anywhere flagged as an unwired input (previously rendered a false "✅ All launch blockers complete"; the renderer in operator_actions.py now also self-reports this instead of lying)

Exit code 0 = no drift. Exit code 1 = drift detected; output lists every issue with the exact path to fix.

## Fix what it finds

For most drift, the fix is one command:

```bash
python .claude/skills/status-propagator/propagate.py --campaign <slug> --asset <NN> --status <state>
```

Dashboard To Do / asset list drift is currently manual — those rows are campaign-specific and operator-prioritised. See the status-propagator [SKILL.md](../status-propagator/SKILL.md) "What it does NOT handle" section.

## Companion tool

See [`status-propagator`](../status-propagator/SKILL.md) — the fix-side of the same workflow.
