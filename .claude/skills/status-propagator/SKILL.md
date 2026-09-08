---
name: status-propagator
description: Update an asset's status across all the layers that gallery + dashboard + operator-review surfaces read from — asset.yaml, numeric-prefix asset record, preview.md, then re-render HTMLs + rebuild gallery. Use whenever an operator approves an asset OR status moves between Production / For-Human-Review / Approved / Archived. Replaces the manual 9-touch-point discipline that drifts every time.
---

# status-propagator

**One command, all layers updated atomically. No more "I forgot to update asset.yaml" or "the dashboard still shows Queued" drift.**

## When to use

Every time an asset status changes:
- Operator approves an asset
- Producer drafts a new asset (status: in-production)
- Producer ships an asset (status: for-human-review)
- Operator archives or declines

Stop hand-editing asset.yaml + the asset record + preview.md + re-rendering separately. That's a 5-step discipline that drifts on every miss.

## What it does

Given `(campaign, asset_id, new_status)`:

1. **Updates asset.yaml** `status:` field (load-bearing — gallery's primary check)
2. **Updates the numeric-prefix asset record .md** `**Status**:` line (gallery's MD fallback + operator-readable)
3. **Updates preview.md** `**Status**:` line (operator review surface)
4. **Re-renders** both HTMLs via render-html skill
5. **Rebuilds** the gallery so tile badges + filters reflect new state

## Approval must disposition open questions (SYS-013)

When the new status is `approved`, the gate is closing — so the asset's pre-approval
**open questions must be dispositioned, not left dangling.** For each item under an
`## Open questions for operator (gate)` / `Operator decisions required at gate` section,
route it to exactly one of:

- **answered** → fold the answer into the asset's audit-history / notes (it stops being open);
- **deferred** → re-home as a Phase-5 `operator_action` in `asset.yaml` (survives approval as a deploy-time action, counted on the dashboard To Do, NOT the gallery questions badge);
- **closed / killed** → drop it with a one-line reason.

**Gallery behaviour (build-gallery, SYS-013):** gate questions count only while the asset is
pre-approval (`In Production` / `For Human Review`). Once `Approved` / `Archived` / `Declined`
the gate is closed and they stop counting — so an approved asset shows **no** question badge
unless a question was explicitly deferred-open (as a Phase-5 operator_action). The disposition
happens AT approval — operator policy 2026-06-25.

## Usage

```bash
python .claude/skills/status-propagator/propagate.py \
    --campaign gamma-launch-2026q2 \
    --asset 01 \
    --status approved \
    --note "v5.3 final polish approved 2026-06-10"
```

### Status values

| Flag | Display | Use when |
|---|---|---|
| `approved` | Approved | Operator gate ✅ |
| `for-human-review` | For Human Review | Producer return + Brand cleared |
| `in-production` | In Production | Producer fired, drafting |
| `archived` | Archived | Asset no longer in active scope |
| `declined` | Declined | Operator killed |

### Optional flags

- `--note "..."` — extra context appended to the Status line in MDs
- `--no-render` — skip HTML re-render + gallery rebuild (use during batch sweeps; finish with one full rebuild)

## Operator-action sub-commands

Each asset can declare `operator_actions` in its `asset.yaml` — these are the operator-execute items that survive creative approval (printer pick, ESP wire, deploy, ffmpeg trim, etc.). The dashboard To Do block is auto-generated from all pending actions across the campaign.

Mark one done:
```bash
python .claude/skills/status-propagator/propagate.py \
    --campaign gamma-launch-2026q2 --asset 5 --task pick-printer --done
```

Un-mark (if it wasn't really done):
```bash
python .claude/skills/status-propagator/propagate.py \
    --campaign gamma-launch-2026q2 --asset 5 --task pick-printer --pending
```

The dashboard md needs a `<!-- OPERATOR_ACTIONS_AUTO -->` marker where the To Do table belongs — render-html replaces it with a generated table on every dashboard render.

### YAML schema for operator_actions

```yaml
operator_actions:
  - id: pick-printer                       # stable slug for --task
    title: "Pick print partner"
    why: "Inkness Carlton recommended"     # optional
    time: "~10 min"                         # optional
    blocks_launch: true                     # optional; surfaces 🚀 in table
    priority: P1                            # optional; default P1
    phase: 4                                # optional; default 4
    where: "preview.md"                     # optional; relative path → renders as [open] link
    status: pending                         # pending | done
    completed: "2026-06-12"                 # auto-set when status → done
```

## What it does NOT handle (yet)

- **Dashboard `📋 Full asset list` table** — the Plan v2.1 numbering doesn't always match actual folder numbering. Manual until the asset-list block also gets auto-derived from `assets/*/asset.yaml`.
- **tasks.md cross-campaign queue** — manual.

For now, after running propagator, also manually update:
- `campaigns/<slug>/<slug>.md` asset list rows (Plan v2.1 numbering mismatch)
- `campaigns/tasks.md` if cross-campaign action changed
- **The asset record's `## What the operator does next` section** (caught 2026-06-11: Battle Cards showed ✅ Approved while the right-hand panel still listed re-read/verdict instructions). The render pipeline extracts this section into the action panel — on approval, rewrite it to post-approval actions (how to use, edit path, next scheduled review) and strip resolved `## Flags for Brand Manager` / `## Open questions for operator (gate)` blocks. Prose judgment, so the script can't do it — CM must, then re-render.

## Companion tool

See [`check-state`](../check-state/SKILL.md) — walks every asset folder and reports any drift between yaml + MDs + dashboard. Run before review sessions to catch what propagator hasn't been pointed at yet.
